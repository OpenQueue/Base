# -*- coding: utf-8 -*-

import validators
import dathost
import bcrypt

from os import path
from typing import AsyncGenerator, TYPE_CHECKING, Tuple, Union
from datetime import datetime
from sqlalchemy.sql import func, select
from mimetypes import guess_extension
from backblaze.settings import UploadSettings
from secrets import token_urlsafe

from .resources import Config, Sessions

from .tables import (
    league_table,
    user_table,
    ban_table
)

from .league import League
from .ban import Ban

from .exceptions import (
    LeagueTaken,
    InvalidUser,
    InvalidPfpUrl,
    InvalidDathostDetails,
    ExternalInUse
)

from .models.league import LeagueModel
from .models.user import UserModel
from .models.ban import BanModel

from .misc import str_uuid4, leagues
from .email import send_email

from .webhook import WebhookSender

from .settings.ban import BanSettings
from .settings.dathost import DathostSettings

from .decorators import validate_region, validate_tickrate

if TYPE_CHECKING:
    from . import SkrimBase


class User:
    def __init__(self, upper: "SkrimBase",  user_id: str) -> None:
        """Used to interact with user.

        Parameters
        ----------
        upper: SkrimBase
        user_id : str
        """

        self.upper = upper
        self.user_id = user_id

    def ban(self, ban_id: str) -> Ban:
        """Used to interact with ban.

        Parameters
        ----------
        ban_id : str

        Returns
        -------
        Ban
        """

        return Ban(ban_id, self.user_id)

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

        async for model, league in leagues(user_id=self.user_id, league=League,
                                           search=search, desc=desc):
            yield model, league

    async def validate_email_code(self, code: str) -> bool:
        """Used to validate a email code.

        Parameters
        ----------
        code : str
            email code to compare

        Returns
        -------
        bool
        """

        valid_code = await Sessions.database.fetch_val(
            select([user_table.c.email_code]).select_from(
                user_table
            ).where(
                user_table.c.user_id == self.user_id
            )
        )

        hashed_code = bcrypt.hashpw(
            code.encode(),
            bcrypt.gensalt()
        )

        return bcrypt.checkpw(valid_code.encode(), hashed_code)

    async def update(self, name: str = None, pfp_extension: str = None,
                     email: str = None, password: str = None,
                     dathost_settings: DathostSettings = None,
                     discord_id: int = None,
                     steam_id: str = None,
                     email_confirmed: bool = None
                     ) -> Union[UserModel, None]:
        """Used to update values of user.

        Parameters
        ----------
        name : str, optional
            by default None
        pfp_extension : str, optional
            by default None
        email : str, optional
            by default None
        password : str, optional
            by default None
        dathost_settings: DathostSettings, optional
            by default None
        discord_id : int, optional
            by default None
        steam_id : str, optional
            by default None
        email_confirmed : bool, optional
            by default None

        Raises
        ------
        InvalidDathostDetails
        ExternalInUse

        Returns
        -------
        Union[UserModel, None]
        """

        values = {}
        if name:
            values["name"] = name
        if pfp_extension:
            values["pfp_extension"] = pfp_extension
        if email:
            values["email"] = email
            values["email_confirmed"] = False
            values["email_code"] = token_urlsafe(24)

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
        if password:
            values["password"] = bcrypt.hashpw(
                password.encode(), bcrypt.gensalt()
            )
        if dathost_settings:
            try:
                dathost_account = await dathost.Awaiting(
                    email=dathost_settings.email,
                    password=dathost_settings.password,
                ).account()
            except Exception:
                raise InvalidDathostDetails()
            else:
                try:
                    await self.upper.external_id_to_user(
                        dathost_account.account_id
                    )
                except InvalidUser:
                    pass
                else:
                    raise ExternalInUse()

                values["dathost_id"] = dathost_account.account_id
        if steam_id:
            try:
                await self.upper.external_id_to_user(steam_id)
            except InvalidUser:
                pass
            else:
                raise ExternalInUse()

            values["steam_id"] = steam_id
        if discord_id:
            try:
                await self.upper.external_id_to_user(discord_id)
            except InvalidUser:
                pass
            else:
                raise ExternalInUse()

            values["discord_id"] = discord_id
        if email_confirmed is not None:
            values["email_confirmed"] = email_confirmed

        if values:
            await Sessions.database.execute(
                user_table.update().values(**values).where(
                    user_table.c.user_id == self.user_id
                )
            )

            user_model = await self.get()

            await Sessions.scheduler.spawn(
                WebhookSender(user_model).user_updated()
            )

            return user_model

    async def add_pfp(self, url: str) -> Union[UserModel, None]:
        """Used to add pfp to profile from URL.

        Parameters
        ----------
        url : str

        Raises
        ------
        InvalidPfpUrl

        Returns
        -------
        Union[UserModel, None]
        """

        if not validators.url(url):
            raise InvalidPfpUrl()

        async with Sessions.requests.get(url) as resp:
            if resp.status == 200 and "Content-Type" in resp.headers:
                extension = guess_extension(resp.headers["Content-Type"])
                if not extension:
                    return

                await Sessions.bucket.upload(UploadSettings(
                    path.join(
                        Config.pfp.pathway,
                        self.user_id + extension
                    ).replace("\\", "/")
                ), await resp.read())

                return await self.update(pfp_extension=extension)

    async def create_ban(self, ban_settings: BanSettings
                         ) -> Tuple[BanModel, Ban]:
        """Used to ban user.

        Parameters
        ----------
        ban_settings : BanSettings

        Returns
        -------
        BanModel
        Ban

        Raises
        ------
        InvalidUser
        """

        now = datetime.now()

        values = {
            "ban_id": str_uuid4(),
            "user_id": self.user_id,
            "global_": True,
            "reason": ban_settings.reason,
            "timestamp": now,
            "expires": now + ban_settings.expires,
            "revoked": False,
            "banner_id": ban_settings.banner_id,
            "league_id": None
        }

        try:
            await Sessions.database.execute(
                ban_table.insert().values(
                    **values
                )
            )
        except Exception:
            raise InvalidUser()
        else:
            ban_model = BanModel(**values)

            await Sessions.scheduler.spawn(
                WebhookSender(ban_model).user_banned()
            )

            return ban_model, self.ban(values["ban_id"])

    async def exists(self) -> bool:
        """Checks if user exists.

        Returns
        -------
        bool
        """

        return await Sessions.database.fetch_val(
            select([func.count()]).select_from(user_table).where(
                user_table.c.user_id == self.user_id
            )
        ) == 1

    async def get(self) -> UserModel:
        """Used to get user.

        Returns
        -------
        UserModel

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
                user_table.c.user_id == self.user_id
            ).group_by(
                user_table.c.user_id,
                league_table.c.user_id
            )
        )

        if row:
            return UserModel(**row)
        else:
            raise InvalidUser()

    @validate_region("region")
    @validate_tickrate("tickrate", "demo_tickrate")
    async def create_league(self, league_id: str, league_name: str,
                            region: str, tickrate: int = 128,
                            demo_tickrate: int = 64,
                            disabled: bool = False, banned: bool = False,
                            allow_api_access: bool = False,
                            kill: float = 1.0,
                            death: float = -1.0, round_won: float = 1.5,
                            round_lost: float = -1.5, match_won: float = 2.0,
                            match_lost: float = -2.0, assist: float = 0.5,
                            mate_blinded: float = -0.5,
                            mate_killed: float = -2.0, headshot: float = 0.1,
                            score: float = 0.001
                            ) -> Tuple[LeagueModel, League]:
        """Used to create a league.

        Parameters
        ----------
        league_id : str
        league_name : str
        tickrate : int, optional
            by default 128
        demo_tickrate : int, optional
            by default 64
        region : str
            Valid dathost region.
        disabled : bool, optional
            by default False
        banned : bool, optional
            by default False
        allow_api_access : bool, optional
            by default False
        kill : float, optional
            by default 1.0
        death : float, optional
            by default -1.0
        round_won : float, optional
            by default 1.5
        round_lost : float, optional
            by default -1.5
        match_won : float, optional
            by default 2.0
        match_lost : float, optional
            by default -2.0
        assist : float, optional
            by default 0.5
        mate_blinded : float, optional
            by default -0.5
        mate_killed : float, optional
            by default -2.0
        headshot : float, optional
            by default 0.1
        score : float, optional
            by default 0.001

        Returns
        -------
        LeagueModel
        League

        Raises
        ------
        InvalidUser
        LeagueTaken
        """

        user = await self.get()

        values = {
            "user_id": self.user_id,
            "league_id": league_id,
            "league_name": league_name,
            "kill": kill,
            "death": death,
            "round_won": round_won,
            "round_lost": round_lost,
            "match_won": match_won,
            "match_lost": match_lost,
            "assist": assist,
            "mate_blinded": mate_blinded,
            "mate_killed": mate_killed,
            "banned": banned,
            "disabled": disabled,
            "allow_api_access": allow_api_access,
            "region": region,
            "headshot": headshot,
            "score": score,
            "timestamp": datetime.now(),
            "tickrate": tickrate,
            "demo_tickrate": demo_tickrate
        }

        try:
            await Sessions.database.execute(
                league_table.insert().values(**values)
            )
        except Exception:
            raise LeagueTaken()
        else:
            league_model = LeagueModel(
                email=user.email,
                dathost_id=user.dathost_id,
                **values
            )

            await Sessions.scheduler.spawn(
                WebhookSender(league_model, league_id).league_created()
            )

            return league_model, League(league_id)
