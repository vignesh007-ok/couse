# Movie List Application — VIGNESH.E (24MIS0559)

College DevOps course project using Flask, SQLite, HTML, CSS, and JavaScript.

## Completed milestones: V1 and V2

V1 is implemented as a responsive movie shelf with add, view, and delete functionality. Each movie stores a title, genre, release year, and description in SQLite.

V2 retains the V1 functionality and adds a case-insensitive search over movie titles/descriptions and a genre filter. Both filters can be combined.

V3 (sorting and statistics), Jenkins, Docker Hub publishing, and Kubernetes deployment are subsequent project milestones. The existing V2 Dockerfile has a pre-existing, uncommitted local edit and has deliberately not been changed during this application-code milestone.

## V1 files

```text
versions/v1/
├── app.py
├── Dockerfile
├── static/
│   ├── app.js
│   └── style.css
└── templates/
    └── index.html
versions/v2/
├── app.py
├── templates/
│   └── index.html
└── static/
    ├── app.js
    └── style.css
tests/
└── test_app_versions.py
```

The default local database is created at `versions/v1/instance/movies.sqlite3`. Set `DATABASE` to choose another file. SQLite data files are excluded from Git.

## Run a version locally in VS Code

From the project root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PORT = "5002"
python versions\v2\app.py
```

Open http://127.0.0.1:5002/ to try V2. To launch V1 in a separate terminal, use:

```powershell
$env:PORT = "5001"
python versions\v1\app.py
```

Keep each terminal open and browse to:

- V1 app: http://127.0.0.1:5001/
- V1 health check: http://127.0.0.1:5001/healthz
- V2 app: http://127.0.0.1:5002/
- V2 health check: http://127.0.0.1:5002/healthz

Each version uses its own SQLite database by default. To use a non-default database path, set `$env:DATABASE` before starting Flask.

## Test V1

From the project root:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q versions\v1 versions\v2 tests
```

The automated tests cover V1 rendering, validation, SQLite persistence, deletion, and escaping; V2 regression tests additionally cover title/description search, literal wildcard handling, case-insensitive genre filtering, combined filters, and empty results.

## Planned DevOps sequence

After confirming this V2 milestone, the remaining work will proceed in order:

1. Implement V3 sorting, statistics, and responsive improvements; test it and wait for confirmation.
2. Create and push the separate GitHub version branches/commits using the repository and account details you choose.
3. Configure Jenkins stages for checkout, build, test, and Docker image build.
4. Build and tag Docker images `v1`, `v2`, and `v3`; authenticate to Docker Hub interactively or through Jenkins credentials.
5. Push the images and deploy three Kubernetes Deployments and NodePort Services, then verify localhost access.

Never put GitHub or Docker Hub passwords/tokens in source files, command history, or this README. Use an interactive login or Jenkins credentials.
