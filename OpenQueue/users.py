# -*- coding: utf-8 -*-


from typing import AsyncGenerator, List, Tuple
from sqlalchemy.sql import select
from datetime import datetime

from .tables import user_table, ban_table
from .resources import Sessions
from .exceptions import InvalidUser
from .settings.ban import BanSettings
from .models.ban import BanModel
from .ban import Ban
from .webhook import WebhookSender
from .misc import str_uuid4


class Users:
    def __init__(self, user_ids: List[str]) -> None:
        """Used to interact with a list of users.

        Parameters
        ----------
        user_ids : List[str]
            List of user IDs.
        """

        self.user_ids = user_ids

    async def create_ban(self, ban_settings: BanSettings
                         ) -> AsyncGenerator[Tuple[BanModel, Ban], None]:
        """Used to create bans.

        Parameters
        ----------
        ban_settings : BanSettings

        Returns
        -------
        BanModel
        Ban
        """

        now = datetime.now()
        expires = now + ban_settings.expires

        bans = []
        bans_append = bans.append

        for user_id in self.user_ids:
            values = {
                "ban_id": str_uuid4(),
                "user_id": user_id,
                "global_": False,
                "reason": ban_settings.reason,
                "timestamp": now,
                "expires": expires,
                "revoked": False,
                "banner_id": ban_settings.banner_id,
                "league_id": None
            }

            bans_append(values)

            ban_model = BanModel(**values)

            await Sessions.scheduler.spawn(
                WebhookSender(ban_model).user_banned()
            )

            yield ban_model, Ban(values["ban_id"], values["user_id"])

        try:
            await Sessions.database.execute_many(
                ban_table.insert(), bans
            )
        except Exception:
            raise InvalidUser()

    async def validate(self) -> None:
        """Used to check if users are valid.

        Raises
        ------
        InvalidUser
            If users invalid.
        """

        user_ids_clone = list(self.user_ids)

        query = select([
            user_table.c.user_id
        ]).select_from(user_table).where(
            user_table.c.user_id.in_(self.user_ids)
        )

        async for row in Sessions.database.iterate(query=query):
            user_ids_clone.remove(row["user_id"])

        if len(user_ids_clone) != 0:
            raise InvalidUser(
                invalid_users=user_ids_clone
            )
