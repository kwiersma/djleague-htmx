from django.urls import path
from .views import HomePageView, TeamsView, TeamEditView, TeamRowView, DraftView

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("teams", TeamsView.as_view(), name="teams"),
    path("teams/<int:id>/edit", TeamEditView.as_view(), name="team_edit"),
    path("teams/<int:id>/row", TeamRowView.as_view(), name="team_row"),
    path("draft", DraftView.as_view(), name="draft"),
]
