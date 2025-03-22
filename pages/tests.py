from datetime import datetime
from http import HTTPStatus

from django.urls import reverse

from djleague import factories
from djleague.models import FantasyTeam, Player
from djleague.tests import BaseTestCase
from pages.views import PickRow


class TestHome(BaseTestCase):

    def test_home(self):
        # Act
        resp = self.client.get(reverse("home"))

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)


class TestTeamsView(BaseTestCase):

    def test_list(self):
        # Arrange
        factories.FantasyTeamFactory()

        # Act
        resp = self.client.get(reverse("teams"))

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(len(resp.context_data.get("teams")), 1)


class TestTeamRowView(BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.team = factories.FantasyTeamFactory()
        cls.url = reverse("team_row", kwargs=dict(id=cls.team.id))

    def test_view(self):
        # Act
        resp = self.client.get(self.url)

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(resp, "fantasyteams/_row.html")
        self.assertContains(resp, self.team.name)

    def test_not_found(self):
        resp = self.client.get(reverse("team_row", kwargs=dict(id=9999)))
        self.assertEqual(resp.status_code, HTTPStatus.NOT_FOUND)


class TestTeamEditView(BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.team = factories.FantasyTeamFactory()
        cls.url = reverse("team_edit", kwargs=dict(id=cls.team.id))

    def test_happy_htmx(self):
        # Act
        resp = self.client.get(self.url, headers={"HX-Request": "true"})

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(resp, "fantasyteams/_edit.html")
        form = resp.context_data["form"]
        self.assertEqual(form.instance, self.team)

        # Arrange
        data = dict(name="Test Team", owner="Test Owner", draft_order=1)

        # Act - post form
        resp = self.client.post(self.url, headers={"HX-Request": "true"}, data=data)

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(resp.headers["HX-Redirect"], reverse("teams"))

    def test_happy(self):
        # Act
        resp = self.client.get(self.url)

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(resp, "fantasyteams/edit.html")
        form = resp.context_data["form"]
        self.assertEqual(form.instance, self.team)

        # Arrange
        data = dict(name="Test Team", owner="Test Owner", draft_order=1)

        # Act - post form
        resp = self.client.post(self.url, data=data, follow=True)

        # Assert
        self.assertRedirects(resp, reverse("teams"))
        message = list(resp.context.get("messages"))[0]
        self.assertEqual(message.tags, "success")
        self.assertIn("Team successfully updated", message.message)

        team = FantasyTeam.objects.get(pk=self.team.id)
        self.assertEqual(team.name, data["name"])
        self.assertEqual(team.owner, data["owner"])
        self.assertEqual(team.draft_order, data["draft_order"])

    def test_invalid_form(self):
        # Arrange
        data = dict(name="", owner="Test Owner", draft_order=1)

        # Act - post form
        resp = self.client.post(self.url, data=data)

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        message = list(resp.context.get("messages"))[0]
        self.assertEqual(message.tags, "warning")
        self.assertIn("Missing team information", message.message)


class TestDraftView(BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.player = factories.Player()
        cls.team = factories.FantasyTeamFactory()
        cls.url = reverse("draft")

    def test_view(self):
        # Act
        resp = self.client.get(self.url)

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(resp, "draft/draft.html")
        self.assertIn(self.player, resp.context_data["players"].object_list)
        self.assertIn(self.team, resp.context_data["teams"])

    def test_filter_position(self):
        # Arrange
        self.player.position = "QB"
        self.player.save()
        factories.Player(position="RB")

        # Act
        resp = self.client.get(self.url, data={"position": "QB"})

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        found_players = resp.context_data["players"].object_list
        self.assertEqual(len(found_players), 1)
        self.assertIn(self.player, found_players)

    def test_htmx_view(self):
        # Act
        resp = self.client.get(self.url, headers={"HX-Request": "true"})

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(resp.template_name, ["draft/_players.html"])
        self.assertIn(self.player, resp.context_data["players"].object_list)

    def test_htmx_position_filter(self):
        # Arrange
        self.player.position = "QB"
        self.player.save()
        factories.Player(position="RB")

        # Act
        resp = self.client.get(self.url, data={"position": "QB"}, headers={"HX-Request": "true"})

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(resp.template_name, ["draft/_players.html"])
        found_players = resp.context_data["players"].object_list
        self.assertEqual(len(found_players), 1)
        self.assertIn(self.player, found_players)


class TestTeamPlayersView(BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.team = factories.FantasyTeamFactory(draft_order=1)
        cls.player = factories.Player(fantasyteam=cls.team, round=1, pick=1)
        cls.url = reverse("team_players")

    def test_htmx_view(self):
        # Act
        resp = self.client.get(self.url, data=dict(fantasyteam=self.team.id))

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(resp.template_name, ["draft/_team-players.html"])
        self.assertEqual(resp.context_data["current_team_id"], self.team.id)
        self.assertIn(self.player, resp.context_data["team_players"])

    def test_htmx_no_team_id(self):
        # Arrange
        extra_team = factories.FantasyTeamFactory(draft_order=2)

        # Act
        resp = self.client.get(self.url)

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(resp.template_name, ["draft/_team-players.html"])
        self.assertEqual(resp.context_data["current_team_id"], self.team.id)
        self.assertIn(self.player, resp.context_data["team_players"])


class TestDraftPlayerView(BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.team = factories.FantasyTeamFactory(draft_order=1)
        cls.player = factories.Player()
        cls.url = reverse("draft_player", kwargs=dict(id=cls.player.id))

    def test_htmx_view(self):
        # Act
        resp = self.client.get(self.url, headers={"HX-Request": "true"})

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(resp.template_name, ["draft/_draft-player.html"])
        self.assertEqual(resp.context_data["current_fantasyteam_id"], self.team.id)
        self.assertEqual(resp.context_data["player"].id, self.player.id)
        self.assertEqual(resp.context_data["round"], 1)
        self.assertEqual(resp.context_data["pick"], 1)

    def test_htmx_post(self):
        # Arrange
        data = dict(fantasyteam=self.team.id)

        # Act
        resp = self.client.post(self.url, data=data, headers={"HX-Request": "true"})

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(resp.headers.get("HX-Trigger"), "player-drafted")

        player = Player.objects.get(pk=self.player.id)
        self.assertEqual(player.fantasyteam, self.team)
        self.assertEqual(player.pick, 1)
        self.assertEqual(player.round, 1)


class TestLastPicksView(BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.team1 = factories.FantasyTeamFactory(draft_order=1)
        cls.team2 = factories.FantasyTeamFactory(draft_order=2)
        cls.team3 = factories.FantasyTeamFactory(draft_order=3)
        cls.url = reverse("last_picks")

    def test_no_picks(self):
        # Act
        resp = self.client.get(self.url, headers={"HX-Request": "true"})

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(resp.template_name, ["draft/_last_picks.html"])
        self.assertEqual(resp.context_data["current_pick"]["owner"], self.team1.owner)
        self.assertEqual(resp.context_data["current_pick"]["round"], 1)
        self.assertEqual(resp.context_data["current_pick"]["pick"], 1)
        self.assertEqual(resp.context_data["on_deck"]["owner"], "")

    def test_after_first_pick(self):
        # Arrange
        player = factories.Player(fantasyteam=self.team1, round=1, pick=1, picktime=datetime.now())

        # Act
        resp = self.client.get(self.url, headers={"HX-Request": "true"})

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(resp.template_name, ["draft/_last_picks.html"])
        self.assertEqual(resp.context_data["current_pick"]["owner"], self.team2.owner)
        self.assertEqual(resp.context_data["current_pick"]["round"], 1)
        self.assertEqual(resp.context_data["current_pick"]["pick"], 2)
        self.assertEqual(resp.context_data["last_pick"]["fantasyteam"], self.team1.name)
        self.assertEqual(resp.context_data["last_pick"]["owner"], self.team1.owner)
        self.assertEqual(resp.context_data["last_pick"]["round"], 1)
        self.assertEqual(resp.context_data["last_pick"]["pick"], 1)
        self.assertEqual(resp.context_data["on_deck"]["owner"], self.team3.owner)


class TestUpcomingPicksView(BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.team1 = factories.FantasyTeamFactory(draft_order=1)
        cls.team2 = factories.FantasyTeamFactory(draft_order=2)
        cls.team3 = factories.FantasyTeamFactory(draft_order=3)
        cls.url = reverse("upcoming_picks")

    def test_no_picks(self):
        # Act
        resp = self.client.get(self.url, headers={"HX-Request": "true"})

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertEqual(resp.template_name, ["draft/_upcoming_picks.html"])
        self.assertEqual(len(resp.context_data["rows"]), 8)

        row1: PickRow = resp.context_data["rows"][0]
        self.assertEqual(row1.row_type, "round")
        self.assertEqual(row1.name, "Round 1")

        row2: PickRow = resp.context_data["rows"][1]
        self.assertEqual(row2.row_type, "team")
        self.assertEqual(row2.name, f"{self.team1.name} ({self.team1.owner})")
        self.assertEqual(row2.item_class, "danger")
        self.assertEqual(row2.pick_no, 1)

        row3: PickRow = resp.context_data["rows"][2]
        self.assertEqual(row3.row_type, "team")
        self.assertEqual(row3.name, f"{self.team2.name} ({self.team2.owner})")
        self.assertEqual(row3.item_class, "warning")
        self.assertEqual(row3.pick_no, 2)

        row4: PickRow = resp.context_data["rows"][3]
        self.assertEqual(row4.row_type, "team")
        self.assertEqual(row4.name, f"{self.team3.name} ({self.team3.owner})")
        self.assertEqual(row4.item_class, "")
        self.assertEqual(row4.pick_no, 3)
