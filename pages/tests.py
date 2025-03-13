from http import HTTPStatus

from django.urls import reverse

from djleague import factories
from djleague.models import FantasyTeam
from djleague.tests import BaseTestCase


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
        resp = self.client.post(self.url, data={"position": "QB"})

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        found_players = resp.context_data["players"].object_list
        self.assertEqual(len(found_players), 1)
        self.assertIn(self.player, found_players)


class TestDraftSearchView(BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.player = factories.Player()
        cls.url = reverse("draft")

    def test_htmx_view(self):
        # Act
        resp = self.client.post(self.url)

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(resp, "draft/_players.html")
        self.assertIn(self.player, resp.context_data["players"].object_list)

    def test_position_filter(self):
        # Arrange
        self.player.position = "QB"
        self.player.save()
        factories.Player(position="RB")

        # Act
        resp = self.client.post(self.url, data={"position": "QB"})

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        found_players = resp.context_data["players"].object_list
        self.assertEqual(len(found_players), 1)
        self.assertIn(self.player, found_players)
