# Movie List API: v1, v2, and v3

This repository contains three Flask API versions. Each version has a separate Alpine-based Dockerfile and Kubernetes Deployment/Service. Movies are stored in process memory, so they disappear on restart and do not replicate between pods. These examples are for local learning, not production data storage.

## 1. Workspace structure

```text
movie-list-app/
├── .gitignore
├── Jenkinsfile
├── README.md
├── requirements.txt
├── k8s/
│   ├── deployment-v1.yaml
│   ├── deployment-v2.yaml
│   ├── deployment-v3.yaml
│   ├── service-v1.yaml
│   ├── service-v2.yaml
│   └── service-v3.yaml
├── tests/
│   └── test_app_versions.py
└── versions/
    ├── v1/
    │   ├── Dockerfile
    │   └── app.py
    ├── v2/
    │   ├── Dockerfile
    │   └── app.py
    └── v3/
        ├── Dockerfile
        └── app.py
```

## 2. Run and test locally

Run these commands from the project root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Run a specific version on port 5000 in its own terminal:

```powershell
python versions\v1\app.py
python versions\v2\app.py
python versions\v3\app.py
```

Stop one version with Ctrl+C before starting another on that same port.

## 3. GitHub commits and branches

Create an empty GitHub repository named `movie-app` under the account you control before pushing. The example remote below follows the requested Docker Hub namespace as the presumed GitHub owner; confirm that this GitHub repository exists and that you have access. GitHub authentication should use Git Credential Manager/browser sign-in or a newly created PAT entered only at the secure prompt. Never put a PAT or password in a remote URL, command, file, or Jenkinsfile.

Git commit email becomes part of public commit metadata. Configure it only if you intend it to appear in commits:

```powershell
git init -b v1
git config user.name "Vignesh"
git config user.email "vignesh.e2024@vitstudentac.in"
git add .gitignore Jenkinsfile README.md requirements.txt tests
git add versions\v1 k8s\deployment-v1.yaml k8s\service-v1.yaml
git commit -m "Add movie API v1"
git remote add origin https://github.com/vigneshvicky1852007/movie-app.git
git push -u origin v1

git switch -c v2
git add versions\v2 k8s\deployment-v2.yaml k8s\service-v2.yaml
git commit -m "Add movie API v2 movie listing"
git push -u origin v2

git switch -c v3
git add versions\v3 k8s\deployment-v3.yaml k8s\service-v3.yaml
git commit -m "Add movie API v3 deletion"
git push -u origin v3
```

Each later branch descends from the previous version, so `v2` contains v1 and v2, while `v3` contains all three. Check the history with `git log --oneline --decorate --all`.

## 4. Docker build and push

Docker Hub authentication is interactive. Use a Docker Hub access token at the password prompt; do not type it into a command or save it in source control.

```powershell
docker login --username vigneshvicky1852007

docker build --file versions\v1\Dockerfile --tag vigneshvicky1852007/movie-app:v1 .
docker push vigneshvicky1852007/movie-app:v1

docker build --file versions\v2\Dockerfile --tag vigneshvicky1852007/movie-app:v2 .
docker push vigneshvicky1852007/movie-app:v2

docker build --file versions\v3\Dockerfile --tag vigneshvicky1852007/movie-app:v3 .
docker push vigneshvicky1852007/movie-app:v3

docker image ls vigneshvicky1852007/movie-app
```

## 5. Jenkins setup and pipeline

The root `Jenkinsfile` is parameterized. Create a Jenkins **Multibranch Pipeline** job for the GitHub repository and enable branches `v1`, `v2`, and `v3`. Each run must select the `VERSION` that matches its branch, because earlier branches do not yet contain later versions.

Add these Jenkins credentials (Manage Jenkins → Credentials):

1. ID `dockerhub-creds`, kind **Username with password**. Username is the Docker Hub username; password is a Docker Hub access token.
2. ID `kubeconfig`, kind **Secret file**. Upload a kubeconfig usable by the Jenkins agent. The Kubernetes API address in it must be reachable from that agent.

The Jenkins agent needs Git, Docker CLI and daemon access, `kubectl`, and a POSIX shell. Jenkins uses the credential binding plugin. The pipeline builds the selected Dockerfile, pushes `docker.io/vigneshvicky1852007/movie-app:<version>`, applies that version's Kubernetes manifests, and waits for the rollout. It never needs a password embedded in the Jenkinsfile.

Run the Jenkins job once for each matching branch/version:

```text
Branch v1, VERSION v1
Branch v2, VERSION v2
Branch v3, VERSION v3
```

## 6. Deploy directly to Kubernetes

The manifests already reference the requested Docker Hub images. Deploy all versions:

```powershell
kubectl apply -f k8s\deployment-v1.yaml
kubectl apply -f k8s\service-v1.yaml
kubectl apply -f k8s\deployment-v2.yaml
kubectl apply -f k8s\service-v2.yaml
kubectl apply -f k8s\deployment-v3.yaml
kubectl apply -f k8s\service-v3.yaml
kubectl rollout status deployment/movie-app-v1
kubectl rollout status deployment/movie-app-v2
kubectl rollout status deployment/movie-app-v3
kubectl get deployments,pods,services
```

NodePorts are `30001` (v1), `30002` (v2), and `30003` (v3). Whether those ports are reachable at localhost depends on the Kubernetes distribution and host networking configuration.

### Minikube or kind port-forward fallback

Run each command in its own terminal and leave the processes running:

```powershell
kubectl port-forward --address 127.0.0.1 service/movie-app-v1 5001:80
kubectl port-forward --address 127.0.0.1 service/movie-app-v2 5002:80
kubectl port-forward --address 127.0.0.1 service/movie-app-v3 5003:80
```

## 7. API and verification commands

### v1 — add a movie

```powershell
curl.exe -i http://localhost:5001/healthz
curl.exe -i -X POST http://localhost:5001/add -H "Content-Type: application/json" -d '{"title":"Arrival","director":"Denis Villeneuve","year":2016}'
```

### v2 — add and list movies

```powershell
curl.exe -i http://localhost:5002/healthz
curl.exe -i -X POST http://localhost:5002/add -H "Content-Type: application/json" -d '{"title":"Arrival","director":"Denis Villeneuve","year":2016}'
curl.exe -i http://localhost:5002/movies
```

### v3 — add, list, and delete movies

```powershell
curl.exe -i http://localhost:5003/healthz
curl.exe -i -X POST http://localhost:5003/add -H "Content-Type: application/json" -d '{"title":"Arrival","director":"Denis Villeneuve","year":2016}'
curl.exe -i http://localhost:5003/movies
curl.exe -i -X DELETE http://localhost:5003/delete/Arrival
curl.exe -i http://localhost:5003/movies
```

The v1, v2, and v3 applications are distinct processes with independent in-memory movie lists; adding a movie to one does not add it to the others.

### Cleanup

```powershell
kubectl delete -f k8s\service-v1.yaml -f k8s\deployment-v1.yaml
kubectl delete -f k8s\service-v2.yaml -f k8s\deployment-v2.yaml
kubectl delete -f k8s\service-v3.yaml -f k8s\deployment-v3.yaml
```
