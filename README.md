# SecretShare — Cloud-Native Platform for Secure Secret Sharing

> **Assignment 2 — Distributed Computing | BSc in Computer Engineering (LEI) | ISMAT | 2025/2026**

## Architecture

```text
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Frontend  │      │   Backend   │      │    Redis    │
│   (nginx)   │----->│   (Flask)   │----->│  (stateful) │
│  port 80    │      │  port 5000  │      │  port 6379  │
└─────────────┘      └─────────────┘      └─────────────┘
    stateless            stateless             stateful
```

**Zero-knowledge:** Secrets are encrypted using OpenPGP **in the browser** before being sent to the server.

The server stores only the ciphertext and never sees the plaintext secret.

## Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Frontend | HTML/JavaScript + OpenPGP.js | Client-side encryption |
| Backend | Flask + Gunicorn | Lightweight, easy-to-containerize API |
| Persistence | Redis | Native TTL support and automatic expiration |
| Proxy | Nginx | Reverse proxy and security headers |
| Containerization | Docker | Isolation and reproducibility |
| Orchestration | Kubernetes | Scalability and resilience |

## Running Locally with Docker Compose

```bash
# 1. Copy the environment variables template
cp .env.example .env
# Edit .env and set a strong Redis password

# 2. Build and start the services
docker compose up --build -d

# 3. Access the application
open http://localhost:8080

# 4. View backend logs
docker compose logs -f backend

# 5. Check the status of the services
docker compose ps
```

## Deploying to Kubernetes (minikube)

```bash
# 1. Start minikube
minikube start

# 2. Build images in the minikube Docker environment
eval $(minikube docker-env)
docker build -t secretshare-backend:latest ./backend
docker build -t secretshare-frontend:latest ./frontend

# 3. Edit the password in the Secret
# (k8s/01-secret.yaml) before applying the manifests!
# Replace "changeme_strong_password" with a real password

# 4. Apply all manifests in order
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-secret.yaml
kubectl apply -f k8s/02-configmap.yaml
kubectl apply -f k8s/03-redis.yaml
kubectl apply -f k8s/04-backend.yaml
kubectl apply -f k8s/05-frontend.yaml
kubectl apply -f k8s/06-ingress.yaml

# 5. Check pod and service status
kubectl get pods -n secretshare
kubectl get services -n secretshare

# 6. Access the application through minikube
minikube service frontend-service -n secretshare

# 7. Manually scale the backend
kubectl scale deployment backend --replicas=4 -n secretshare

# 8. Check Horizontal Pod Autoscaler (HPA)
kubectl get hpa -n secretshare
```

## Repository Structure

```text
secret-share/
├── backend/
│   ├── app.py              # Flask API
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html          # SPA with browser-based OpenPGP encryption
│   ├── nginx.conf          # Nginx configuration and security headers
│   └── Dockerfile
├── k8s/
│   ├── 00-namespace.yaml   # Kubernetes namespace
│   ├── 01-secret.yaml      # Redis password (Kubernetes Secret)
│   ├── 02-configmap.yaml   # Non-sensitive configuration
│   ├── 03-redis.yaml       # Redis, PVC and Service
│   ├── 04-backend.yaml     # Backend Deployment and HPA
│   ├── 05-frontend.yaml    # Frontend Deployment
│   └── 06-ingress.yaml     # NGINX Ingress configuration
├── docker-compose.yml
├── nginx-proxy.conf
├── .env.example
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check for the application and Redis |
| POST | `/api/secret` | Create a secret |
| GET | `/api/secret/<id>` | Retrieve and consume a secret |

### POST `/api/secret` — JSON Request Body

```json
{
  "ciphertext": "<OpenPGP armored string>",
  "ttl": 86400,
  "one_time": true
}
```

- `ciphertext`: The encrypted secret in OpenPGP ASCII-armored format.
- `ttl`: Time to live in seconds (86,400 seconds = 24 hours).
- `one_time`: Whether the secret should be deleted after its first successful retrieval.

## Security Mechanisms

- **Zero-knowledge architecture:** Secrets are encrypted in the browser using OpenPGP.js before transmission.
- **Automatic TTL expiration:** Redis automatically expires secrets without requiring manual cleanup.
- **One-time access:** Secrets are deleted after their first successful retrieval when one-time access is enabled.
- **Non-root containers:** Containers run as the `appuser` user.
- **Security headers:** Includes `X-Frame-Options`, Content Security Policy (CSP), and `X-Content-Type-Options`.
- **Kubernetes Secrets:** The Redis password is stored in a Kubernetes `Secret` resource, encoded in base64.
- **Internal network isolation:** Redis is accessible only through the internal network.

## Reflection Questions — Summary

1. **Stateless vs. stateful:** The frontend and backend are stateless, while Redis is stateful, with data persistence provided by a PersistentVolumeClaim (PVC).

2. **Advantages of Docker:** Reproducible environments, process isolation, and consistent deployment across different machines.

3. **Docker Compose vs. Kubernetes:** Compose simplifies local development, while Kubernetes provides advanced orchestration capabilities, including high availability, autoscaling, and rolling updates.

4. **Sensitive configuration:** The Redis password is stored in a `.env` file for Docker Compose and in a Kubernetes `Secret` for Kubernetes deployments.

5. **Can the server access the plaintext secret?** No. The secret is encrypted in the browser using OpenPGP.js before being transmitted to the backend.

6. **Scalability:** The stateless backend can scale horizontally using the Horizontal Pod Autoscaler (HPA). For production environments, Redis Cluster can provide a more scalable data layer.

7. **Limitations:** A single Redis instance is a single point of failure (SPOF). The lab deployment does not include HTTPS by default. Kubernetes Secrets are base64-encoded rather than encrypted by base64 itself; production deployments should use appropriate encryption at rest and secret-management solutions.

8. **Inspired by Yopass:** The project follows concepts such as TTL, one-time access, zero-knowledge encryption, and self-hosting. The main difference is its custom technology stack: Flask and Redis instead of Go and Memcached.

---

**Project:** SecretShare  
**Course:** Distributed Computing  
**Academic Year:** 2025/2026  
**Institution:** ISMAT
