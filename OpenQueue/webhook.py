# -*- coding: utf-8 -*-

from aiohttp import BasicAuth, ClientConnectionError

from sqlalchemy.sql import select, and_

from .resources import Config, Sessions
from .tables import webhook_table
from .constants import WEBHOOK_EVENTS
from .models.base import ApiSchema


class WebhookSender:
    def __init__(self, model: ApiSchema, league_id: str = None) -> None:
        """Used to send webhooks to URL.

        Parameters
        ----------
        league_id : str, optional
            by default None
        model : Type[ApiSchema]
            Must have .api_schema param.
        """

        self.league_id = league_id
        self.api_schema = model.api_schema(True)

    async def __send(self, url: str, key: str = None,
                     additional_data: dict = None,
                     additional_headers: dict = {}) -> None:
        """Used to send payload.

        Parameters
        ----------
        url : str
        key : str, optional
            by default None
        additional_data : dict, optional
            by default None
        additional_headers : dict, optional
            by default None
        """

        if additional_data:
            payload = {
                **self.api_schema,
                **additional_data
            }
        else:
            payload = self.api_schema

        try:
            await Sessions.requests.post(
                url,
                timeout=Config.webhooks.timeout,
                json=payload,
                auth=BasicAuth("", key) if key else None,
                headers=additional_headers
            )
        except ClientConnectionError:
            pass

    async def __event(self, event_id: int) -> None:
        """Used to send json to URL based off league_id & event_id.

        Parameters
        ----------
        event_id : int
            ID of event.
        """

        # Fixed API webhooks.
        # These are for dynamic redis caching on the API.
        # Ensures data between API & Base are identical no matter
        # if its used for the API or not.

        if (Config.webhooks.global_webhook_url and
                event_id in Config.webhooks.global_webhooks):
            await self.__send(
                Config.webhooks.global_webhook_url,
                Config.webhooks.key,
                {
                    "__wh_event_id": event_id,
                    "league_id": self.league_id
                },
                {"CachingWebhook": "true"}
            )

        if self.league_id:
            and_statement = and_(
                webhook_table.c.event_id == event_id,
                webhook_table.c.league_id == self.league_id
            )
        else:
            and_statement = webhook_table.c.event_id == event_id

        query = select([
            webhook_table.c.url,
            webhook_table.c.webhook_key
        ]).select_from(webhook_table).where(and_statement)

        async for row in Sessions.database.iterate(query):
            await self.__send(
                row["url"],
                row["webhook_key"] if self.league_id else Config.webhooks.key
            )

    async def match_update(self) -> None:
        """Used to send match update webhook.
        """

        await self.__event(WEBHOOK_EVENTS["match.update"])

    async def match_end(self) -> None:
        """Used to send match end webhook.
        """

        await self.__event(WEBHOOK_EVENTS["match.end"])

    async def match_start(self) -> None:
        """Used to send match start webhook.
        """

        await self.__event(WEBHOOK_EVENTS["match.start"])

    async def demo_uploaded(self) -> None:
        """Used to send demo uploaded webhook
        """

        await self.__event(WEBHOOK_EVENTS["demo.uploaded"])

    async def user_banned(self) -> None:
        """Used to send user banned webhook.
        """

        await self.__event(WEBHOOK_EVENTS["user.banned"])

    async def user_ban_revoked(self) -> None:
        """Used to send user ban revoked webhook.
        """

        await self.__event(WEBHOOK_EVENTS["user.ban.revoked"])

    async def league_created(self) -> None:
        """Used to send league created webhook
        """

        await self.__event(WEBHOOK_EVENTS["league.created"])

    async def league_updated(self) -> None:
        """Used tp send league updated webhooks.
        """

        await self.__event(WEBHOOK_EVENTS["league.updated"])

    async def user_created(self) -> None:
        """Called when user created.
        """

        await self.__event(WEBHOOK_EVENTS["user.created"])

    async def user_updated(self) -> None:
        """Called when user updated.
        """

        await self.__event(WEBHOOK_EVENTS["user.updated"])

    async def league_user_created(self) -> None:
        """Called when league user created.
        """

        await self.__event(WEBHOOK_EVENTS["league.user.created"])

    async def league_user_updated(self) -> None:
        """Called when league user updated.
        """

        await self.__event(WEBHOOK_EVENTS["league.user.updated"])
