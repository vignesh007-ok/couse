import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_MOVIE = {"title": "Arrival", "director": "Denis Villeneuve", "year": 2016}


def load_app(version):
    module_path = ROOT / "versions" / version / "app.py"
    spec = importlib.util.spec_from_file_location(f"movie_app_{version}", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.app.config.update(TESTING=True)
    return module


class MovieAppVersionTests(unittest.TestCase):
    def test_v1_adds_movies_and_has_no_list_endpoint(self):
        module = load_app("v1")
        client = module.app.test_client()

        response = client.post("/add", json=SAMPLE_MOVIE)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json, SAMPLE_MOVIE)
        self.assertEqual(module.movies, [SAMPLE_MOVIE])
        self.assertEqual(client.get("/movies").status_code, 404)

    def test_v2_adds_and_lists_movies(self):
        module = load_app("v2")
        client = module.app.test_client()

        response = client.post("/add", json=SAMPLE_MOVIE)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(client.get("/movies").json, [SAMPLE_MOVIE])
        self.assertEqual(client.delete("/delete/Arrival").status_code, 404)

    def test_v3_adds_lists_and_deletes_movies(self):
        module = load_app("v3")
        client = module.app.test_client()

        self.assertEqual(client.post("/add", json=SAMPLE_MOVIE).status_code, 201)
        self.assertEqual(client.get("/movies").json, [SAMPLE_MOVIE])
        response = client.delete("/delete/Arrival")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["deleted"], SAMPLE_MOVIE)
        self.assertEqual(client.get("/movies").json, [])
        self.assertEqual(client.delete("/delete/Arrival").status_code, 404)

    def test_add_validates_required_fields(self):
        module = load_app("v3")
        client = module.app.test_client()

        self.assertEqual(client.post("/add", json={"title": "Arrival"}).status_code, 400)
        self.assertEqual(client.post("/add", json={**SAMPLE_MOVIE, "year": True}).status_code, 400)
        self.assertEqual(client.post("/add", json={**SAMPLE_MOVIE, "year": 1887}).status_code, 400)
        self.assertEqual(client.post("/add", data="not json").status_code, 415)
        self.assertEqual(module.movies, [])

    def test_health_endpoint_reports_each_version(self):
        for version in ("v1", "v2", "v3"):
            with self.subTest(version=version):
                client = load_app(version).app.test_client()
                response = client.get("/healthz")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json["version"], version)


if __name__ == "__main__":
    unittest.main()
