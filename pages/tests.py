from http import HTTPStatus

from django.urls import reverse

from accounts.models import CustomUser
from accounts.tests import BaseTestCase


class TestHome(BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        email = "test@test.com"
        cls.user = CustomUser.objects.create_user(email=email, password="funfun", username=email)

    def test_logged_in(self):
        # Arrange
        self.simulate_login(self.user)

        # Act
        resp = self.client.get(reverse("home"))

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertIn(self.user.email, resp.rendered_content)

    def test_not_logged_in(self):
        # Act
        resp = self.client.get(reverse("home"))

        # Assert
        self.assertEqual(resp.status_code, HTTPStatus.OK)
        self.assertNotIn(self.user.email, resp.rendered_content)
        self.assertIn(reverse("account_login"), resp.rendered_content)
