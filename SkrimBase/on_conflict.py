# -*- coding: utf-8 -*-

from typing import Any
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as postgresql_insert

from .tables import scoreboard_table, statistic_table
from .resources import Config


def on_scoreboard_conflict() -> Any:
    """Used for updating a player on a scoreboard on conflict.
    """

    if Config.database.engine == "mysql":
        query_insert = mysql_insert(scoreboard_table)
        return query_insert.on_duplicate_key_update(
            captain=scoreboard_table.c.captain,
            team=query_insert.inserted.team,
            alive=query_insert.inserted.alive,
            ping=query_insert.inserted.ping,
            kills=scoreboard_table.c.kills + query_insert.inserted.kills,
            headshots=scoreboard_table.c.headshots +
            query_insert.inserted.headshots,
            assists=scoreboard_table.c.assists + query_insert.inserted.assists,
            deaths=scoreboard_table.c.deaths + query_insert.inserted.deaths,
            shots_fired=scoreboard_table.c.shots_fired +
            query_insert.inserted.shots_fired,
            shots_hit=scoreboard_table.c.shots_hit +
            query_insert.inserted.shots_hit,
            mvps=scoreboard_table.c.mvps + query_insert.inserted.mvps,
            score=scoreboard_table.c.score + query_insert.inserted.score,
            disconnected=query_insert.inserted.disconnected
        )
    elif Config.database.engine == "psycopg2":
        query_insert = postgresql_insert(scoreboard_table)
        return query_insert.on_conflict_do_update(
            set_=dict(
                captain=scoreboard_table.c.captain,
                team=query_insert.inserted.team,
                alive=query_insert.inserted.alive,
                ping=query_insert.inserted.ping,
                kills=scoreboard_table.c.kills + query_insert.inserted.kills,
                headshots=scoreboard_table.c.headshots +
                query_insert.inserted.headshots,
                assists=scoreboard_table.c.assists
                + query_insert.inserted.assists,
                deaths=scoreboard_table.c.deaths
                + query_insert.inserted.deaths,
                shots_fired=scoreboard_table.c.shots_fired +
                query_insert.inserted.shots_fired,
                shots_hit=scoreboard_table.c.shots_hit +
                query_insert.inserted.shots_hit,
                mvps=scoreboard_table.c.mvps + query_insert.inserted.mvps,
                score=scoreboard_table.c.score + query_insert.inserted.score,
                disconnected=query_insert.inserted.disconnected
            )
        )
    else:
        return scoreboard_table.insert


def on_statistic_conflict() -> Any:
    """Used for updating a statistics on conflict.
    """

    if Config.database.engine == "mysql":
        query_insert = mysql_insert(statistic_table)
        return query_insert.on_duplicate_key_update(
            kills=statistic_table.c.kills + query_insert.inserted.kills,
            headshots=statistic_table.c.headshots +
            query_insert.inserted.headshots,
            assists=statistic_table.c.assists + query_insert.inserted.assists,
            deaths=statistic_table.c.deaths + query_insert.inserted.deaths,
            shots_fired=statistic_table.c.shots_fired +
            query_insert.inserted.shots_fired,
            shots_hit=statistic_table.c.shots_hit +
            query_insert.inserted.shots_hit,
            mvps=statistic_table.c.mvps + query_insert.inserted.mvps,
            elo=statistic_table.c.elo + query_insert.inserted.elo
        )
    elif Config.database.engine == "psycopg2":
        query_insert = postgresql_insert(statistic_table)
        return query_insert.on_conflict_do_update(
            set_=dict(
                kills=statistic_table.c.kills + query_insert.inserted.kills,
                headshots=statistic_table.c.headshots +
                query_insert.inserted.headshots,
                assists=statistic_table.c.assists +
                query_insert.inserted.assists,
                deaths=statistic_table.c.deaths + query_insert.inserted.deaths,
                shots_fired=statistic_table.c.shots_fired +
                query_insert.inserted.shots_fired,
                shots_hit=statistic_table.c.shots_hit +
                query_insert.inserted.shots_hit,
                mvps=statistic_table.c.mvps + query_insert.inserted.mvps,
                elo=statistic_table.c.elo + query_insert.inserted.elo
            )
        )
    else:
        return statistic_table.insert
