from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import Http404, HttpResponse, QueryDict
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic
from django.views.generic import TemplateView

from djleague.models import FantasyTeam, Player
from pages.forms import FantasyTeamForm, FantasyTeamInlineForm, PlayersFilter


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


class DraftBaseView(TemplateView):

    def _build_search_context(self) -> dict:
        initial = QueryDict("", mutable=True)
        initial.update(self.request.GET)
        if not initial.get("sort"):
            initial["sort"] = "rank"
        f = PlayersFilter(initial, queryset=Player.objects.select_related("team", "fantasyteam"))
        paginator = Paginator(f.qs, 10)
        page = self.request.GET.get("page", 1)
        try:
            paged_players = paginator.page(page)
        except PageNotAnInteger:
            paged_players = paginator.page(1)
            page = 1
        except EmptyPage:
            paged_players = paginator.page(paginator.num_pages)
        page = int(page)
        pagination = dict()
        pagination["has_other_pages"] = paginator.num_pages > 1
        pagination["previous_page_number"] = page - 1
        pagination["has_previous"] = page > 1
        pagination["has_next"] = page < paginator.num_pages
        pagination["next_page_number"] = page + 1
        pagination["start_count"] = (paged_players.paginator.per_page * page) - 9
        pagination["through_count"] = paged_players.paginator.per_page * page

        context = dict(players=paged_players, pagination=pagination, filter=f)

        return context


class DraftView(DraftBaseView):
    template_name = "draft/draft.html"

    def get(self, request, *args, **kwargs):
        context = self._build_search_context()
        context["teams"] = FantasyTeam.objects.order_by("draft_order")

        if request.headers.get("HX-Request"):
            self.template_name = "draft/_players.html"

        return self.render_to_response(context)
