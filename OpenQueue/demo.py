# -*- coding: utf-8 -*-

from typing import TYPE_CHECKING
from sqlalchemy.sql import and_
from os import path
from dathost.exceptions import NotFound
from dathost.server.awaiting import ServerAwaiting
from backblaze.settings import UploadSettings, PartSettings
from zipstream import AioZipStream

from .resources import Sessions, Config
from .webhook import WebhookSender
from .tables import scoreboard_total_table

from .models.match import DemoModel

if TYPE_CHECKING:
    from .league.match import Match


class Demo:
    def __init__(self, server: ServerAwaiting, match: "Match") -> None:
        """Used to upload demos to b2.

        Parameters
        ----------
        server : ServerAwaiting
        match : "Match"
        """

        self.server = server
        self.match = match

    @property
    def __file_name(self) -> str:
        return self.match.match_id + Config.demo.extension

    @property
    def __demo_pathway(self) -> str:
        pathway = path.join(
            Config.demo.pathway,
            self.match.match_id + Config.demo.compressed_extension
        )

        return pathway.replace("\\", "/")

    async def __update_value(self, **kwargs) -> None:
        await Sessions.database.execute(
            scoreboard_total_table.update().values(
                **kwargs
            ).where(
                and_(
                    scoreboard_total_table.c.match_id == self.match.match_id,
                    scoreboard_total_table.c.league_id ==
                    self.match.upper.league_id
                )
            )
        )

    async def upload(self) -> None:
        """Compresses and uploads demo from dathost to b2.
        """

        await self.__update_value(demo_status=1)

        server_file = self.server.file(self.__file_name)
        aiozip = AioZipStream([{
            "stream": server_file.download_iterate(),
            "name": self.__file_name,
            "compression": "deflate"
        }])

        content_type = "application/octet-stream"

        model, file = await Sessions.bucket.create_part(PartSettings(
            self.__demo_pathway,
            content_type=content_type
        ))

        parts = file.parts()

        chunked = b""
        total_size = 0

        try:
            async for chunk in aiozip.stream():
                chunked += chunk

                if len(chunked) >= 5000024:
                    await parts.data(chunked)

                    total_size += len(chunked)
                    chunked = b""
        except NotFound:
            return

        if chunked:
            if parts.part_number == 0:
                await file.cancel()

                model, _ = await Sessions.bucket.upload(UploadSettings(
                    self.__demo_pathway,
                    content_type=content_type
                ), chunked)
            else:
                await parts.data(chunked)
                total_size += len(chunked)

                await parts.finish()
        else:
            await parts.finish()

        await self.__update_value(
            b2_id=model.file_id,
            demo_status=2
        )

        webhook = WebhookSender(
            DemoModel(self.match.match_id, self.match.upper.league_id, 2),
            self.match.upper.league_id
        )

        await Sessions.scheduler.spawn(webhook.demo_uploaded())
        await Sessions.scheduler.spawn(self.match.analyze_demo())
