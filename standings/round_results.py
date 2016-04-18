import itertools
import logging
logger = logging.getLogger(__name__)

from django.db.models.expressions import RawSQL

from results.models import TeamScore
from participants.models import Team
from tournaments.models import Round

def add_team_round_results(standings, rounds, lookup):

    teamscores = TeamScore.objects.select_related('debate_team__team', 'debate_team__debate__round').filter(ballot_submission__confirmed=True)
    teamscores = teamscores.annotate(opposition_id=RawSQL("""
        SELECT opposition.team_id
        FROM draw_debateteam AS opposition
        WHERE opposition.debate_id = draw_debateteam.debate_id
        AND opposition.id != draw_debateteam.id""", ()
    ))
    teamscores = list(teamscores)
    oppositions = Team.objects.in_bulk([ts.opposition_id for ts in teamscores])

    for info in standings:
        info.round_results = [None] * len(rounds)

    round_lookup = {r: i for i, r in enumerate(rounds)}
    for ts in teamscores:
        ts.opposition = oppositions[ts.opposition_id]
        info = lookup(standings, ts.debate_team.team)
        info.round_results[round_lookup[ts.debate_team.debate.round]] = ts

    for info in standings:
        info.results_in = info.round_results[-1] is not None
