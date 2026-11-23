from django.test import SimpleTestCase
from django.urls import reverse


class LivenessViewTests(SimpleTestCase):
    def test_liveness_returns_standard_envelope(self) -> None:
        response = self.client.get(reverse("core:liveness"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["status"], "ok")
