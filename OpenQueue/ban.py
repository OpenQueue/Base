# -*- coding: utf-8 -*-

from sqlalchemy.sql import and_

from .models.ban import BanRevokedModel, BanModel

from .exceptions import InvalidBan
from .resources import Sessions
from .tables import ban_table, ban_exception_table
from .webhook import WebhookSender


class Ban:
    def __init__(self, ban_id: str, user_id: str,
                 league_id: str = None) -> None:
        """Used to interact with a ban.

        Parameters
        ----------
        ban_id : str
        user_id : str
        league_id : str, optional
            If ban is within context of league.
        """

        self.ban_id = ban_id
        self.user_id = user_id
        self.league_id = league_id

    @property
    def __and_statement(self) -> and_:
        return and_(
            ban_table.c.ban_id == self.ban_id,
            ban_table.c.user_id == self.user_id,
            ban_table.c.league_id == self.league_id
        )

    async def get(self) -> BanModel:
        """Used to get ban.

        Returns
        -------
        BanModel

        Raises
        ------
        InvalidBan
        """

        row = await Sessions.database.fetch_one(
            ban_table.select().where(self.__and_statement)
        )

        if row:
            return BanModel(**row)
        else:
            raise InvalidBan()

    async def league_exception(self) -> None:
        """Used to ignore a global ban for a league.

        Raises
        ------
        InvalidBan
        """

        assert self.league_id

        try:
            await Sessions.database.execute(
                ban_exception_table.insert().values(
                    ban_id=self.ban_id,
                    league_id=self.league_id
                )
            )
        except Exception:
            raise InvalidBan()

        await Sessions.scheduler.spawn(
            WebhookSender(
                BanRevokedModel(
                    self.user_id,
                    self.ban_id,
                    True,
                    self.league_id
                ),
                self.league_id
            ).user_ban_revoked()
        )

    async def revoke(self) -> None:
        """Used to revoke a ban.
        """

        await Sessions.database.execute(
            ban_table.update().values(
                revoked=True
            ).where(
                self.__and_statement
            )
        )

        await Sessions.scheduler.spawn(
            WebhookSender(
                BanRevokedModel(
                    self.user_id,
                    self.ban_id,
                    True,
                    self.league_id
                ),
                self.league_id
            ).user_ban_revoked()
        )
