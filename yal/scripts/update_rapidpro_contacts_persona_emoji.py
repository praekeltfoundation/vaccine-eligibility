import argparse
import json

import emoji
import requests

from yal.utils import extract_first_emoji


def get_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pretends to be a webhook from whatsapp for a template message "
        "button click with payload"
    )
    parser.add_argument("url", help="Base URL for the transport")
    parser.add_argument("api_token", help="Rapidpro API token")

    return parser.parse_args()


def update_contacts(arguments: argparse.Namespace):
    rapidpro_base_api_url = arguments.url
    api_token = arguments.api_token

    response = requests.get(
        f"{rapidpro_base_api_url}/api/v2/contacts.json",
        headers={"Authorization": f"Token {api_token}"},
    )
    response = response.json()

    for contact in response["results"]:
        if (
            not emoji.is_emoji(contact["fields"]["persona_emoji"])
            and contact["fields"]["persona_emoji"] != "Skip"
            and contact["fields"]["persona_emoji"] is not None
        ):
            new_persona_emoji = extract_first_emoji(contact["fields"]["persona_emoji"])

            payload = json.dumps({"fields": {"persona_emoji": new_persona_emoji}})
            headers = {
                "Authorization": f"Token {api_token}",
                "Content-Type": "application/json",
            }

            post_response = requests.post(
                f"{rapidpro_base_api_url}/api/v2/contacts.json?uuid={contact['uuid']}",
                headers=headers,
                data=payload,
            )
            if post_response.status_code == 200:
                print(f"success {contact['uuid']}")
            else:
                print(f"failed {contact['uuid']}")
                print(post_response.content)


def main():
    arguments = get_arguments()
    update_contacts(arguments)


if __name__ == "__main__":
    main()
