# -*- coding: utf-8 -*-

from typing import Dict
from aiohttp import ClientTimeout

from ..constants import WEBHOOK_EVENTS


class WebhookSettings:
    def __init__(self, key: str = None,
                 global_webhooks: Dict[int, str] = None,
                 global_webhook_url: str = "https://skrim.gg/api/caching/",
                 timeout: float = 3.0
                 ) -> None:
        """Master webhook settings.

        Parameters
        ----------
        key : str, optional
            Webhook key, by default None
        global_webhooks : Dict[int, str], optional
            If None WEBHOOK_EVENTS constant will be use.
        global_webhook_url: str, optional
            by default "https://skrim.gg/api/caching/"
        timeout : float, optional
        """

        self.timeout = ClientTimeout(total=timeout)  # type: ignore
        self.key = key
        if global_webhooks:
            self.global_webhooks = global_webhooks
        else:
            self.global_webhooks = {
                event_id: event_name
                for event_name, event_id in WEBHOOK_EVENTS.items()
            }
        self.global_webhook_url = global_webhook_url
