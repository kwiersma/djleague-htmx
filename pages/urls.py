from django.urls import path

from .views import HomePageView, TeamsView

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("teams", TeamsView.as_view(), name="teams"),
]
