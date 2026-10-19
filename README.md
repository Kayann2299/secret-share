# SecretShare — Plataforma Cloud-Native para Partilha Segura de Segredos

> Trabalho 2 — Computação Distribuída | LEI | ISMAT | 2025/2026

## Arquitetura

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Frontend  │      │   Backend   │      │    Redis    │
│  (nginx)    │----->│   (Flask)   │----->│  (stateful) │
│  porta 80   │      │  porta 5000 │      │  porta 6379 │
└─────────────┘      └─────────────┘      └─────────────┘
    stateless           stateless           stateful
```

**Zero-knowledge:** o segredo é cifrado com OpenPGP **no browser** antes de ser enviado.
O servidor armazena apenas o ciphertext — nunca vê o conteúdo em claro.

## Stack

| Componente | Tecnologia | Razão |
|---|---|---|
| Frontend | HTML/JS + OpenPGP.js | Cifragem no cliente |
| Backend | Flask + Gunicorn | Leve, fácil de containerizar |
| Persistência | Redis | TTL nativo, expiração automática |
| Proxy | Nginx | Reverse proxy + security headers |
| Container | Docker | Isolamento e reprodutibilidade |
| Orquestração | Kubernetes | Escalabilidade e resiliência |

## Execução Local com Docker Compose

```bash
# 1. Copiar variáveis de ambiente
cp .env.example .env
# Editar .env com uma password segura para o Redis

# 2. Construir e iniciar
docker compose up --build -d

# 3. Aceder à aplicação
open http://localhost:8080

# 4. Ver logs
docker compose logs -f backend

# 5. Estado dos serviços
docker compose ps
```

## Execução em Kubernetes (minikube)

```bash
# 1. Iniciar minikube
minikube start

# 2. Construir imagens no contexto do minikube
eval $(minikube docker-env)
docker build -t secretshare-backend:latest ./backend
docker build -t secretshare-frontend:latest ./frontend

# 3. Editar a password no Secret (k8s/01-secret.yaml) antes de aplicar!
# Substituir "changeme_strong_password" por uma password real

# 4. Aplicar todos os manifestos por ordem
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-secret.yaml
kubectl apply -f k8s/02-configmap.yaml
kubectl apply -f k8s/03-redis.yaml
kubectl apply -f k8s/04-backend.yaml
kubectl apply -f k8s/05-frontend.yaml
kubectl apply -f k8s/06-ingress.yaml

# 5. Verificar estado dos pods
kubectl get pods -n secretshare
kubectl get services -n secretshare

# 6. Aceder via minikube
minikube service frontend-service -n secretshare

# 7. Escalar o backend manualmente
kubectl scale deployment backend --replicas=4 -n secretshare

# 8. Ver HPA (autoscaling)
kubectl get hpa -n secretshare
```

## Estrutura do Repositório

```
secret-share/
├── backend/
│   ├── app.py              # API Flask
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html          # SPA com cifragem OpenPGP no browser
│   ├── nginx.conf          # Config nginx + security headers
│   └── Dockerfile
├── k8s/
│   ├── 00-namespace.yaml
│   ├── 01-secret.yaml      # Redis password (Kubernetes Secret)
│   ├── 02-configmap.yaml   # Configuração não sensível
│   ├── 03-redis.yaml       # Redis + PVC + Service
│   ├── 04-backend.yaml     # Backend + HPA (autoscaling)
│   ├── 05-frontend.yaml    # Frontend deployment
│   └── 06-ingress.yaml     # Ingress nginx
├── docker-compose.yml
├── nginx-proxy.conf
├── .env.example
└── README.md
```

## Endpoints da API

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/health` | Health check (Redis + app) |
| POST | `/api/secret` | Criar segredo |
| GET | `/api/secret/<id>` | Consultar e consumir segredo |

### POST /api/secret — body JSON
```json
{
  "ciphertext": "<OpenPGP armored string>",
  "ttl": 86400,
  "one_time": true
}
```

## Mecanismos de Segurança

- **Zero-knowledge**: cifragem AES-256 com OpenPGP.js no browser
- **TTL automático**: Redis expira segredos sem intervenção manual
- **Leitura única**: segredo eliminado após primeira consulta
- **Utilizador não-root**: containers correm com `appuser`
- **Security headers**: X-Frame-Options, CSP, X-Content-Type-Options
- **Secrets Kubernetes**: password Redis em `kind: Secret` (base64)
- **Rede interna**: Redis apenas acessível na rede `internal`

## Questões de Reflexão (resumo)

1. **Stateless vs Stateful**: Frontend e Backend são stateless; Redis é stateful (dados persistidos em PVC)
2. **Vantagens Docker**: ambiente reprodutível, isolamento, deploy consistente em qualquer máquina
3. **Compose vs K8s**: Compose é simples para dev local; K8s adiciona HA, autoscaling, rolling updates
4. **Config sensível**: password Redis em `.env` (Compose) e `kind: Secret` (K8s)
5. **Servidor acede em claro?**: Não — o ciphertext é gerado no browser com OpenPGP antes do envio
6. **Escalabilidade**: backend stateless escala horizontalmente via HPA; Redis com Redis Cluster em produção
7. **Limitações**: Redis single-node é SPOF; sem HTTPS no lab; Secret K8s apenas base64 (usar Sealed Secrets em prod)
8. **Inspiração no Yopass**: TTL, leitura única, zero-knowledge e self-hosting; diferença principal: stack própria (Flask+Redis vs Go+Memcached)
