import asyncio
import logging
import secrets
from urllib.parse import urljoin

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
from yal import config
from yal.pleasecallme import Application as PleaseCallMeApplication
from yal.utils import BACK_TO_MAIN, GENERIC_ERROR, GET_HELP

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

    async def state_servicefinder_start(self):
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
            error=self._(GENERIC_ERROR),
            next={
                "yes": "state_check_address",
            },
        )

    async def state_check_address(self):
        metadata = self.user.metadata

        for field in ("province", "suburb", "street_name", "street_number"):
            if field not in metadata:
                return await self.go_to_state("state_pre_no_location")

        metadata = self.user.metadata
        address = (
            f"{metadata['street_number']} {metadata['street_name']} "
            f"{metadata['suburb']}",
        )
        async with get_google_api() as session:
            for i in range(3):
                try:
                    response = await session.get(
                        urljoin(
                            config.GOOGLE_PLACES_URL,
                            "/maps/api/place/autocomplete/json",
                        ),
                        params={
                            "input": address,
                            "key": config.GOOGLE_PLACES_KEY,
                            "sessiontoken": metadata.get("google_session_token"),
                            "language": "en",
                            "components": "country:za",
                        },
                    )
                    response.raise_for_status()
                    data = await response.json()

                    if data["status"] != "OK":
                        return await self.go_to_state("state_pre_no_location")

                    first_result = data["predictions"][0]
                    self.save_metadata("place_id", first_result["place_id"])

                    return await self.go_to_state("state_pre_confirm_existing_address")
                except HTTP_EXCEPTIONS as e:
                    if i == 2:
                        logger.exception(e)
                        return await self.go_to_state("state_error")
                    else:
                        continue

    async def state_pre_confirm_existing_address(self):
        metadata = self.user.metadata
        await self.worker.publish_message(
            self.inbound.reply(
                self._("👩🏾 *Okay, I just need to confirm some details...*")
            )
        )
        await asyncio.sleep(0.5)

        msg = self._(
            "\n".join(
                [
                    "🏥 Find Clinics and Services",
                    "*Get help near you*",
                    "-----",
                    "🙍🏾‍♀️ *The address I have for you right now is:*",
                    "",
                    f"{metadata['street_number']} {metadata['street_name']},",
                    metadata["suburb"],
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                    GET_HELP,
                ]
            )
        )
        await self.worker.publish_message(self.inbound.reply(msg))
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
                    "🙍🏾‍♀️ *Would you like me to recommend helpful services close to "
                    "this address?*",
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
            error=self._(GENERIC_ERROR),
            next={
                "yes": "state_address_coords_lookup",
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

                    categories = {c["_id"]: c["name"] for c in response_body}
                    self.save_metadata("categories", categories)
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
                "👩🏾 Perfect! That helps me narrow it down.",
                "",
                "*Next, please tell me what you need help with*",
            ]
        )
        await self.worker.publish_message(self.inbound.reply(self._(msg)))
        await asyncio.sleep(0.5)

        return await self.go_to_state("state_category")

    async def state_category(self):
        async def next_(choice: Choice):
            if choice.value == "talk":
                return PleaseCallMeApplication.START_STATE
            return "state_service_lookup"

        metadata = self.user.metadata
        category_text = "\n".join(
            [f"{i+1} - {v}" for i, v in enumerate(metadata["categories"].values())]
        )
        category_choices = [Choice(k, v) for k, v in metadata["categories"].items()]
        category_choices.append(Choice("talk", "Talk to someone"))

        question = self._(
            "\n".join(
                [
                    "🏥 Find Clinics and Services",
                    "*Get help near you*",
                    "-----",
                    "",
                    "🙍🏾‍♀️ *Choose an option from the list:*",
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
            error=self._(GENERIC_ERROR),
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
        question = "\n".join(
            [
                "🙍🏾‍♀️ *Sorry, we can't find any services near you.*",
                "",
                "But don't worry, here are some other options you can try:",
                "",
            ]
        )
        return MenuState(
            self,
            question=self._(question),
            error=self._(GENERIC_ERROR),
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
                "👩🏾*Okay, I've got you. Here are your closest options...*",
            ]
        )
        await self.worker.publish_message(self.inbound.reply(self._(msg)))
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

        category = metadata["categories"][self.user.answers["state_category"]]

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

    async def state_pre_no_location(self):
        await self.worker.publish_message(
            self.inbound.reply(
                self._("👩🏾 *Okay, I just need to confirm some details...*")
            )
        )
        await asyncio.sleep(0.5)

        return await self.go_to_state("state_location")

    async def state_pre_different_location(self):
        await self.worker.publish_message(
            self.inbound.reply(self._("🙍🏾‍♀️ *Sure. Where would you like me to look?*"))
        )
        await asyncio.sleep(0.5)

        return await self.go_to_state("state_location")

    async def state_location(self):
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
                            "🙍🏾‍♀️*Hmmm, for some reason I couldn't find that "
                            "location. Let's try again.*",
                            "",
                            "*OR*",
                            "",
                            "*Send HELP to talk to to a human.*",
                        ]
                    )
                )

        return FreeText(
            self,
            question="\n".join(
                [
                    "🏥 Find Clinics and Services",
                    "*Get help near you*",
                    "-----",
                    "",
                    "🙍🏾‍♀️*You can share a location by sending me a pin (📍). To do "
                    "this:*",
                    "",
                    "1️⃣ Tap the *+* button on the bottom left of this screen.",
                    "2️⃣ Tap *Location*",
                    "3️⃣ Select *Send Your Current Location* (or *use the search "
                    "bar* at the top of the screen to look up the address or area "
                    "you want to share).",
                    "",
                    "-----",
                    "*Or reply:*",
                    BACK_TO_MAIN,
                    GET_HELP,
                ]
            ),
            next="state_category_lookup",
            check=store_location_coords,
        )
