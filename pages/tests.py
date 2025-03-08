from http import HTTPStatus

from django.urls import reverse

from djleague import factories
from djleague.tests import BaseTestCase


class TestHome(BaseTestCase):

    def test_home(self):
        # Arrange

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
