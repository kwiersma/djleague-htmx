import django_filters
from django import forms

from djleague.models import FantasyTeam, Player


class FantasyTeamForm(forms.ModelForm):

    class Meta:
        model = FantasyTeam
        fields = ("name", "owner", "draft_order")


class FantasyTeamInlineForm(forms.ModelForm):
    draft_order = forms.IntegerField(label="", required=True, min_value=0, max_value=14)
    name = forms.CharField(label="", required=True)
    owner = forms.CharField(label="", required=True)

    class Meta:
        model = FantasyTeam
        fields = ("name", "owner", "draft_order")


class PlayersFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(
        label="Status",
        choices=[("0", "Available"), ("1", "Drafted")],
    )
    position = django_filters.ChoiceFilter(
        label="Position",
        field_name="position",
        choices=[
            ("QB", "QB"),
            ("RB", "RB"),
            ("WR", "WR"),
            ("TE", "TE"),
            ("K", "K"),
            ("DEF", "DEF"),
        ],
    )
    lastname = django_filters.CharFilter(label="Last Name", field_name="lastname", lookup_expr="istartswith")

    sort = django_filters.OrderingFilter(
        fields=(
            ("rank", "rank"),
            ("adp", "avgPick"),
            ("points", "points"),
            ("lastname", "lastname"),
        ),
    )

    class Meta:
        model = Player
        fields = ("lastname",)

    def query_string(self) -> str:
        qstring = "?d=1"
        fields = ["lastname", "position", "status"]
        for fieldname in fields:
            if self.data.get(fieldname) and self.data.get(fieldname) != "None":
                qstring += f"&{fieldname}={self.data.get(fieldname)}"
        return qstring
