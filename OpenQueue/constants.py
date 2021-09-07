# -*- coding: utf-8 -*-

# Dathost region codes!

REGIONS = [
    "amsterdam",
    "barcelona",
    "bristol",
    "chicago",
    "dallas",
    "dusseldorf",
    "istanbul",
    "los_angeles",
    "moscow",
    "new_york_city",
    "portland",
    "singapore",
    "stockholm",
    "strasbourg",
    "sydney",
    "warsaw"
]


# Both key & value should be unique.
# Uses number substitution cypher
# Shouldn't really ever change.
# 14 = N; 12 = L

WEBHOOK_EVENTS = {
    "match.end": 141201,
    "match.start": 141202,
    "match.update": 141203,
    "demo.uploaded": 141204,
    "user.banned": 141205,
    "user.ban.revoked": 141206,
    "league.created": 141207,
    "league.updated": 141208,
    "user.created": 141209,
    "user.updated": 141210,
    "league.user.created": 141211,
    "league.user.updated": 141212,
}


# Just checking for duplicated event ids.
for event_id in WEBHOOK_EVENTS.values():
    assert list(
        WEBHOOK_EVENTS.values()
    ).count(event_id) == 1, f"{event_id} isn't unique."
