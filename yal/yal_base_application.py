from urllib.parse import ParseResult, urlunparse

from vaccine.base_application import BaseApplication
from yal import config


class BaseApplication(BaseApplication):
    @staticmethod
    def turn_profile_url(whatsapp_id):
        return urlunparse(
            ParseResult(
                scheme="https",
                netloc=config.API_HOST or "",
                path=f"/v1/contacts/{whatsapp_id}/profile",
                params="",
                query="",
                fragment="",
            )
        )
