# -*- coding: utf-8 -*-


from typing import AsyncGenerator, List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.sql import or_, select

from ..resources import Sessions
from ..tables import ban_table, ban_exception_table

from ..models.ban import BanModel

if TYPE_CHECKING:
    from ..league import League


class Users:
    def __init__(self, upper: "League", users: List[str]) -> None:
        """Used to interact with users within league context.

        Parameters
        ----------
        upper : "League"
        users : List[str]
            List of user IDs.
        """

        self.upper = upper
        self.users = users

    async def active_ban_users(self) -> AsyncGenerator[BanModel, None]:
        """Used to yield actively banned users.

        Yields
        -------
        BanModel
        """

        query = ban_table.select().where(
            ban_table.c.user_id.in_(self.users)
        ).where(
            or_(
                ban_table.c.expires == None,  # noqa: E711
                ban_table.c.expires > datetime.now()
            )
        ).where(
            ban_table.c.user_id.notin_(
                select([ban_exception_table.c.ban_id]).select_from(
                    ban_exception_table
                ).where(
                    ban_exception_table.c.league_id == self.upper.league_id
                )
            )
        )

        async for ban in Sessions.database.iterate(query):
            yield BanModel(**ban)
