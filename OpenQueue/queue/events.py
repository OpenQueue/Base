# -*- coding: utf-8 -*-

from ..resources import QueueGlobal


def on_queue_full():
    """Called when queue is full.
    """

    def decorator(func):
        QueueGlobal.on_queue_full.append(func)

    return decorator


def on_map_select():
    """Called when map selected.
    """

    def decorator(func):
        QueueGlobal.on_map_select.append(func)

    return decorator
