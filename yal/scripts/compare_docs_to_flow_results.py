import argparse
import asyncio
from urllib.parse import urljoin

import aiohttp
import pytablereader


def get_arguments():
    parser = argparse.ArgumentParser(
        description="Compares the documentation to the flow results specification on "
        "the server, and notifies on any questions missing on the server"
    )
    parser.add_argument("url", help="The base URL for the flow results server")
    parser.add_argument(
        "token", help="An authorization token to access the flow results server"
    )
    return parser.parse_args()


def get_documented_states():
    loader = pytablereader.MarkdownTableFileLoader("yal/tests/states_dictionary.md")
    documented_states = set()
    for data in loader.load():
        documented_states = documented_states | {
            row["state_name"]
            for row in data.as_dict()[data.table_name]
            if row["accepts_user_input"]
        }
    return documented_states


async def get_server_states(args: argparse.Namespace):
    packages_url = urljoin(args.url, "api/v1/flow-results/packages/")
    headers = {
        "Authorization": f"Token {args.token}",
        "Accept": "application/json",
        "User-Agent": "compare-docs-script",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(packages_url, headers=headers) as resp:
            flow_id = (await resp.json())["data"][0]["id"]
        package_url = urljoin(packages_url, f"{flow_id}/")
        async with session.get(package_url, headers=headers) as resp:
            return set(
                (await resp.json())["data"]["attributes"]["resources"][0]["schema"][
                    "questions"
                ].keys()
            )


def main():
    args = get_arguments()
    documented_states = get_documented_states()
    server_states = asyncio.run(get_server_states(args))
    difference = documented_states - server_states
    assert len(difference) == 0, (
        f"{len(difference)} states are not in the definition. List: {difference}"
    )
    print("Done! No missing questions found")


if __name__ == "__main__":
    main()
