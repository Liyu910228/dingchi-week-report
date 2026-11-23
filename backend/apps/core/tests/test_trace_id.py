import re

from django.test import SimpleTestCase
from django.urls import reverse


class TraceIdMiddlewareTests(SimpleTestCase):
    def test_request_gets_generated_trace_id_in_response(self) -> None:
        response = self.client.get(reverse("core:liveness"))

        self.assertEqual(response.status_code, 200)
        self.assertRegex(response["X-Trace-ID"], re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"))

    def test_valid_incoming_trace_id_is_preserved(self) -> None:
        response = self.client.get(reverse("core:liveness"), HTTP_X_TRACE_ID="local-trace-001")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Trace-ID"], "local-trace-001")
