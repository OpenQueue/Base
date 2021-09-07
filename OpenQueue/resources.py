# -*- coding: utf-8 -*-

import dathost
import aiohttp
import aiojobs

from databases import Database
from backblaze.bucket.awaiting import AwaitingBucket
from typing import Union

from .settings.webhook import WebhookSettings
from .settings.upload import DemoSettings
from .settings.upload import PfpSettings
from .settings.upload import B2Settings
from .settings.steam import SteamSettings
from .settings.playwin import PlaywinSettings
from .settings.gametick import GameTickSettings
from .settings.database import DatabaseSettings
from .settings.smtp import SmtpSettings


class Config:
    """Config singleton.
    """

    db_engine: str

    clone_id: str

    demo: DemoSettings
    webhooks: WebhookSettings
    pfp: PfpSettings
    b2: B2Settings
    steam: SteamSettings
    playwin: Union[PlaywinSettings, None]
    game_tick: GameTickSettings
    database: DatabaseSettings
    smtp: SmtpSettings


class Sessions:
    """Session singleton.
    """

    database: Database
    bucket: AwaitingBucket
    game: dathost.Awaiting
    requests: aiohttp.ClientSession
    scheduler: aiojobs.Scheduler


class QueueGlobal:
    on_queue_full: list = []
    on_map_select: list = []
