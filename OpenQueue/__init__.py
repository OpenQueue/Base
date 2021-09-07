# -*- coding: utf-8 -*-

import backblaze
import dathost
import aiohttp
import aiojobs
import bcrypt

from typing import Tuple, Union, AsyncGenerator
from databases import Database
from datetime import datetime
from sqlalchemy.sql import or_, func, select
from secrets import token_urlsafe

from .resources import Sessions, Config
from .webhook import WebhookSender

from .tables import (
    create_tables,
    user_table,
    league_table,
    integration_table
)

from .user import User
from .league import League
from .queue import Queue
from .login import Login

from .settings.database import DatabaseSettings
from .settings.upload import (
    B2Settings,
    DemoSettings,
    PfpSettings
)
from .settings.gametick import GameTickSettings
from .settings.steam import SteamSettings
from .settings.dathost import DathostSettings
from .settings.webhook import WebhookSettings
from .settings.playwin import PlaywinSettings
from .settings.smtp import SmtpSettings
from .settings.integration import IntegrationSettings

from .misc import str_uuid4, cache_events, leagues

from .exceptions import (
    UserTaken,
    InvalidUser
)

from .models.user import UserModel
from .models.league import LeagueModel
from .models.integration import IntegrationModel

from .email import send_email


__version__ = "0.0.37"
__url__ = "https://github.com/OpenQueue"
__description__ = "Base functionality for OpenQueue."
__author__ = "WardPearce"
__author_email__ = "wardpearce@protonmail.com"
__license__ = "AGPL-3.0 License"


class OpenQueue:
    def __init__(self, database_settings: DatabaseSettings,
                 b2_settings: B2Settings,
                 dathost_settings: DathostSettings,
                 steam_settings: SteamSettings,
                 webhook_settings: WebhookSettings,
                 smtp_settings: SmtpSettings,
                 pfp_settings: PfpSettings = PfpSettings(),
                 game_tick_settings: GameTickSettings = GameTickSettings(),
                 demo_settings: DemoSettings = DemoSettings(),
                 playwin_settings: PlaywinSettings = None,
                 integration_settings: IntegrationSettings = None
                 ) -> None:
        """Skrim Base functionality.

        Parameters
        ----------
        database_settings : DatabaseSettings
        b2_settings : B2Settings
        dathost_settings : DathostSettings
        steam_settings : SteamSettings
        webhook_settings : WebhookSettings
        pfp_settings : PfpSettings, optional
            by default PfpSettings()
        game_tick_settings : GameTickSettings, optional
            by default GameTickSettings()
        demo_settings : DemoSettings, optional
            by default DemoSettings()
        playwin_settings : PlaywinSettings, optional
            by default None
        integration_settings : IntegrationSettins, optional
            If not provided then it will use defaults
            already saved in the database.
            by default None
        """

        # Sessions should never be created here
        # Use OpenQueue.startup, its important
        # sessions are created within the correct
        # loop context.

        assert isinstance(database_settings, DatabaseSettings)
        assert isinstance(b2_settings, B2Settings)
        assert isinstance(demo_settings, DemoSettings)
        assert isinstance(pfp_settings, PfpSettings)
        assert isinstance(dathost_settings, DathostSettings)
        assert isinstance(steam_settings, SteamSettings)
        assert isinstance(webhook_settings, WebhookSettings)
        assert isinstance(game_tick_settings, GameTickSettings)
        assert isinstance(
            playwin_settings, PlaywinSettings
        ) if playwin_settings else True

        Config.b2 = b2_settings
        Config.demo = demo_settings
        Config.pfp = pfp_settings
        Config.webhooks = webhook_settings
        Config.steam = steam_settings
        Config.playwin = playwin_settings
        Config.clone_id = dathost_settings.clone_id
        Config.game_tick = game_tick_settings
        Config.database = database_settings
        Config.smtp = smtp_settings

        self.dathost_settings = dathost_settings
        self.integration_settings = integration_settings

        create_tables(
            "{}+{}{}".format(
                database_settings.engine,
                database_settings.alchemy_engine,
                database_settings.url
            )
        )

    async def startup(self) -> None:
        """Connects to sessions
        """

        self.b2 = backblaze.Awaiting(
            Config.b2.key_id,
            Config.b2.application_key
        )

        Sessions.requests = aiohttp.ClientSession()

        Sessions.game = dathost.Awaiting(
            email=self.dathost_settings.email,
            password=self.dathost_settings.password,
            timeout=self.dathost_settings.timeout
        )

        Sessions.bucket = self.b2.bucket(
            Config.b2.bucket_id
        )

        Sessions.database = Database(
            Config.database.engine + Config.database.url
        )

        Sessions.scheduler = await aiojobs.create_scheduler()

        await Sessions.database.connect()
        await self.b2.authorize()

        await cache_events()

        if self.integration_settings:
            current_integrations = await Sessions.database.fetch_all(
                select([
                    integration_table.c.name
                ]).select_from(integration_table)
            )
            if current_integrations:
                current_integrations = [
                    name[0] for name in current_integrations
                ]
            else:
                current_integrations = []

            for intergration in self.integration_settings.defaults:
                if intergration.name not in current_integrations:
                    await Sessions.database.execute(
                        integration_table.insert().values(
                            **intergration.api_schema(False)
                        )
                    )

    async def shutdown(self) -> None:
        """Closes sessions.
        """

        await Sessions.scheduler.close()
        await Sessions.database.disconnect()
        await Sessions.requests.close()
        await Sessions.game.close()
        await self.b2.close()

    async def create_user(self, name: str, email: str,
                          password: str) -> Tuple[UserModel, User]:
        """Used to create user.

        Parameters
        ----------
        name : str
        email : str
        password : str

        Returns
        -------
        UserModel
        User
        """

        user_id = str_uuid4()
        email_code = token_urlsafe(24)

        values = {
            "user_id": user_id,
            "name": name,
            "email": email,
            "email_confirmed": False,
            "email_code": email_code,
            "password": bcrypt.hashpw(password.encode(), bcrypt.gensalt()),
            "timestamp": datetime.now()
        }

        try:
            await Sessions.database.execute(
                user_table.insert().values(**values)
            )
        except Exception:
            raise UserTaken()
        else:
            user_model = UserModel(**values)

            await Sessions.scheduler.spawn(
                WebhookSender(user_model).user_created()
            )

            await Sessions.scheduler.spawn(
                send_email(
                    to=email,
                    subject="Skrim.gg | Please confirm your email!",
                    header="Welcome to Skrim.gg, {}!".format(name),
                    body="""Thanks for joining Skrim.gg!
                    Please click the button to confirm your email.

                    If you didn't sign up to Skrim.gg, please
                    ignore this email.""",
                    button="Confirm my email",
                    url=Config.smtp.confirmation + values["email_code"]
                )
            )

            return user_model, self.user(values["user_id"])

    async def external_id_to_user(self, external_id: Union[str, int]
                                  ) -> Tuple[UserModel, User]:
        """Converts external ID to Nexus League ID.

        Parameters
        ----------
        external_id : Union[str, int]

        Returns
        -------
        UserModel
        User

        Raises
        ------
        InvalidUser
        """

        row = await Sessions.database.fetch_one(
            select([
                user_table,
                func.group_concat(
                    league_table.c.league_id
                ).label("league_ids")
            ]).select_from(
                user_table.join(
                    league_table,
                    league_table.c.user_id == user_table.c.user_id,
                    isouter=True
                )
            ).where(
                or_(
                    user_table.c.discord_id == external_id,
                    user_table.c.steam_id == external_id,
                    user_table.c.dathost_id == external_id
                )
            ).group_by(
                user_table.c.user_id,
                league_table.c.user_id
            )
        )

        if row:
            return UserModel(**row), self.user(row["user_id"])
        else:
            raise InvalidUser()

    async def integrations(self) -> AsyncGenerator[IntegrationModel, None]:
        """Lists all optional integrations.

        Yields
        -------
        IntegrationModel
        """

        query = integration_table.select()
        async for row in Sessions.database.iterate(query):
            yield IntegrationModel(**row)

    def login(self, email: str, password: str) -> Login:
        """Used to interact with user login.

        Parameters
        ----------
        email : str
        password : str

        Returns
        -------
        Login
        """

        return Login(self, email, password)

    def create_queue(self, capacity: int = 10) -> Queue:
        """Used to create a queue.

        Notes
        -----
        Queue only stored in memory.

        Parameters
        ----------
        capacity : int, optional
            by default 10

        Returns
        -------
        Queue
        """

        return Queue(capacity)

    def user(self, user_id: str) -> User:
        """Used to interact with user.

        Parameters
        ----------
        user_id : str

        Returns
        -------
        User
        """

        return User(self, user_id)

    def league(self, league_id: str) -> League:
        """Used to interact with league.

        Parameters
        ----------
        league_id : str

        Returns
        -------
        League
        """

        return League(league_id)

    async def leagues(self, search: str = None,
                      desc: bool = True
                      ) -> AsyncGenerator[Tuple[LeagueModel, League], None]:
        """Used to list leagues.

        Parameters
        ----------
        user_id : str, optional
            by default None
        search : str, optional
            by default None
        desc : bool, optional
            by default True

        Yields
        -------
        LeagueModel
        League
        """

        async for model, league in leagues(search=search, desc=desc,
                                           league=League):
            yield model, league
