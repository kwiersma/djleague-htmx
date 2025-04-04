from django.urls import path

from .views import (
    HomePageView,
    TeamsView,
    TeamEditView,
    TeamRowView,
    DraftView,
    TeamPlayersView,
    DraftPlayerView,
    LastPicksView,
    UpcomingPicksView,
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("teams", TeamsView.as_view(), name="teams"),
    path("teams/<int:id>/edit", TeamEditView.as_view(), name="team_edit"),
    path("teams/<int:id>/row", TeamRowView.as_view(), name="team_row"),
    path("draft", DraftView.as_view(), name="draft"),
    path("draft/team-players", TeamPlayersView.as_view(), name="team_players"),
    path("draft/players/<int:id>/draft", DraftPlayerView.as_view(), name="draft_player"),
    path("draft/last-picks", LastPicksView.as_view(), name="last_picks"),
    path("draft/upcoming-picks", UpcomingPicksView.as_view(), name="upcoming_picks"),
]
