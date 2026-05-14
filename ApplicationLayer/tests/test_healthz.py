import app as application


class TestHealthz:
    def setup_method(self):
        application.app.config["TESTING"] = True
        self.client = application.app.test_client()

    def test_healthz_returns_200(self):
        response = self.client.get("/healthz")
        assert response.status_code == 200

    def test_healthz_returns_json_status_ok(self):
        response = self.client.get("/healthz")
        data = response.get_json()
        assert data == {"status": "ok"}

    def test_healthz_content_type_is_json(self):
        response = self.client.get("/healthz")
        assert response.content_type == "application/json"

    def test_healthz_has_cors_header(self):
        response = self.client.get("/healthz")
        assert response.headers.get("Access-Control-Allow-Origin") == "*"
