from django import forms

from djleague.models import FantasyTeam


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
