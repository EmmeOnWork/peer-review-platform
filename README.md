# Peer Review Platform — Microservices & CI/CD on Kubernetes

Group project for the DevOps course of the M.Sc. in Computer Engineering at the
University of Salerno (team of three, June 2025).

Teachers publish assignments; students submit their work and review each
other's submissions. The platform is split into microservices and released
through a Jenkins pipeline onto a MicroK8s cluster.

## Architecture

| Component | Stack | Data store |
| --- | --- | --- |
| `Backend/Auth` | Python / Flask, JWT (RS256) | PostgreSQL |
| `Backend/Assignments` | Python / Flask | MongoDB |
| `Backend/Submissions` | Python / Flask | MongoDB + MinIO (files) |
| `Backend/Reviews` | Python / Flask | MongoDB |
| `Backend/Reports` | Python / Flask | none (reads the other services) |
| `Frontend` | Vue.js, served by NGINX | — |

Each service exposes an OpenAPI contract (`openapi.yaml`) and ships its own
Dockerfile, tests and Kubernetes manifests; no two services share a database. An NGINX Ingress
is the single entry point and routes by path (`/auth`, `/assignments`,
`/submissions`, `/reviews`, `/reports`, `/`).

Diagrams are in [`Documentation/Diagrams`](Documentation/Diagrams): components,
deployment, sequence diagrams and the CI/CD activity diagrams.

## CI/CD pipeline

The [`Jenkinsfile`](Jenkinsfile) is a small orchestrator: it picks a list of
steps from the branch name and loads each one from
[`OrchestrationPipeline/`](OrchestrationPipeline). The branching model is
GitFlow.

| Branch | Steps |
| --- | --- |
| feature branches | detect the changed services, validate their structure, build and test their Docker images, merge `develop` in, deploy to staging, run integration tests and security scans (Trivy, kube-hunter), push to `develop` |
| `develop` | deploy to pre-release, wait for manual approval, run smoke tests and load tests (Locust), merge to `master` |
| `master` | deploy to production, run smoke tests and load tests, roll back with `kubectl rollout undo` if they fail, regenerate the package diagram |

Only the services touched by a commit are rebuilt. Manifests are kept per
environment under each service's `k8s/` folder and applied by Jenkins.

## Repository layout

```
Backend/                 one folder per microservice
Frontend/                Vue.js single-page app
Ingress/                 Ingress rules for pre-release and production
OrchestrationPipeline/   one Groovy file per pipeline step
Tests/                   cross-service integration tests and load tests
Documentation/           diagrams and links to the written documents
Jenkinsfile              pipeline orchestrator
```

## About this public copy

The commit history is the original one, with its original dates (12–28 June
2025). `develop` is the default branch because it holds the latest work;
`master` holds what was released to production.

The history was rewritten once before publication, so commit hashes differ
from the university repository:

- private keys and TLS material were removed, and the values of every
  Kubernetes `Secret` were replaced with `REDACTED`;
- the internal host, the server account and the e-mail addresses used by the
  pipeline were replaced with placeholders (`INTERNAL_HOST`, `ci-user`,
  `...@example.com`);
- teammates' e-mail addresses were anonymised, and the commits made by the
  Jenkins bot are attributed to `jenkins-bot`.

To run the system you therefore need to generate an RSA key pair for the Auth
service (`Backend/Auth/private.pem` and `public.pem`) and fill in the `Secret`
values in the manifests.
