import asynctest

from .. import SkrimBase

from ..settings.database import DatabaseSettings
from ..settings.upload import B2Settings
from ..settings.dathost import DathostSettings
from ..settings.steam import SteamSettings
from ..settings.webhook import WebhookSettings
from ..settings.smtp import SmtpSettings
from ..settings.integration import IntegrationSettings

from ..models.integration import IntegrationModel

from .shared_vars import (
    DATABASE,
    BACKBLAZE,
    DATHOST,
    STEAM,
    WEBHOOK,
    SMTP
)


class TestBase(asynctest.TestCase):
    skrim: SkrimBase

    use_default_loop = True

    async def setUp(self) -> None:
        self.skrim = SkrimBase(
            database_settings=DatabaseSettings(**DATABASE),
            b2_settings=B2Settings(**BACKBLAZE),
            dathost_settings=DathostSettings(**DATHOST),
            steam_settings=SteamSettings(**STEAM),
            webhook_settings=WebhookSettings(**WEBHOOK),
            smtp_settings=SmtpSettings(**SMTP),
            integration_settings=IntegrationSettings([
                IntegrationModel(
                    name="playwin",
                    auth_url=None,
                    logo="https://www.playwin.me/images/vector-smart-object_2.png",  # noqa: E501
                    globally_required=False
                ),
                IntegrationModel(
                    name="discord",
                    auth_url="/api/auth/site/discord/",
                    logo="https://discord.com/assets/2d20a45d79110dc5bf947137e9d99b66.svg",  # noqa: E501
                    globally_required=False
                ),
                IntegrationModel(
                    name="steam",
                    auth_url="/api/auth/site/steam/",
                    logo="https://cdn.freebiesupply.com/images/large/2x/steam-logo-black-transparent.png",  # noqa: E501
                    globally_required=True
                ),
                IntegrationModel(
                    name="dathost",
                    auth_url="/api/auth/site/dathost/",
                    logo="https://dathost.net/assets/img/logo.min.svg",  # noqa: E501
                    globally_required=False
                )
            ])
        )

        # Starts up all sessions
        await self.skrim.startup()

    async def tearDown(self) -> None:
        # Close any open sessions.
        await self.skrim.shutdown()
