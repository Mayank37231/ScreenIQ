from django.contrib.auth.models import User
from django.test import override_settings
from rest_framework.test import APIClient, APITestCase

from .ai import normalize_score
from .models import Application


class ScoreNormalizationTests(APITestCase):
    def test_normalizes_decimal_and_word_scores(self):
        self.assertEqual(str(normalize_score("7.3")), "7.3")
        self.assertEqual(str(normalize_score("Seven")), "7.0")


class ApplicationApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="hr", password="pass")
        self.other_user = User.objects.create_user(username="other", password="pass")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    @override_settings(AI_PROVIDER="mock")
    def test_screen_candidate_creates_application_for_current_user(self):
        response = self.client.post(
            "/api/screen/",
            {
                "job_description": "Python Django developer",
                "resume": "Ada Lovelace\nPython and Django experience",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Application.objects.get().created_by, self.user)
        self.assertEqual(response.data["candidate_name"], "Ada Lovelace")

    def test_application_list_only_returns_current_users_rows(self):
        Application.objects.create(
            job_description="Backend",
            resume="Current User",
            candidate_name="Current User",
            ai_score="8.0",
            ai_reasons=["a", "b", "c"],
            created_by=self.user,
        )
        Application.objects.create(
            job_description="Backend",
            resume="Other User",
            candidate_name="Other User",
            ai_score="4.0",
            ai_reasons=["a", "b", "c"],
            created_by=self.other_user,
        )

        response = self.client.get("/api/applications/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["candidate_name"], "Current User")

    def test_screen_candidate_rejects_missing_fields(self):
        response = self.client.post("/api/screen/", {"resume": "No job"}, format="json")

        self.assertEqual(response.status_code, 400)
