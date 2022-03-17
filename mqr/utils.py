from temba_client.v2 import TembaClient

import vaccine.healthcheck_config as config

rapidpro = None
if config.EXTERNAL_REGISTRATIONS_V2:
    rapidpro = TembaClient(config.RAPIDPRO_URL, config.RAPIDPRO_TOKEN)
