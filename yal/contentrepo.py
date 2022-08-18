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


async def get_choices_by_id(page_id):
    return await get_choices_by_path(f"/api/v2/pages?id={page_id}")


async def get_suggested_choices(topics_viewed):
    return await get_choices_by_path(
        f"/suggestedcontent/?topics_viewed={','.join(topics_viewed)}"
    )


async def get_page_detail_by_tag(user, tag):
    error, choices = await get_choices_by_path(f"/api/v2/pages?tag={tag}")

    if error:
        return error, choices

    return await get_page_details(user, choices[0].value, 1)


async def get_choices_by_path(path):
    choices = []
    async with get_contentrepo_api() as session:
        for i in range(3):
            try:
                logger.info(f">>>> get_choices_by_path {path}")
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


async def get_page_details(user, page_id, message_id, suggested=False):
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
                if suggested:
                    params["data__suggested"] = True

                logger.info(f">>>> get_page_details /api/v2/pages/{page_id}")
                logger.info(params)
                response = await session.get(
                    urljoin(config.CONTENTREPO_API_URL, f"/api/v2/pages/{page_id}"),
                    params=params,
                )
                response.raise_for_status()
                response_body = await response.json()

                page_details["page_id"] = page_id
                page_details["has_children"] = response_body["has_children"]
                page_details["title"] = response_body["title"]
                page_details["subtitle"] = response_body["subtitle"]
                page_details["body"] = response_body["body"]["text"]["value"]["message"]

                page_details["parent_id"] = response_body["meta"]["parent"]["id"]
                page_details["parent_title"] = response_body["meta"]["parent"]["title"]

                page_details["tags"] = response_body["tags"]

                if not page_details["has_children"]:
                    message_number = response_body["body"]["message"]
                    total_messages = response_body["body"]["total_messages"]

                    if total_messages > message_number:
                        page_details["next_prompt"] = (
                            response_body["body"]["text"]["value"].get("next_prompt")
                            or "Next"
                        )
                    else:

                        if "prompt_quiz" in page_details["tags"]:
                            quiz_tag = [
                                i for i in page_details["tags"] if i.startswith("quiz_")
                            ][0]
                            page_details["quiz_tag"] = quiz_tag

                    related_pages = await find_related_pages(response_body["tags"])
                    if related_pages:
                        page_details["related_pages"] = related_pages

                    if message_number == 1:
                        page_details["quick_replies"] = response_body["quick_replies"]

                if response_body["body"]["text"]["value"].get("image"):
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


async def find_related_pages(tags):
    related_pages = {}
    for tag in tags:
        if tag.startswith("related_"):
            page_id = tag.replace("related_", "")
            error, related_choices = await get_choices_by_id(page_id)
            if not error:
                for choice in related_choices:
                    related_pages[choice.value] = f"Learn more about {choice.label}"

    return related_pages
