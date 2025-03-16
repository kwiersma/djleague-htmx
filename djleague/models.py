from typing import Optional

from django.db import models
from django.db.models import CASCADE


class NFLTeam(models.Model):
    abbrev = models.CharField(max_length=20, unique=True)
    city = models.CharField(max_length=50)
    byeweek = models.IntegerField("bye week")

    def __str__(self):
        return "{0}".format(self.abbrev)

    class Meta:
        verbose_name = "NFL Team"
        verbose_name_plural = "NFL Teams"


class FantasyTeam(models.Model):
    name = models.CharField(max_length=100)
    owner = models.CharField(max_length=50)
    draft_order = models.IntegerField("draft order")

    exported = ("name", "owner", "draft_order")

    def as_dict(self):
        export = {attr: value for (attr, value) in self.__dict__.items() if attr in self.exported}
        export["id"] = self.id
        export["draftorder"] = self.draft_order
        return export

    def get_draftorder(self):
        return self.draft_order

    def __str__(self):
        return "{0} ({1})".format(self.name, self.owner)

    class Meta:
        verbose_name = "Fantasy Team"
        verbose_name_plural = "Fantasy Teams"


class PlayerManager(models.Manager):
    def fetch_last_picks(self) -> dict:
        fantasyTeams = FantasyTeam.objects.order_by("draft_order")
        first_team = fantasyTeams[0]
        jsonPicks = []
        lastPicks = Player.objects.exclude(round=None).exclude(pick=None).order_by("-round", "-pick")[:2]

        nextTeam = None
        nextTeam2 = None
        thisRound = 1
        thisPick = 1
        if lastPicks:
            if lastPicks[0].pick + 1 != len(fantasyTeams) + 1:
                thisRound = lastPicks[0].round
                thisPick = lastPicks[0].pick + 1
            else:
                thisRound = lastPicks[0].round + 1
                thisPick = 1
            i = 0
            for i in range(len(fantasyTeams)):
                team = fantasyTeams[i]
                if thisRound % 2:
                    # odd numbered round: we down the draft order lowest to highest
                    if team.draft_order == thisPick:
                        nextTeam = team
                        if (i + 1) < len(fantasyTeams):
                            nextTeam2 = fantasyTeams[i + 1]
                        else:
                            # we are the last pick of the round so snake around so this team gets two picks
                            # in a row
                            nextTeam2 = team
                else:
                    # even numbered round: we down the draft order highest to lowest
                    if team.draft_order == ((len(fantasyTeams) + 1) - thisPick):
                        nextTeam = team
                        if (i - 1) >= 0:
                            nextTeam2 = fantasyTeams[i - 1]
                        else:
                            # we are at the last pick of the round so snaking around so this
                            # team gets two picks in a row
                            nextTeam2 = team
        jsonPicks.append(
            {
                "fantasyTeam": nextTeam.name if nextTeam else first_team.name,
                "fantasyteam_id": nextTeam.id if nextTeam else first_team.id,
                "owner": nextTeam.owner if nextTeam else "",
                "round": thisRound,
                "pick": thisPick,
            }
        )
        jsonPicks.append(
            {
                "fantasyTeam": nextTeam2.name if nextTeam2 else "",
                "fantasyteam_id": nextTeam2.id if nextTeam2 else "",
                "owner": nextTeam2.owner if nextTeam2 else "",
                "round": "",
                "pick": "",
            }
        )
        if lastPicks:
            for lastPick in lastPicks:
                jsonPicks.append(
                    {
                        "player_id": lastPick.id,
                        "player": lastPick.lastname + ", " + lastPick.firstname,
                        "pick": lastPick.pick,
                        "round": lastPick.round,
                        "pickNo": lastPick.pickNo,
                        "fantasyteam": lastPick.fantasyteam.name if lastPick.fantasyteam is not None else "",
                        "fantasyteam_id": lastPick.fantasyteam.id if lastPick.fantasyteam is not None else "",
                        "owner": lastPick.fantasyteam.owner if lastPick.fantasyteam is not None else "",
                        "picktime": lastPick.picktime.isoformat(),
                    }
                )
        return jsonPicks


class Player(models.Model):
    firstname = models.CharField(max_length=50, null=True)
    lastname = models.CharField(max_length=50, null=True)
    pick = models.SmallIntegerField(null=True)
    points = models.SmallIntegerField(null=True)
    position = models.CharField(max_length=50)
    rank = models.SmallIntegerField(null=True)
    round = models.SmallIntegerField(null=True)
    team = models.ForeignKey(NFLTeam, to_field="abbrev", db_column="team", on_delete=CASCADE)
    url = models.CharField(max_length=200, null=True)
    fantasyteam = models.ForeignKey(FantasyTeam, blank=True, null=True, on_delete=CASCADE)
    picktime = models.DateTimeField(null=True)

    yahooID = models.IntegerField(null=True)
    avgPick = models.FloatField(null=True)
    nfl_status = models.CharField(max_length=100, null=True)

    objects = PlayerManager()

    @property
    def pickNo(self) -> Optional[int]:
        return (self.pick + (self.round - 1) * 10) if self.pick else None

    def __str__(self):
        return (
            self.lastname
            + ", "
            + self.firstname
            + " ("
            + self.position
            + " - "
            + self.team.abbrev
            + ") Rank: {0}".format(self.rank)
        )

    exported = (
        "firstname",
        "lastname",
        "pick",
        "points",
        "position",
        "rank",
        "round",
        "url",
        "avgPick",
        "nfl_status",
    )

    def as_dict(self):
        export = {attr: value for (attr, value) in self.__dict__.items() if attr in self.exported}
        export["id"] = self.id
        if self.fantasyteam:
            export["fantasyteam_id"] = self.fantasyteam_id
            export["fantasyteam"] = self.fantasyteam.name
            export["owner"] = self.fantasyteam.owner
        else:
            export["fantasyteam_id"] = ""
            export["fantasyteam"] = ""
            export["owner"] = ""
        export["byeweek"] = self.team.byeweek
        export["avgpick"] = self.avgPick
        export["team"] = self.team.abbrev

        export["pickNo"] = self.pickNo

        return export

    class Meta:
        verbose_name = "Player"
        verbose_name_plural = "Players"
