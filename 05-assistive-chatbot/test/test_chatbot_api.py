import json
import unittest
from chatbot_api import app
from fastapi.testclient import TestClient


# logger = logging.getLogger(f"chatbot.chatbot_api")

client = TestClient(app)


class TestAPI(unittest.TestCase):
    def test_read_healthcheck(self):
        with self.assertLogs("chatbot.chatbot_api", level="INFO") as cm:
            response = client.get("/healthcheck")
            response_data = json.loads(response.content)
            assert response.status_code == 200
            assert response_data["status"] == "OK"
            self.assertIn("Healthy", cm.output[1])
