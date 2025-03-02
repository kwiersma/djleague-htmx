from django.views import generic
from django.views.generic import TemplateView

from djleague.models import FantasyTeam


class HomePageView(TemplateView):
    template_name = "pages/home.html"


class TeamsView(generic.ListView):
    template_name = "fantasyteams/index.html"
    context_object_name = "teams"

    def get_queryset(self):
        return FantasyTeam.objects.order_by("draft_order")
