import os
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, url_for


def create_app(test_config=None):
    app = Flask(
        __name__,
        root_path=str(Path(__file__).resolve().parent),
        template_folder="templates",
        static_folder="static",
    )
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "local-development-key"),
        DATABASE=os.environ.get(
            "DATABASE",
            str(Path(app.root_path) / "instance" / "movies.sqlite3"),
        ),
    )
    if test_config:
        app.config.update(test_config)

    database_path = Path(app.config["DATABASE"])
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 120),
                genre TEXT NOT NULL CHECK(length(genre) BETWEEN 1 AND 60),
                release_year INTEGER NOT NULL CHECK(release_year BETWEEN 1888 AND 2200),
                description TEXT NOT NULL CHECK(length(description) BETWEEN 1 AND 1000),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()

    def connect_db():
        connection = sqlite3.connect(app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        return connection

    @app.get("/")
    def index():
        with closing(connect_db()) as connection:
            movies = connection.execute(
                """
                SELECT id, title, genre, release_year, description
                FROM movies
                ORDER BY id DESC
                """
            ).fetchall()
        return render_template("index.html", movies=movies, version="V1")

    @app.post("/movies")
    def add_movie():
        title = request.form.get("title", "").strip()
        genre = request.form.get("genre", "").strip()
        description = request.form.get("description", "").strip()
        year_text = request.form.get("release_year", "").strip()

        errors = []
        if not title or len(title) > 120:
            errors.append("Enter a movie title (up to 120 characters).")
        if not genre or len(genre) > 60:
            errors.append("Enter a genre (up to 60 characters).")
        if not description or len(description) > 1000:
            errors.append("Enter a description (up to 1000 characters).")
        try:
            release_year = int(year_text)
            if not 1888 <= release_year <= 2200:
                errors.append("Release year must be between 1888 and 2200.")
        except ValueError:
            release_year = None
            errors.append("Enter a valid release year.")

        if errors:
            for error in errors:
                flash(error, "error")
            with closing(connect_db()) as connection:
                movies = connection.execute(
                    """
                    SELECT id, title, genre, release_year, description
                    FROM movies
                    ORDER BY id DESC
                    """
                ).fetchall()
            return render_template("index.html", movies=movies, version="V1"), 400

        with closing(connect_db()) as connection:
            connection.execute(
                """
                INSERT INTO movies (title, genre, release_year, description)
                VALUES (?, ?, ?, ?)
                """,
                (title, genre, release_year, description),
            )
            connection.commit()

        flash(f"“{title}” added to your collection.", "success")
        return redirect(url_for("index"), code=303)

    @app.post("/movies/<int:movie_id>/delete")
    def delete_movie(movie_id):
        with closing(connect_db()) as connection:
            cursor = connection.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
            connection.commit()
        if cursor.rowcount == 0:
            abort(404)
        flash("Movie removed from your collection.", "success")
        return redirect(url_for("index"), code=303)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok", "version": "v1"}

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )
