import asyncio
import aiohttp
import argparse
import hmac
import json
from base64 import b64encode
from datetime import datetime
from hashlib import sha256
from urllib.parse import urljoin
from uuid import uuid4


def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pretends to be a webhook from whatsapp for a template message "
        "button click with payload"
    )
    parser.add_argument("url", help="Base URL for the transport")
    parser.add_argument("hmac_secret", help="HMAC secret to sign the request with")
    parser.add_argument(
        "whatsapp_id", help="The whatsapp ID for the user we want to trigger this for"
    )
    parser.add_argument(
        "payload", help="The payload that the template button was sent with"
    )
    return parser.parse_args()


def create_whatsapp_message(arguments: argparse.Namespace) -> dict:
    return {
        "messages": [
            {
                "from": arguments.whatsapp_id,
                "id": uuid4().hex,
                "timestamp": datetime.now().isoformat(),
                "type": "button",
                "button": {
                    "payload": arguments.payload,
                    "text": arguments.payload,
                },
            }
        ]
    }


def create_hmac_signature(body: str, secret: str) -> str:
    h = hmac.new(secret.encode(), body.encode(), sha256)
    return b64encode(h.digest()).decode()


async def make_request(arguments: argparse.Namespace):
    body = json.dumps(create_whatsapp_message(arguments))
    signature = create_hmac_signature(body, arguments.hmac_secret)
    headers = {
        "X-Turn-Hook-Signature": signature,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "qa-trigger-template-payload-script",
    }
    url = urljoin(arguments.url, "v1/webhook")
    async with aiohttp.ClientSession() as session:
        async with session.post(url=url, headers=headers, data=body) as resp:
            resp.raise_for_status()


def main():
    arguments = get_arguments()
    asyncio.run(make_request(arguments))


if __name__ == "__main__":
    main()
