from typing import AsyncGenerator, Callable, Tuple, TYPE_CHECKING
from sqlalchemy import select, and_, or_, func

from ..tables import scoreboard_table, scoreboard_total_table, user_table
from ..models.match import MatchModel
from ..resources import Sessions

if TYPE_CHECKING:
    from .match import Match


async def matches(match: Callable[[str], "Match"], league_id: str,
                  user_id: str = None, search: str = None,
                  page: int = 1, limit: int = 10, desc: bool = True
                  ) -> AsyncGenerator[Tuple[MatchModel, "Match"], None]:
    """Used to list matches.

    Parameters
    ----------
    match : Match
    league_id : str
    user_id : str, optional
        by default None
    search : str, optional
        by default None
    page : int, optional
        by default 1
    limit : int, optional
        by default 10
    desc : bool, optional
        by default True

    Yields
    ------
    MatchModel
        Holds basic match details.
    Match
        Used for interacting with a match.
    """

    capt_team_1 = user_table.alias("capt_team_1")
    capt_team_2 = user_table.alias("capt_team_2")
    team_1_scoreboard = scoreboard_table.alias("team_1_scoreboard")
    team_2_scoreboard = scoreboard_table.alias("team_2_scoreboard")

    team_1_join = {
        "right": team_1_scoreboard.join(
            capt_team_1,
            and_(
                capt_team_1.c.user_id == team_1_scoreboard.c.user_id,
                team_1_scoreboard.c.team == 0,
                team_1_scoreboard.c.captain == True  # noqa: E712
            )
        ),
        "onclause": team_1_scoreboard.c.match_id ==
        scoreboard_total_table.c.match_id,
        "isouter": True
    }

    team_2_join = {
        "right": team_2_scoreboard.join(
            capt_team_2,
            and_(
                capt_team_2.c.user_id == team_2_scoreboard.c.user_id,
                team_2_scoreboard.c.team == 1,
                team_2_scoreboard.c.captain == True  # noqa: E712
            )
        ),
        "onclause": team_2_scoreboard.c.match_id ==
        scoreboard_total_table.c.match_id,
        "isouter": True
    }

    query = select([
        scoreboard_total_table.c.match_id,
        scoreboard_total_table.c.league_id,
        scoreboard_total_table.c.raw_ip,
        scoreboard_total_table.c.game_port,
        scoreboard_total_table.c.server_id,
        scoreboard_total_table.c.b2_id,
        scoreboard_total_table.c.timestamp,
        scoreboard_total_table.c.status,
        scoreboard_total_table.c.demo_status,
        scoreboard_total_table.c.map,
        scoreboard_total_table.c.team_1_name,
        scoreboard_total_table.c.team_2_name,
        scoreboard_total_table.c.team_1_score,
        scoreboard_total_table.c.team_2_score,
        scoreboard_total_table.c.team_1_side,
        scoreboard_total_table.c.team_2_side,
        capt_team_1.c.user_id.label("capt_team_1_user_id"),
        capt_team_2.c.user_id.label("capt_team_2_user_id"),
        capt_team_1.c.pfp_extension.label("capt_team_1_pfp_extension"),
        capt_team_2.c.pfp_extension.label("capt_team_2_pfp_extension"),
        func.group_concat(user_table.c.user_id).label("user_ids"),
        func.group_concat(
            user_table.c.pfp_extension
        ).label("user_pfp_extensions"),
        func.group_concat(user_table.c.name).label("user_names"),
        func.group_concat(scoreboard_table.c.team).label("user_teams")
    ])

    if search:
        like_search = "%{}%".format(search)

        query = query.select_from(
            scoreboard_total_table.join(
                scoreboard_table,
                scoreboard_table.c.
                match_id == scoreboard_total_table.c.match_id
            ).join(
                user_table,
                user_table.c.user_id == scoreboard_table.c.user_id
            ).join(**team_1_join).join(**team_2_join)
        ).where(
            and_(
                scoreboard_total_table.c.league_id == league_id,
                or_(
                    scoreboard_total_table.c.match_id == search,
                    scoreboard_total_table.c.map.like(like_search),
                    scoreboard_total_table.c.team_1_name.like(like_search),
                    scoreboard_total_table.c.team_2_name.like(like_search),
                    user_table.c.name.like(like_search),
                    user_table.c.user_id == search,
                    user_table.c.steam_id == search
                )
            )
        )

        if user_id:
            query = query.where(
                scoreboard_table.c.user_id == user_id
            )
    else:
        query = query.select_from(
            scoreboard_total_table.join(
                scoreboard_table,
                scoreboard_table.c.
                match_id == scoreboard_total_table.c.match_id
            ).join(**team_1_join).join(**team_2_join).join(
                user_table,
                user_table.c.user_id == scoreboard_table.c.user_id
            )
        )
        if user_id:
            query = query.where(
                and_(
                    scoreboard_total_table.c.league_id == league_id,
                    scoreboard_table.c.user_id == user_id
                )
            )
        else:
            query = query.where(
                scoreboard_total_table.c.league_id == league_id
            )

    query = query.distinct().order_by(
        scoreboard_total_table.c.timestamp.desc() if desc
        else scoreboard_total_table.c.timestamp.asc()
    ).limit(limit).offset((page - 1) * limit if page > 1 else 0).group_by(
        scoreboard_total_table.c.match_id
    )

    async for row in Sessions.database.iterate(query=query):
        yield MatchModel(**row), match(row["match_id"])
