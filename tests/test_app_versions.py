import importlib.util
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "versions" / "v1" / "app.py"
SPEC = importlib.util.spec_from_file_location("movie_app_v1", APP_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
V2_APP_PATH = ROOT / "versions" / "v2" / "app.py"
V2_SPEC = importlib.util.spec_from_file_location("movie_app_v2", V2_APP_PATH)
V2_MODULE = importlib.util.module_from_spec(V2_SPEC)
V2_SPEC.loader.exec_module(V2_MODULE)


class MovieAppV1Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "movies.sqlite3"
        self.app = MODULE.create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-key",
                "DATABASE": str(self.database),
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_sample_movie(self, **overrides):
        movie = {
            "title": "Spirited Away",
            "genre": "Animation",
            "release_year": "2001",
            "description": "A young girl enters a mysterious spirit world.",
        }
        movie.update(overrides)
        return self.client.post("/movies", data=movie, follow_redirects=True)

    def test_homepage_renders_student_project_and_empty_state(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"VIGNESH.E", response.data)
        self.assertIn(b"24MIS0559", response.data)
        self.assertIn(b"Your shelf is waiting.", response.data)

    def test_add_movie_persists_and_renders_all_fields(self):
        response = self.add_sample_movie()

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Spirited Away", response.data)
        self.assertIn(b"Animation", response.data)
        self.assertIn(b"2001", response.data)
        self.assertIn(b"A young girl enters a mysterious spirit world.", response.data)
        self.assertTrue(self.database.is_file())

    def test_movie_persists_between_app_instances(self):
        self.add_sample_movie()
        second_app = MODULE.create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-key",
                "DATABASE": str(self.database),
            }
        )

        response = second_app.test_client().get("/")

        self.assertIn(b"Spirited Away", response.data)

    def test_delete_removes_existing_movie(self):
        self.add_sample_movie()
        with closing(sqlite3.connect(self.database)) as connection:
            row = connection.execute("SELECT id FROM movies").fetchone()

        response = self.client.post(f"/movies/{row[0]}/delete", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Spirited Away", response.data)
        self.assertIn(b"Movie removed from your collection.", response.data)

    def test_delete_returns_404_for_missing_movie(self):
        response = self.client.post("/movies/999/delete")

        self.assertEqual(response.status_code, 404)

    def test_invalid_movie_is_rejected_without_database_insert(self):
        response = self.add_sample_movie(release_year="not-a-year")

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Enter a valid release year.", response.data)
        with closing(sqlite3.connect(self.database)) as connection:
            count = connection.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
        self.assertEqual(count, 0)

    def test_user_content_is_html_escaped(self):
        response = self.add_sample_movie(title="<script>alert(1)</script>")

        self.assertIn(b"&lt;script&gt;alert(1)&lt;/script&gt;", response.data)
        self.assertNotIn(b"<script>alert(1)</script>", response.data)

    def test_health_endpoint_reports_v1(self):
        response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok", "version": "v1"})


class MovieAppV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "movies.sqlite3"
        self.app = V2_MODULE.create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-key",
                "DATABASE": str(self.database),
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_movie(self, title, genre, description):
        return self.client.post(
            "/movies",
            data={
                "title": title,
                "genre": genre,
                "release_year": "2020",
                "description": description,
            },
            follow_redirects=True,
        )

    def test_v2_renders_search_and_genre_filter_controls(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Search titles or descriptions", response.data)
        self.assertIn(b"All genres", response.data)
        self.assertIn(b"V2", response.data)

    def test_search_matches_title_and_description_case_insensitively(self):
        self.add_movie("Moonrise Kingdom", "Comedy", "A young pair runs away together.")
        self.add_movie("Arrival", "Science Fiction", "A linguist makes first contact.")

        title_results = self.client.get("/?q=MOONRISE")
        description_results = self.client.get("/?q=linguist")

        self.assertIn(b"Moonrise Kingdom", title_results.data)
        self.assertNotIn(b"Arrival", title_results.data)
        self.assertIn(b"Arrival", description_results.data)
        self.assertNotIn(b"Moonrise Kingdom", description_results.data)

    def test_search_treats_wildcards_as_literal_characters(self):
        self.add_movie("100% Cinema", "Drama", "A literal percent in the title.")
        self.add_movie("Cinema", "Drama", "A regular title.")

        response = self.client.get("/?q=%25")

        self.assertIn(b"100% Cinema", response.data)
        self.assertNotIn(b"Regular title", response.data)

    def test_genre_filter_is_case_insensitive(self):
        self.add_movie("Moonrise Kingdom", "Comedy", "A young pair runs away together.")
        self.add_movie("Arrival", "Science Fiction", "A linguist makes first contact.")

        response = self.client.get("/?genre=cOmEdY")

        self.assertIn(b"Moonrise Kingdom", response.data)
        self.assertNotIn(b"Arrival", response.data)
        self.assertIn(b'value="Comedy" selected', response.data)

    def test_search_and_genre_filters_combine(self):
        self.add_movie("Moonrise Kingdom", "Comedy", "A young pair runs away together.")
        self.add_movie("The Grand Budapest Hotel", "Comedy", "A concierge cares for his hotel.")
        self.add_movie("Arrival", "Science Fiction", "A linguist meets an alien visitor.")

        response = self.client.get("/?q=hotel&genre=Comedy")

        self.assertIn(b"The Grand Budapest Hotel", response.data)
        self.assertNotIn(b"Moonrise Kingdom", response.data)
        self.assertNotIn(b"Arrival", response.data)

    def test_no_match_has_clear_filter_action(self):
        self.add_movie("Arrival", "Science Fiction", "A linguist makes first contact.")

        response = self.client.get("/?q=not-a-movie")

        self.assertIn(b"No films found.", response.data)
        self.assertIn(b"Clear filters", response.data)

    def test_add_and_delete_still_work_in_v2(self):
        response = self.add_movie("Arrival", "Science Fiction", "A linguist makes first contact.")
        self.assertIn(b"Arrival", response.data)
        with closing(sqlite3.connect(self.database)) as connection:
            row = connection.execute("SELECT id FROM movies").fetchone()

        response = self.client.post(f"/movies/{row[0]}/delete", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Arrival", response.data)

    def test_health_endpoint_reports_v2(self):
        response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok", "version": "v2"})


if __name__ == "__main__":
    unittest.main()
