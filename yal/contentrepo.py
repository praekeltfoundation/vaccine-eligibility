import logging
from urllib.parse import urljoin

import aiohttp

from vaccine.states import Choice
from vaccine.utils import HTTP_EXCEPTIONS
from yal import config

logger = logging.getLogger(__name__)


def get_contentrepo_api():
    # TODO: Cache the session globally. Things that don't work:
    # - Declaring the session at the top of the file
    #   You get a `Timeout context manager should be used inside a task` error
    # - Declaring it here but caching it in a global variable for reuse
    #   You get a `Event loop is closed` error
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "yal-whatsapp-bot",
        },
    )


def get_url(path):
    return urljoin(config.CONTENTREPO_API_URL, path)


def get_image_url(image):
    return urljoin(config.CONTENTREPO_API_URL, f"media/original_images/{image}")


def get_privacy_policy_url():
    return urljoin(
        config.CONTENTREPO_API_URL, f"/documents/{config.PRIVACY_POLICY_PDF}"
    )


async def get_choices_by_tag(tag):
    return await get_choices_by_path(f"/api/v2/pages?tag={tag}")


async def get_choices_by_parent(parent_id):
    return await get_choices_by_path(f"/api/v2/pages?child_of={parent_id}")


async def get_choices_by_path(path):
    choices = []
    async with get_contentrepo_api() as session:
        for i in range(3):
            try:
                response = await session.get(urljoin(config.CONTENTREPO_API_URL, path))
                response.raise_for_status()
                response_body = await response.json()

                for page in response_body["results"]:
                    choices.append(Choice(str(page["id"]), page["title"]))

                break
            except HTTP_EXCEPTIONS as e:
                if i == 2:
                    logger.exception(e)
                    return True, []
                else:
                    continue
    return False, choices


async def get_page_details(user, page_id, message_id):
    page_details = {}
    async with get_contentrepo_api() as session:
        for i in range(3):
            try:
                params = {
                    "whatsapp": "true",
                    "message": message_id,
                    "data__session_id": user.session_id,
                    "data__user_addr": user.addr,
                }
                response = await session.get(
                    urljoin(config.CONTENTREPO_API_URL, f"/api/v2/pages/{page_id}"),
                    params=params,
                )
                response.raise_for_status()
                response_body = await response.json()

                page_details["has_children"] = response_body["has_children"]
                page_details["title"] = response_body["title"]
                page_details["subtitle"] = response_body["subtitle"]
                page_details["body"] = response_body["body"]["text"]["value"]["message"]

                if not page_details["has_children"]:
                    message_number = response_body["body"]["message"]
                    total_messages = response_body["body"]["total_messages"]

                    if total_messages > message_number:
                        page_details["next_prompt"] = (
                            response_body["body"]["text"]["value"].get("next_prompt")
                            or "Next"
                        )

                if response_body["body"]["text"]["value"]["image"]:
                    image_id = response_body["body"]["text"]["value"]["image"]
                    response = await session.get(
                        urljoin(
                            config.CONTENTREPO_API_URL, f"/api/v2/images/{image_id}"
                        )
                    )
                    response.raise_for_status()
                    response_body = await response.json()
                    page_details["image_path"] = response_body["meta"]["download_url"]

                break
            except HTTP_EXCEPTIONS as e:
                if i == 2:
                    logger.exception(e)
                    return True, []
                else:
                    continue
    return False, page_details
