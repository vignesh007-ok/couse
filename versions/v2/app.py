from flask import Flask, jsonify, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

movies = []


@app.post("/add")
def add_movie():
    if not request.is_json:
        return jsonify(error="Content-Type must be application/json"), 415

    movie = request.get_json()
    if not isinstance(movie, dict):
        return jsonify(error="Request body must be a JSON object"), 400

    title = movie.get("title")
    director = movie.get("director")
    year = movie.get("year")
    if not isinstance(title, str) or not title.strip():
        return jsonify(error="title must be a non-empty string"), 400
    if not isinstance(director, str) or not director.strip():
        return jsonify(error="director must be a non-empty string"), 400
    if isinstance(year, bool) or not isinstance(year, int) or not 1888 <= year <= 2200:
        return jsonify(error="year must be an integer between 1888 and 2200"), 400

    saved_movie = {
        "title": title.strip(),
        "director": director.strip(),
        "year": year,
    }
    movies.append(saved_movie)
    return jsonify(saved_movie), 201


@app.get("/movies")
def get_movies():
    return jsonify(movies)


@app.get("/healthz")
def healthz():
    return jsonify(status="ok", version="v2")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
