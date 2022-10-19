import asyncio
import logging
import secrets
from collections import defaultdict
from urllib.parse import quote_plus, urljoin

import aiohttp
import geopy.distance

from vaccine.base_application import BaseApplication
from vaccine.states import (
    Choice,
    CustomChoiceState,
    EndState,
    ErrorMessage,
    FreeText,
    MenuState,
    WhatsAppButtonState,
)
from vaccine.utils import HTTP_EXCEPTIONS
from yal import config, rapidpro
from yal.pleasecallme import Application as PleaseCallMeApplication
from yal.utils import BACK_TO_MAIN, GET_HELP, get_generic_error, normalise_phonenumber

logger = logging.getLogger(__name__)


def get_servicefinder_api():
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Authorization": f"Basic {config.SERVICEFINDER_TOKEN}",
            "Content-Type": "application/json",
        },
    )


def get_google_api():
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={"Content-Type": "application/json", "User-Agent": "healthcheck-ussd"},
    )


class Application(BaseApplication):
    START_STATE = "state_servicefinder_start"

    def reset_metadata(self):
        self.save_metadata("parent_category", "root")
        self.save_metadata("servicefinder_breadcrumb", "*Get help near you*")

    def append_breadcrumb(self, category):
        breadcrumb = self.user.metadata["servicefinder_breadcrumb"]
        breadcrumb = breadcrumb.replace("*", "") + f" / *{category}*"
        self.save_metadata("servicefinder_breadcrumb", breadcrumb)

    async def state_servicefinder_start(self):
        self.reset_metadata()
        self.save_metadata("google_session_token", secrets.token_bytes(20).hex())
        question = self._(
            "\n".join(
                [
                    "🏥 Find Clinics and Services",
                    "Get help near you",
                    "-----",
                    "",
                    "Would you like me to help you find clinics and services closest "
                    "to you?",
                    "",
                    "1 - Yes, sounds good",
                    "",
                    "-----",
                    "Or reply:",
                    BACK_TO_MAIN,
                    GET_HELP,
                ]
            )
        )

        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("yes", "Yes, sounds good"),
            ],
            error=self._(get_generic_error()),
            next={
                "yes": "state_check_address",
            },
        )

    async def state_check_address(self):
        metadata = self.user.metadata

        for field in ("location_description", "latitude", "longitude"):
            if field not in metadata:
                return await self.go_to_state("state_location")

        return await self.go_to_state("state_pre_confirm_existing_address")

    async def state_pre_confirm_existing_address(self):
        metadata = self.user.metadata
        await self.publish_message(
            self._("[persona_emoji] *Okay, I just need to confirm some details...*")
        )
        await asyncio.sleep(0.5)

        msg = self._(
            "\n".join(
                [
                    "🏥 Find Clinics and Services",
                    "*Get help near you*",
                    "-----",
                    "[persona_emoji] *The address I have for you right now is:*",
                    "",
                    metadata["location_description"],
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                    GET_HELP,
                ]
            )
        )
        await self.publish_message(msg)
        await asyncio.sleep(0.5)

        return await self.go_to_state("state_confirm_existing_address")

    async def state_confirm_existing_address(self):
        question = self._(
            "\n".join(
                [
                    "🏥 Find Clinics and Services",
                    "*Get help near you*",
                    "-----",
                    "",
                    "[persona_emoji] *Would you like me to recommend helpful services "
                    "close to this address?*",
                    "",
                    "1 - Yes please",
                    "2 - Use a different location",
                    "",
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                    GET_HELP,
                ]
            )
        )

        return WhatsAppButtonState(
            self,
            question=question,
            choices=[
                Choice("yes", "Use this location"),
                Choice("new", "Use another location"),
            ],
            error=self._(get_generic_error()),
            next={
                "yes": "state_category_lookup",
                "new": "state_pre_different_location",
            },
        )

    async def state_address_coords_lookup(self):
        async with get_google_api() as session:
            for i in range(3):
                try:
                    response = await session.get(
                        urljoin(
                            config.GOOGLE_PLACES_URL, "/maps/api/place/details/json"
                        ),
                        params={
                            "key": config.GOOGLE_PLACES_KEY,
                            "place_id": self.user.metadata.get("place_id"),
                            "sessiontoken": self.user.metadata.get(
                                "google_session_token"
                            ),
                            "language": "en",
                            "fields": "geometry",
                        },
                    )
                    response.raise_for_status()
                    data = await response.json()

                    location = data["result"]["geometry"]["location"]

                    self.save_metadata("latitude", location["lat"])
                    self.save_metadata("longitude", location["lng"])

                    return await self.go_to_state("state_category_lookup")
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue

    async def state_category_lookup(self):
        async with get_servicefinder_api() as session:
            for i in range(3):
                try:
                    response = await session.get(
                        url=urljoin(config.SERVICEFINDER_URL, "/api/categories"),
                    )
                    response.raise_for_status()
                    response_body = await response.json()

                    categories = defaultdict(dict)
                    for c in response_body:
                        parent = c["parent"] or "root"
                        categories[parent][c["_id"]] = c["name"]

                    self.save_metadata("categories", dict(categories))
                    break
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue

        return await self.go_to_state("state_pre_category_msg")

    async def state_pre_category_msg(self):
        msg = "\n".join(
            [
                "🏥 Find Clinics and Services",
                "*Get help near you*",
                "-----",
                "",
                "[persona_emoji] Perfect! That helps me narrow it down.",
                "",
                "*Next, please tell me what you need help with*",
            ]
        )
        await self.publish_message(self._(msg))
        await asyncio.sleep(0.5)

        return await self.go_to_state("state_category")

    async def state_save_parent_category(self):
        metadata = self.user.metadata

        parent_category = self.user.answers["state_category"]

        category = metadata["categories"][metadata["parent_category"]][parent_category]

        self.save_metadata("parent_category", parent_category)

        self.append_breadcrumb(category)

        return await self.go_to_state("state_category")

    async def state_category(self):
        async def next_(choice: Choice):
            if choice.value == "talk":
                self.reset_metadata()
                return PleaseCallMeApplication.START_STATE

            if choice.value in self.user.metadata["categories"]:
                return "state_save_parent_category"

            return "state_service_lookup"

        metadata = self.user.metadata
        categories = metadata["categories"][metadata.get("parent_category", "root")]

        category_text = "\n".join(
            [f"{i+1} - {v}" for i, v in enumerate(categories.values())]
        )
        category_choices = [Choice(k, v) for k, v in categories.items()]
        category_choices.append(Choice("talk", "Talk to someone"))

        question = self._(
            "\n".join(
                [
                    "🏥 Find Clinics and Services",
                    metadata["servicefinder_breadcrumb"],
                    "-----",
                    "",
                    "[persona_emoji] *Choose an option from the list:*",
                    "",
                    category_text,
                    "",
                    "*OR*",
                    "",
                    f"{len(category_choices)} - Talk to somebody",
                    "",
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                    GET_HELP,
                ]
            )
        )
        return CustomChoiceState(
            self,
            question=question,
            choices=category_choices,
            next=next_,
            error=self._(get_generic_error()),
        )

    async def state_service_lookup(self):
        async with get_servicefinder_api() as session:
            for i in range(3):
                try:
                    response = await session.get(
                        url=urljoin(config.SERVICEFINDER_URL, "/api/locations"),
                        params={
                            "category": self.user.answers["state_category"],
                            "latitude": self.user.metadata["latitude"],
                            "longitude": self.user.metadata["longitude"],
                            "radius": 50,
                        },
                    )
                    response.raise_for_status()
                    response_body = await response.json()

                    facility_count = len(response_body)

                    self.save_metadata("facilities", response_body)
                    break
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue

        if facility_count > 0:
            return await self.go_to_state("state_display_facilities")
        else:
            return await self.go_to_state("state_no_facilities_found")

    async def state_no_facilities_found(self):
        self.reset_metadata()
        question = "\n".join(
            [
                "[persona_emoji] *Sorry, we can't find any services near you.*",
                "",
                "But don't worry, here are some other options you can try:",
                "",
            ]
        )
        return MenuState(
            self,
            question=self._(question),
            error=self._(get_generic_error()),
            choices=[
                Choice("state_location", self._("Try another location")),
                Choice("state_category", self._("Try another service")),
            ],
        )

    async def state_display_facilities(self):
        metadata = self.user.metadata
        msg = "\n".join(
            [
                "🏥 Find Clinics and Services",
                "*Get help near you*",
                "-----",
                "",
                "[persona_emoji]*Okay, I've got you. Here are your closest options...*",
            ]
        )
        await self.publish_message(self._(msg))
        await asyncio.sleep(0.5)

        user_location = (metadata["latitude"], metadata["longitude"])

        def format_facility(i, facility):
            numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
            lng, lat = facility["location"]["coordinates"]
            distance = geopy.distance.geodesic(user_location, (lat, lng)).km
            details = [
                f"{numbers[i]} *{facility['name']}*",
                f"📍 {facility['fullAddress']}",
                f"📞 {facility['telephoneNumber']}",
                f"🦶 {round(distance)} km",
                "----",
                "",
            ]
            return "\n".join(details)

        services = "\n".join(
            [format_facility(i, f) for i, f in enumerate(metadata["facilities"][:5])]
        )

        category = metadata["categories"][metadata.get("parent_category", "root")][
            self.user.answers["state_category"]
        ]

        msg = "\n".join(
            [
                "🏥 Find Clinics and Services",
                f"{category} near you",
                "-----",
                "",
                services,
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )

        return EndState(
            self,
            self._(msg),
            next=self.START_STATE,
        )

    async def state_pre_different_location(self):
        await self.publish_message(
            self._("[persona_emoji] *Sure. Where would you like me to look?*")
        )
        await asyncio.sleep(0.5)

        question = "\n".join(
            [
                "🏥 Find Clinics and Services",
                "*Get help near you*",
                "-----",
                "",
                "[persona_emoji]*You can change your location by sending me a pin (📍)."
                " To do this:*",
                "",
                "1️⃣Tap the *+ _(plus)_* button or the 📎*_(paperclip)_* button "
                "below.",
                "",
                "2️⃣Next, tap *Location* then select *Send Your Current Location.*",
                "",
                "_You can also use the *search 🔎 at the top of the screen, to type "
                "in the address or area* you want to share._",
                "",
                "-----",
                "*Or reply:*",
                BACK_TO_MAIN,
                GET_HELP,
            ]
        )
        return await self.go_to_state("state_location", question=question)

    async def state_location(self, question=None):
        async def store_location_coords(content):
            if not self.inbound:
                return
            loc = self.inbound.transport_metadata.get("message", {}).get("location", {})
            latitude = loc.get("latitude")
            longitude = loc.get("longitude")
            if isinstance(latitude, float) and isinstance(longitude, float):
                self.save_metadata("latitude", latitude)
                self.save_metadata("longitude", longitude)
            else:
                raise ErrorMessage(
                    "\n".join(
                        [
                            "[persona_emoji]*Hmmm, for some reason I couldn't find "
                            "that location. Let's try again.*",
                            "",
                            "*OR*",
                            "",
                            "*Send HELP to talk to to a human.*",
                        ]
                    )
                )

        if not question:
            question = "\n".join(
                [
                    "NEED HELP / Find clinics and services /📍*Location*",
                    "-----",
                    "",
                    "To be able to suggest youth-friendly clinics and FREE services "
                    "near you, I need to know where you live.",
                    "",
                    "[persona_emoji]*(You can share your location by sending me a pin "
                    "(📍). To do this:*",
                    "",
                    "1️⃣*Tap the + _(plus)_* button or the 📎*_(paperclip)_* button "
                    "below.",
                    "",
                    "2️⃣Next, tap *Location* then select *Send Your Current Location.*",
                    "",
                    "_You can also use the *search 🔎 at the top of the screen, to type "
                    "in the address or area* you want to share._",
                    "",
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                    GET_HELP,
                ]
            )

        return FreeText(
            self,
            question=question,
            next="state_get_description_from_coords",
            check=store_location_coords,
        )

    async def state_get_description_from_coords(self):
        metadata = self.user.metadata
        latitude = metadata.get("latitude")
        longitude = metadata.get("longitude")

        async with get_google_api() as session:
            for i in range(3):
                try:
                    response = await session.get(
                        urljoin(
                            config.GOOGLE_PLACES_URL,
                            "/maps/api/geocode/json",
                        ),
                        params={
                            "latlong": quote_plus(f"{latitude},{longitude}"),
                            "key": config.GOOGLE_PLACES_KEY,
                            "sessiontoken": metadata.get("google_session_token"),
                            "language": "en",
                            "components": "country:za",
                        },
                    )
                    response.raise_for_status()
                    data = await response.json()

                    if data["status"] != "OK":
                        return await self.go_to_state("state_error")

                    first_result = data["results"][0]
                    self.save_metadata("place_id", first_result["place_id"])
                    self.save_metadata(
                        "location_description", first_result["formatted_address"]
                    )

                    return await self.go_to_state("state_save_location")
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue

    async def state_save_location(self):
        metadata = self.user.metadata
        latitude = metadata.get("latitude")
        longitude = metadata.get("longitude")
        location_description = metadata.get("location_description")

        msisdn = normalise_phonenumber(self.inbound.from_addr)
        whatsapp_id = msisdn.lstrip(" + ")
        data = {
            "location_description": location_description,
            "latitude": latitude,
            "longitude": longitude,
        }

        await rapidpro.update_profile(whatsapp_id, data)

        return await self.go_to_state("state_category_lookup")
