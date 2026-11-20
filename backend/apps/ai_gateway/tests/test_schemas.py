from django.test import SimpleTestCase

from apps.ai_gateway.schemas import ChatPayloadError, ChatRequest


class ChatRequestTests(SimpleTestCase):
    def test_parses_valid_messages(self) -> None:
        request = ChatRequest.from_payload(
            {"messages": [{"role": "user", "content": "  生成周报  "}]}
        )

        self.assertEqual(len(request.messages), 1)
        self.assertEqual(request.messages[0].content, "生成周报")

    def test_parses_attachment_ids(self) -> None:
        request = ChatRequest.from_payload(
            {"messages": [{"role": "user", "content": "整理附件", "attachment_ids": ["123"]}]}
        )
        self.assertEqual(request.messages[0].attachment_ids, ("123",))

    def test_rejects_too_many_attachments(self) -> None:
        with self.assertRaises(ChatPayloadError):
            ChatRequest.from_payload(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": "整理",
                            "attachment_ids": ["1", "2", "3", "4", "5"],
                        }
                    ]
                }
            )

    def test_rejects_empty_messages(self) -> None:
        with self.assertRaises(ChatPayloadError):
            ChatRequest.from_payload({"messages": []})
