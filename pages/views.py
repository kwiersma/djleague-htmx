from datetime import datetime

import pusher
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import QuerySet
from django.http import Http404, HttpResponse, QueryDict
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic
from django.views.generic import TemplateView

from djleague.models import FantasyTeam, Player
from pages.forms import FantasyTeamForm, FantasyTeamInlineForm, PlayersFilter, DraftPlayerForm


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
        else:
            form = FantasyTeamInlineForm(request.POST, instance=team)

        if form.is_valid():
            form.save()
            messages.success(request, "Team successfully updated")
            if not request.headers.get("HX-Request"):
                return redirect(reverse("teams"))
            else:
                self.template_name = "fantasyteams/_row.html"
                return self.render_to_response(dict(team=form.instance, include_messages=True))
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

    def _build_team_players_context(self, context: dict | None = None) -> dict:
        if not context:
            context = dict()
        context["teams"] = FantasyTeam.objects.order_by("draft_order")
        current_team_id = self.request.GET.get("fantasyteam")
        if not current_team_id:
            current_team_id = context["teams"][0].id
        else:
            current_team_id = int(current_team_id)
        context["current_team_id"] = current_team_id
        context["team_players"] = (
            Player.objects.filter(fantasyteam_id=current_team_id)
            .select_related("team")
            .order_by("round", "pick")
        )
        return context

    def _build_last_picks_context(self, context: dict | None = None) -> dict:
        picks = Player.objects.fetch_last_picks()
        if not context:
            context = dict()
        context["current_pick"] = picks[0]
        context["last_pick"] = picks[2] if len(picks) > 2 else dict()
        context["on_deck"] = picks[1] if len(picks) > 1 else dict()
        context["before_last_pick"] = picks[3] if len(picks) > 3 else dict()
        return context


class DraftView(DraftBaseView):
    template_name = "draft/draft.html"

    def get(self, request, *args, **kwargs):
        context = self._build_search_context()

        if request.headers.get("HX-Request"):
            self.template_name = "draft/_players.html"
        else:
            context = self._build_team_players_context(context)
            context = self._build_last_picks_context(context)

        context["PUSHER_KEY"] = settings.PUSHER_KEY
        context["PUSHER_CLUSER"] = settings.PUSHER_CLUSTER
        return self.render_to_response(context)


class TeamPlayersView(DraftBaseView):
    template_name = "draft/_team-players.html"

    def get(self, request, *args, **kwargs):
        context = self._build_team_players_context()
        return self.render_to_response(context)


class DraftPlayerView(TemplateView):
    template_name = "draft/_draft-player.html"

    def get(self, request, *args, **kwargs):
        context = self._build_context(kwargs)
        initial = dict(fantasyteam=context["current_fantasyteam_id"])

        form = DraftPlayerForm(initial, instance=context["player"])
        context["form"] = form

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        context = self._build_context(kwargs)

        form = DraftPlayerForm(request.POST, instance=context["player"])
        context["form"] = form
        if form.is_valid():
            player = form.instance
            player.round = context["round"]
            player.pick = context["pick"]
            player.picktime = datetime.now()
            player.save()

            if settings.PUSHER_KEY:
                p = pusher.Pusher(
                    app_id=settings.PUSHER_APP_ID,
                    key=settings.PUSHER_KEY,
                    secret=settings.PUSHER_SECRET,
                    cluster=settings.PUSHER_CLUSTER,
                )
                p.trigger("draftedPlayers", "playerDrafted", Player.objects.fetch_last_picks())

            return HttpResponse(headers={"HX-Trigger": "player-drafted"})
        else:
            return self.render_to_response(context)

    def _build_context(self, kwargs) -> dict:
        if not kwargs.get("id"):
            raise Http404()
        try:
            player = Player.objects.get(pk=kwargs.get("id"))
        except Player.DoesNotExist:
            raise Http404()
        picks = Player.objects.fetch_last_picks()
        round = picks[0]["round"]
        pick = picks[0]["pick"]
        context = dict(
            pick=pick, player=player, round=round, current_fantasyteam_id=picks[0]["fantasyteam_id"]
        )
        return context


class LastPicksView(DraftBaseView):
    template_name = "draft/_last_picks.html"

    def get(self, request, *args, **kwargs):
        context = self._build_last_picks_context()
        return self.render_to_response(context)


class PickRow:
    def __init__(self):
        self.row_type = ""
        self.name = ""
        self.round_pick = 0
        self.pick_no = 0
        self.item_class = ""
        self.label_class = ""


class UpcomingPicksView(DraftBaseView):
    template_name = "draft/_upcoming_picks.html"

    def get(self, request, *args, **kwargs):
        teams = FantasyTeam.objects.order_by("draft_order")
        picks = Player.objects.fetch_last_picks()
        rows = self._setup_pick_rows(teams, picks)

        for idx, row in enumerate(rows):
            itemClass = ""
            labelClass = "primary"
            if row.row_type != "round":
                if idx == 1:
                    itemClass = "danger"
                    labelClass = "danger"
                elif idx == 2:
                    itemClass = "warning"
                    labelClass = "warning"
            row.item_class = itemClass
            row.label_class = labelClass

        context = dict(teams=teams, rows=rows)
        return self.render_to_response(context)

    def _setup_pick_rows(self, teams: QuerySet[FantasyTeam], picks: list[dict]) -> list[PickRow]:
        current_round = 0
        current_pick = 1

        if picks and len(picks) > 0:
            current_round = picks[0].get("round")
            current_pick = picks[0].get("pick")

        pick_rows = []

        if teams is None:
            teams = []

        if len(teams) > 0 and current_round > 0:
            pick_rows = self._generate_rows_by_round(current_round, current_pick, teams, pick_rows)
            if len(pick_rows) < 13:
                pick_rows = self._generate_rows_by_round(current_round + 1, 1, teams, pick_rows)

        return pick_rows

    def _generate_rows_by_round(
        self, start_round: int, start_round_pick: int, teams: QuerySet[FantasyTeam], pick_rows: list[PickRow]
    ) -> list[PickRow]:
        is_odd_round = start_round % 2 == 1 or start_round == 0

        pick_row = PickRow()
        pick_row.row_type = "round"
        pick_row.name = "Round " + str(start_round)
        pick_rows.append(pick_row)

        i = 0
        if is_odd_round:
            i = start_round_pick - 1
        else:
            i = len(teams) - start_round_pick

        picks_added = 1
        while i < len(teams) and i >= 0 and len(pick_rows) < 13:
            team = teams[i]
            pick_row = PickRow()
            pick_row.row_type = "team"
            pick_row.name = team.name + " (" + team.owner + ")"
            pick_row.round_pick = start_round_pick + picks_added
            # Round 0 is keepers which don't have a pick no
            pick_row.pick_no = (start_round - 1) * 10 + (pick_row.round_pick - 1)
            pick_rows.append(pick_row)
            picks_added += 1

            if is_odd_round:
                i += 1
            else:
                i -= 1

        return pick_rows
