pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    parameters {
        choice(name: 'VERSION', choices: ['v1', 'v2', 'v3'], description: 'Application version to build and deploy')
    }

    environment {
        DOCKERHUB_NAMESPACE = 'vigneshvicky1852007'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build image') {
            steps {
                sh '''
                    set -eu
                    docker build \
                      --file "versions/${VERSION}/Dockerfile" \
                      --tag "movie-app:$VERSION" \
                      .
                '''
            }
        }

        stage('Push image') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DOCKERHUB_USER',
                        passwordVariable: 'DOCKERHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set -eu
                        REMOTE_IMAGE="docker.io/${DOCKERHUB_NAMESPACE}/movie-app:${VERSION}"
                        printf '%s' "$DOCKERHUB_TOKEN" |
                          docker login --username "$DOCKERHUB_USER" --password-stdin
                        docker tag "movie-app:$VERSION" "$REMOTE_IMAGE"
                        docker push "$REMOTE_IMAGE"
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh '''
                        set -eu
                        REMOTE_IMAGE="docker.io/${DOCKERHUB_NAMESPACE}/movie-app:${VERSION}"
                        kubectl apply -f "k8s/deployment-${VERSION}.yaml"
                        kubectl apply -f "k8s/service-${VERSION}.yaml"
                        kubectl set image \
                          "deployment/movie-app-${VERSION}" \
                          "movie-app=${REMOTE_IMAGE}"
                        kubectl rollout status \
                          "deployment/movie-app-${VERSION}" \
                          --timeout=120s
                    '''
                }
            }
        }
    }

    post {
        always {
            sh 'docker logout || true'
        }
    }
}
