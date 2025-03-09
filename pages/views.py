from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic
from django.views.generic import TemplateView

from djleague.models import FantasyTeam
from pages.forms import FantasyTeamForm, FantasyTeamInlineForm


class HomePageView(TemplateView):
    template_name = "pages/home.html"


class TeamsView(generic.ListView):
    template_name = "fantasyteams/index.html"
    context_object_name = "teams"

    def get_queryset(self):
        return FantasyTeam.objects.order_by("draft_order")


class TeamEditView(generic.UpdateView):
    template_name = "fantasyteams/_edit.html"
    context_object_name = "team"

    def get(self, request, *args, **kwargs):
        if not kwargs.get("id"):
            raise Http404()
        try:
            team = FantasyTeam.objects.get(pk=kwargs.get("id"))
        except FantasyTeam.DoesNotExist:
            raise Http404()

        if not request.headers.get("HX-Request"):
            self.template_name = "fantasyteams/edit.html"
            form = FantasyTeamForm(instance=team)
        else:
            form = FantasyTeamInlineForm(instance=team)
        return self.render_to_response(dict(form=form))

    def post(self, request, *args, **kwargs):
        if not kwargs.get("id"):
            raise Http404()
        try:
            team = FantasyTeam.objects.get(pk=kwargs.get("id"))
        except FantasyTeam.DoesNotExist:
            raise Http404()

        if not request.headers.get("HX-Request"):
            self.template_name = "fantasyteams/edit.html"

        form = FantasyTeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, "Team successfully updated")
            if not request.headers.get("HX-Request"):
                return redirect(reverse("teams"))
            else:
                response = HttpResponse(headers={"HX-Redirect": reverse("teams")})
                return response
        else:
            messages.warning(request, "Missing team information")
            return self.render_to_response(dict(form=form))


class TeamRowView(TemplateView):
    template_name = "fantasyteams/_row.html"

    def get(self, request, *args, **kwargs):
        if not kwargs.get("id"):
            raise Http404()
        try:
            team = FantasyTeam.objects.get(pk=kwargs.get("id"))
        except FantasyTeam.DoesNotExist:
            raise Http404()
        return self.render_to_response(dict(team=team))
