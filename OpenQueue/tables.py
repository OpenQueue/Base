# -*- coding: utf-8 -*-


from sqlalchemy import (
    String,
    Integer,
    Boolean,
    Float,
    BigInteger,
    PrimaryKeyConstraint,
    ForeignKey,
    Table,
    MetaData,
    Column,
    TIMESTAMP,
    TEXT,
    LargeBinary,
    create_engine,
    UniqueConstraint
)

from datetime import datetime


metadata = MetaData()


# Server table
server_table = Table(
    "server",
    metadata,
    Column(
        "server_id",
        String(length=36),
        primary_key=True
    ),
    Column(
        "game_token",
        String(length=32)
    ),
    Column(
        "game_token_id",
        String(length=64)
    ),
    Column(
        "game_token_expires",
        TIMESTAMP
    ),
    Column(
        "month_credits",
        Float
    ),
    Column(
        "month_reset_at",
        TIMESTAMP
    ),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4"
)


# Update table
update_table = Table(
    "update",
    metadata,
    Column(
        "major",
        Integer,
        primary_key=True
    ),
    Column(
        "minor",
        Integer,
        primary_key=True
    ),
    Column(
        "patch",
        Integer,
        primary_key=True
    ),
    Column(
        "message",
        TEXT
    ),
    PrimaryKeyConstraint(
        "major",
        "minor",
        "patch"
    ),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4"
)


# User table
user_table = Table(
    "user",
    metadata,
    Column(
        "name",
        String(length=36)
    ),
    Column(
        "user_id",
        String(length=36),
        primary_key=True
    ),
    Column(
        "steam_id",
        String(length=64),
        unique=True
    ),
    Column(
        "discord_id",
        BigInteger,
        unique=True
    ),
    Column(
        "dathost_id",
        String(length=36),
        nullable=True
    ),
    Column(
        "pfp_extension",
        String(length=6),
        nullable=True
    ),
    Column(
        "email",
        String(length=255),
        unique=True
    ),
    Column(
        "email_confirmed",
        Boolean
    ),
    Column(
        "email_code",
        String(length=48)
    ),
    Column(
        "password",
        LargeBinary()
    ),
    Column(
        "timestamp",
        TIMESTAMP,
        default=datetime.now
    ),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4"
)


# Integration table
integration_table = Table(
    "integration",
    metadata,
    Column(
        "name",
        String(length=36),
        primary_key=True
    ),
    Column(
        "logo",
        String(length=255)
    ),
    Column(
        "auth_url",
        String(length=555)
    ),
    Column(
        "globally_required",
        Boolean
    ),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4"
)


# League table
league_table = Table(
    "league",
    metadata,
    Column(
        "league_id",
        String(length=6),
        primary_key=True
    ),
    Column(
        "league_name",
        String(length=32)
    ),
    Column(
        "region",
        String(length=20)
    ),
    Column(
        "user_id",
        String(length=36),
        ForeignKey("user.user_id")
    ),
    Column(
        "disabled",
        Boolean,
        default=False
    ),
    Column(
        "banned",
        Boolean,
        default=False
    ),
    Column(
        "allow_api_access",
        Boolean
    ),
    Column(
        "timestamp",
        TIMESTAMP,
        default=datetime.now
    ),
    Column(
        "tickrate",
        Integer
    ),
    Column(
        "demo_tickrate",
        Integer
    ),
    Column(
        "kill",
        Float
    ),
    Column(
        "death",
        Float
    ),
    Column(
        "headshot",
        Float
    ),
    Column(
        "score",
        Float
    ),
    Column(
        "round_won",
        Float
    ),
    Column(
        "round_lost",
        Float
    ),
    Column(
        "match_won",
        Float
    ),
    Column(
        "match_lost",
        Float
    ),
    Column(
        "assist",
        Float
    ),
    Column(
        "mate_blinded",
        Float
    ),
    Column(
        "mate_killed",
        Float
    ),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4"
)


# league integration table
league_integration_table = Table(
    "league_integration",
    metadata,
    Column(
        "name",
        String(length=36),
        ForeignKey("integration.name")
    ),
    Column(
        "league_id",
        String(length=6),
        ForeignKey("league.league_id")
    ),
    UniqueConstraint(
        "name",
        "league_id"
    ),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4"
)


# Ban table
ban_table = Table(
    "ban",
    metadata,
    Column(
        "ban_id",
        String(length=36),
        primary_key=True
    ),
    Column(
        "user_id",
        String(length=36),
        ForeignKey("user.user_id")
    ),
    Column(
        "league_id",
        String(length=6),
        ForeignKey("league.league_id"),
        nullable=True
    ),
    Column(
        "global_",
        Boolean
    ),
    Column(
        "revoked",
        Boolean
    ),
    Column(
        "reason",
        TEXT
    ),
    Column(
        "timestamp",
        TIMESTAMP
    ),
    Column(
        "expires",
        TIMESTAMP,
        nullable=True
    ),
    Column(
        "banner_id",
        String(length=36),
        ForeignKey("user.user_id")
    ),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4"
)


# Ban exceptions table
# Used for leagues to ignore global bans.
ban_exception_table = Table(
    "ban_exception",
    metadata,
    Column(
        "ban_id",
        String(length=36),
        ForeignKey("ban.ban_id"),
        primary_key=True
    ),
    Column(
        "league_id",
        String(length=6),
        ForeignKey("league.league_id")
    ),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4"
)


# Events table
event_table = Table(
    "event",
    metadata,
    Column(
        "event_id",
        Integer,
        primary_key=True
    ),
    Column(
        "event_type",
        String(length=20)
    ),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4"
)


# Webhooks table
webhook_table = Table(
    "webhook",
    metadata,
    Column(
        "webhook_key",
        String(length=32),
        primary_key=True
    ),
    Column(
        "url",
        String(length=255)
    ),
    Column(
        "event_id",
        Integer,
        ForeignKey("event.event_id")
    ),
    Column(
        "league_id",
        String(length=6),
        ForeignKey("league.league_id")
    ),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4"
)


# Admin table
admin_table = Table(
    "admin",
    metadata,
    Column(
        "user_id",
        String(length=36),
        ForeignKey("user.user_id"),
        primary_key=True
    ),
    Column(
        "league_id",
        String(length=6),
        ForeignKey("league.league_id"),
        primary_key=True
    ),
    PrimaryKeyConstraint(
        "user_id",
        "league_id",
        sqlite_on_conflict="REPLACE"
    ),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4"
)


# Statistic table
statistic_table = Table(
    "statistic",
    metadata,
    Column(
        "user_id",
        String(length=36),
        ForeignKey("user.user_id"),
        primary_key=True
    ),
    Column(
        "league_id",
        String(length=6),
        ForeignKey("league.league_id"),
        primary_key=True
    ),
    Column(
        "elo",
        Float
    ),
    Column(
        "kills",
        Integer,
        default=0
    ),
    Column(
        "headshots",
        Integer,
        default=0
    ),
    Column(
        "assists",
        Integer,
        default=0
    ),
    Column(
        "deaths",
        Integer,
        default=0
    ),
    Column(
        "shots_fired",
        Integer,
        default=0
    ),
    Column(
        "shots_hit",
        Integer,
        default=0
    ),
    Column(
        "mvps",
        Integer,
        default=0
    ),
    PrimaryKeyConstraint(
        "user_id",
        "league_id",
        sqlite_on_conflict="REPLACE"
    ),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4"
)


# Scoreboard total table
# Status codes
# 0 - Finished
# 1 - Live
# 2 - Processing

# Demo status codes
# 0 - No demo
# 1 - Processing
# 2 - Ready for Download
# 3 - Too large
# 4 - Expired

# Team Sides
# 0 - CT
# 1 - T

# You may be asking why we store IPs & Ports here
# and not in the server table. The server / ports
# can change after the server startups.
scoreboard_total_table = Table(
    "scoreboard_total",
    metadata,
    Column(
        "match_id",
        String(length=36),
        primary_key=True
    ),
    Column(
        "league_id",
        String(length=6),
        ForeignKey("league.league_id"),
        primary_key=True
    ),
    Column(
        "raw_ip",
        String(length=15)
    ),
    Column(
        "game_port",
        Integer
    ),
    Column(
        "server_id",
        String(length=36),
        ForeignKey("server.server_id")
    ),
    Column(
        "b2_id",
        String(length=200),
        nullable=True
    ),
    Column(
        "timestamp",
        TIMESTAMP,
        default=datetime.now
    ),
    Column(
        "status",
        Integer
    ),
    Column(
        "demo_status",
        Integer
    ),
    Column(
        "map",
        String(length=24)
    ),
    Column(
        "team_1_name",
        String(length=64)
    ),
    Column(
        "team_2_name",
        String(length=64)
    ),
    Column(
        "team_1_score",
        Integer,
        default=0
    ),
    Column(
        "team_2_score",
        Integer,
        default=0
    ),
    Column(
        "team_1_side",
        Integer,
        default=0
    ),
    Column(
        "team_2_side",
        Integer,
        default=0
    ),
    PrimaryKeyConstraint(
        "match_id",
        "league_id"
    ),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4"
)


# Team Codes
# 0 = Team 1
# 1 = Team 2
scoreboard_table = Table(
    "scoreboard",
    metadata,
    Column(
        "match_id",
        String(length=36),
        ForeignKey("scoreboard_total.match_id", ondelete="CASCADE"),
        primary_key=True
    ),
    Column(
        "user_id",
        String(length=36),
        ForeignKey("user.user_id"),
        primary_key=True
    ),
    Column(
        "captain",
        Boolean
    ),
    Column(
        "team",
        Integer
    ),
    Column(
        "alive",
        Boolean,
        default=True
    ),
    Column(
        "ping",
        Integer,
        default=0
    ),
    Column(
        "kills",
        Integer,
        default=0
    ),
    Column(
        "headshots",
        Integer,
        default=0
    ),
    Column(
        "assists",
        Integer,
        default=0
    ),
    Column(
        "deaths",
        Integer,
        default=0
    ),
    Column(
        "shots_fired",
        Integer,
        default=0
    ),
    Column(
        "shots_hit",
        Integer,
        default=0
    ),
    Column(
        "mvps",
        Integer,
        default=0
    ),
    Column(
        "score",
        Integer,
        default=0
    ),
    Column(
        "disconnected",
        Boolean,
        default=False
    ),
    PrimaryKeyConstraint(
        "user_id",
        "match_id",
        sqlite_on_conflict="REPLACE"
    ),
    mysql_engine="InnoDB",
    mysql_charset="utf8mb4"
)


def create_tables(database_url: str) -> None:
    """Creates tables.
    """

    metadata.create_all(
        create_engine(database_url)
    )
