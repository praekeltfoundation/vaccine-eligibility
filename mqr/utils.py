from temba_client.v2 import TembaClient

import vaccine.healthcheck_config as config


rapidpro = TembaClient(config.RAPIDPRO_URL, config.RAPIDPRO_TOKEN)
