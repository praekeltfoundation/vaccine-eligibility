import logging
from urllib.parse import urljoin

import aiohttp

from vaccine.utils import HTTP_EXCEPTIONS
from yal import config
from yal.utils import get_current_datetime

logger = logging.getLogger(__name__)


def get_rapidpro_api():
    return aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=5),
        headers={
            "Authorization": f"Token {config.RAPIDPRO_TOKEN_TEMP}",
            "Content-Type": "application/json",
            "User-Agent": "mqr-baseline-study-ussd",
        },
    )


async def get_profile(whatsapp_id):
    urn = f"whatsapp:{whatsapp_id}"
    fields = {}
    async with get_rapidpro_api() as session:
        for i in range(3):
            try:
                response = await session.get(
                    urljoin(config.RAPIDPRO_URL, "/api/v2/contacts.json"),
                    params={"urn": urn},
                )
                response.raise_for_status()
                response_body = await response.json()

                if len(response_body["results"]) > 0:
                    contact = response_body["results"][0]
                    fields = contact["fields"]

                break
            except HTTP_EXCEPTIONS as e:
                if i == 2:
                    logger.exception(e)
                    return True, fields
                else:
                    continue

    return False, fields


async def update_profile(whatsapp_id, fields, metadata):
    """
    Updates the user's profile on RapidPro.

    whatsapp_id: The user's whatsapp URN path
    fields: Keys are fields to update, values are values to update them to
    metadata: The user's metadata. Used to keep cached contact in sync with RapidPro
    """
    urn = f"whatsapp:{whatsapp_id}"
    async with get_rapidpro_api() as session:
        for i in range(3):
            try:
                params = {"fields": {}}

                for key, value in fields.items():
                    if value is not None:
                        params["fields"][key] = value

                response = await session.post(
                    urljoin(config.RAPIDPRO_URL, f"/api/v2/contacts.json?urn={urn}"),
                    json=params,
                )
                response.raise_for_status()
                for key, value in fields.items():
                    metadata[key] = value
                break
            except HTTP_EXCEPTIONS as e:
                if i == 2:
                    logger.exception(e)
                    return True
                else:
                    continue
    return False


async def start_flow(whatsapp_id, flow_uuid):
    urn = f"whatsapp:{whatsapp_id}"
    async with get_rapidpro_api() as session:
        for i in range(3):
            try:
                data = {
                    "flow": flow_uuid,
                    "urns": [urn],
                }
                response = await session.post(
                    urljoin(config.RAPIDPRO_URL, "/api/v2/flow_starts.json"),
                    json=data,
                )
                response.raise_for_status()
                break
            except HTTP_EXCEPTIONS as e:
                if i == 2:
                    logger.exception(e)
                    return True
                else:
                    continue
    return False

async def get_instance_fields():
    async with get_rapidpro_api() as session:
        for i in range(3):
            try:
                response = await session.get(
                    urljoin(config.RAPIDPRO_URL_TEMP, "/api/v2/fields.json"),
                )
                response.raise_for_status()
                response_body = await response.json()

                if len(response_body["results"]) > 0:
                    fields = response_body["results"]
                    #print(fields)
                break
            except HTTP_EXCEPTIONS as e:
                if i == 2:
                    logger.exception(e)
                    return True
                else:
                    continue
    return fields


def get_field_keys(instance_fields):
    fields = instance_fields
    keys = [field["key"] for field in fields]
    return keys    

def get_field_keys_and_types(instance_fields):
    fields = instance_fields['results']
    keys_and_types = {}
    for field in fields:
        keys_and_types.update({field["key"]: field["value_type"]})
    return keys_and_types  

def _get_fields_to_leave_unchanged():    
    fields_to_leave_unchanged = ["key1", "key2"]
    return fields_to_leave_unchanged

def _get_fields_to_update_and_retain():
    fields_to_update_and_retain = {
        "opted_out": "True",
        "opted_out_timestamp": get_current_datetime().isoformat(),
        "push_message_opt_in": "False",
        
    }
    return fields_to_update_and_retain 


def _prepare_fields_to_clear():
    optout_payload = {}
    fields_to_update_and_retain = _get_fields_to_update_and_retain()
    fields_to_leave_unchanged = _get_fields_to_leave_unchanged()
    return optout_payload


   