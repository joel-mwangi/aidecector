# Deployment Guide - Multimodal Misinformation Detection System

## Quick Reference

| Environment | Best For | Complexity | Cost |
|---|---|---|---|
| Docker Desktop (local) | Development, testing | Low | Free |
| Docker Compose (single VM) | Small deployments, demos | Medium | $5-20/mo |
| Kubernetes (cloud) | Production, scaling | High | $50-500+/mo |
| AWS ECS | AWS ecosystem | Medium | $50-200+/mo |
| Cloud Run (GCP) | Serverless, scaling | Low-Medium | $0-100/mo |

---

## 1. LOCAL DEVELOPMENT (Docker Desktop)

### Prerequisites
- Docker Desktop installed
- 4GB+ RAM allocated to Docker
- 20GB+ free disk space

### Deploy Locally

```bash
# Navigate to project
cd misinformation-detection-system

# Build image
docker build -t misinformation-detector:latest -f Dockerfile .

# Start stack
docker compose up --build -d

# Verify services
docker compose ps

# View logs
docker compose logs -f api

# Test health
curl http://localhost:8000/health

# Submit test analysis
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "media_type": "image",
    "claim": "Test image"
  }'

# Stop all services
docker compose down
```

### Local Development Tips

```bash
# Rebuild only API (faster)
docker compose build api && docker compose up -d api

# Stream logs from specific service
docker compose logs -f detection-queue

# Execute command in running container
docker compose exec api python -m pytest tests/ -v

# Access database
docker compose exec postgres psql -U detector -d misinformation

# Clear all data
docker compose down -v
```

---

## 2. SINGLE VM DEPLOYMENT (Docker Compose)

Best for: Small-scale production, proof-of-concept, internal use.

### Prerequisites
- Linux VM (Ubuntu 22.04 recommended)
- 8GB+ RAM
- 50GB+ disk space
- Public/private IP address

### Step 1: Install Docker & Docker Compose

```bash
# SSH into VM
ssh user@your-vm-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify
docker --version && docker-compose --version
```

### Step 2: Clone & Configure Project

```bash
# Clone repository (or upload files)
git clone https://github.com/your-repo/misinformation-detection.git
cd misinformation-detection

# Create environment file
cat > .env <<EOF
ENVIRONMENT=production
LOG_LEVEL=info
DATABASE_URL=postgresql://detector:CHANGE_ME@postgres:5432/misinformation
REDIS_URL=redis://redis:6379
GPU_ENABLED=false
API_PORT=8000
EOF

# Update docker-compose.yml for production
# Change postgres password
# Change redis persistence settings
# Add memory/CPU limits
```

### Step 3: Deploy with Reverse Proxy

Install Nginx as reverse proxy:

```bash
# Install Nginx
sudo apt install -y nginx

# Create Nginx config
sudo tee /etc/nginx/sites-available/detector <<EOF
upstream detector_api {
    server localhost:8000;
}

server {
    listen 80;
    server_name your.domain.com;

    location / {
        proxy_pass http://detector_api;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://detector_api;
        access_log off;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/detector /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Optional: SSL with Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your.domain.com
```

### Step 4: Start Services

```bash
# Build and start
docker compose up -d --build

# Watch logs
docker compose logs -f

# Verify all running
docker compose ps

# Check database is initialized
docker compose exec postgres psql -U detector -d misinformation -c "\dt"
```

### Step 5: Backup & Monitoring

```bash
# Create backup script
sudo tee /usr/local/bin/backup-detector.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/backups/detector"
mkdir -p $BACKUP_DIR
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup database
docker compose exec -T postgres pg_dump -U detector misinformation > \
  $BACKUP_DIR/db_$TIMESTAMP.sql

# Backup uploads
tar -czf $BACKUP_DIR/uploads_$TIMESTAMP.tar.gz uploads/

# Keep only last 7 days
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $TIMESTAMP"
EOF

sudo chmod +x /usr/local/bin/backup-detector.sh

# Schedule daily backups with cron
sudo crontab -e
# Add: 2 3 * * * /usr/local/bin/backup-detector.sh
```

### Step 6: Monitor with systemd

Create systemd service for auto-restart:

```bash
sudo tee /etc/systemd/system/docker-detector.service <<EOF
[Unit]
Description=Misinformation Detector Docker Stack
After=docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=/home/user/misinformation-detection
ExecStart=/usr/bin/docker-compose up
ExecStop=/usr/bin/docker-compose down
Restart=on-failure
RestartSec=10s
User=user

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable docker-detector
sudo systemctl start docker-detector
sudo systemctl status docker-detector
```

---

## 3. KUBERNETES DEPLOYMENT (Production)

Best for: Large-scale, multi-region, high availability.

### Prerequisites
- Kubernetes cluster (GKE, EKS, AKS, or self-hosted)
- kubectl configured
- Helm (optional but recommended)

### Step 1: Create Kubernetes Manifests

```bash
# Create namespace
kubectl create namespace detector

# Create secrets for sensitive data
kubectl create secret generic detector-secrets \
  --from-literal=db-password=CHANGE_ME \
  --from-literal=redis-password=CHANGE_ME \
  -n detector
```

Create `k8s/postgres-deployment.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: detector
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: detector
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:16-alpine
        env:
        - name: POSTGRES_USER
          value: detector
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: detector-secrets
              key: db-password
        - name: POSTGRES_DB
          value: misinformation
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U detector
          initialDelaySeconds: 30
          periodSeconds: 10
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: detector
spec:
  selector:
    app: postgres
  ports:
  - protocol: TCP
    port: 5432
    targetPort: 5432
  type: ClusterIP
```

Create `k8s/redis-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: detector
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command:
        - redis-server
        - "--appendonly"
        - "yes"
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-storage
          mountPath: /data
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 10
          periodSeconds: 5
      volumes:
      - name: redis-storage
        emptyDir: {}

---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: detector
spec:
  selector:
    app: redis
  ports:
  - protocol: TCP
    port: 6379
    targetPort: 6379
  type: ClusterIP
```

Create `k8s/api-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: detector
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: misinformation-detector:latest
        imagePullPolicy: Always
        env:
        - name: ENVIRONMENT
          value: production
        - name: LOG_LEVEL
          value: info
        - name: DATABASE_URL
          value: postgresql://detector:CHANGE_ME@postgres:5432/misinformation
        - name: REDIS_URL
          value: redis://redis:6379
        - name: GPU_ENABLED
          value: "false"
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: detector
spec:
  selector:
    app: api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Create `k8s/workers-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: visual-worker
  namespace: detector
spec:
  replicas: 2
  selector:
    matchLabels:
      app: visual-worker
  template:
    metadata:
      labels:
        app: visual-worker
    spec:
      containers:
      - name: visual-worker
        image: misinformation-detector:latest
        command: ["python", "-m", "src.workers.detection_worker"]
        env:
        - name: WORKER_TYPE
          value: visual
        - name: REDIS_URL
          value: redis://redis:6379
        - name: DATABASE_URL
          value: postgresql://detector:CHANGE_ME@postgres:5432/misinformation
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: audio-worker
  namespace: detector
spec:
  replicas: 2
  selector:
    matchLabels:
      app: audio-worker
  template:
    metadata:
      labels:
        app: audio-worker
    spec:
      containers:
      - name: audio-worker
        image: misinformation-detector:latest
        command: ["python", "-m", "src.workers.detection_worker"]
        env:
        - name: WORKER_TYPE
          value: audio
        - name: REDIS_URL
          value: redis://redis:6379
        - name: DATABASE_URL
          value: postgresql://detector:CHANGE_ME@postgres:5432/misinformation
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: detector
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Step 2: Deploy to Kubernetes

```bash
# Create namespace and secrets
kubectl create namespace detector
kubectl create secret generic detector-secrets \
  --from-literal=db-password=YOUR_SECURE_PASSWORD \
  -n detector

# Apply manifests
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/workers-deployment.yaml

# Verify deployment
kubectl get pods -n detector
kubectl get services -n detector

# Monitor logs
kubectl logs -n detector -f deployment/api

# Get LoadBalancer IP
kubectl get service api -n detector
```

### Step 3: Setup Ingress (Optional)

```bash
# Install Nginx Ingress Controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace

# Create Ingress
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: detector-ingress
  namespace: detector
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - detector.example.com
    secretName: detector-tls
  rules:
  - host: detector.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
EOF
```

---

## 4. AWS DEPLOYMENT (ECS)

Best for: AWS ecosystem, managed services.

### Step 1: Create ECR Repository

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Create repository
aws ecr create-repository --repository-name misinformation-detector

# Push image
docker tag misinformation-detector:latest \
  ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/misinformation-detector:latest

docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/misinformation-detector:latest
```

### Step 2: Setup RDS PostgreSQL

```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier detector-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username detector \
  --master-user-password CHANGE_ME \
  --allocated-storage 50 \
  --storage-type gp2
```

### Step 3: Setup ElastiCache Redis

```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id detector-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```

### Step 4: Create ECS Task Definition

Save as `ecs-task-definition.json`:

```json
{
  "family": "detector-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/misinformation-detector:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        },
        {
          "name": "DATABASE_URL",
          "value": "postgresql://detector:PASSWORD@detector-db.xxxxx.us-east-1.rds.amazonaws.com:5432/misinformation"
        },
        {
          "name": "REDIS_URL",
          "value": "redis://detector-redis.xxxxx.ng.0001.use1.cache.amazonaws.com:6379"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/detector",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create ECS service
aws ecs create-service \
  --cluster default \
  --service-name detector-api \
  --task-definition detector-api \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

---

## 5. GCP CLOUD RUN (Serverless)

Best for: Minimal management, auto-scaling.

```bash
# Setup
gcloud config set project YOUR_PROJECT_ID

# Create Cloud SQL instance
gcloud sql instances create detector-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create misinformation --instance=detector-db

# Create service account
gcloud iam service-accounts create detector-app

# Build and push to Artifact Registry
gcloud builds submit --tag us-central1-docker.pkg.dev/PROJECT_ID/detector/detector:latest

# Deploy to Cloud Run
gcloud run deploy detector-api \
  --image us-central1-docker.pkg.dev/PROJECT_ID/detector/detector:latest \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars DATABASE_URL=postgresql://... \
  --set-env-vars REDIS_URL=redis://...
```

---

## 6. MONITORING & LOGGING

### Application Monitoring

```yaml
# prometheus-config.yaml for Kubernetes
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: detector
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'detector-api'
      static_configs:
      - targets: ['api:8000']
      metrics_path: '/metrics'
```

### Log Aggregation

```bash
# Install ELK stack (Elasticsearch, Logstash, Kibana)
helm repo add elastic https://helm.elastic.co
helm install elasticsearch elastic/elasticsearch -n detector
helm install kibana elastic/kibana -n detector

# Configure Docker logging
docker run -d \
  --log-driver json-file \
  --log-opt labels=app=detector \
  --log-opt max-size=10m \
  --log-opt max-file=5 \
  misinformation-detector
```

### Health Checks

```bash
# Setup uptime monitoring
curl https://healthchecks.io/
# Or use:
# - DataDog
# - New Relic
# - Sentry (for error tracking)
```

---

## 7. SCALING STRATEGIES

### Horizontal Scaling

```bash
# Docker Compose scale workers
docker compose up -d --scale visual-worker=4 --scale audio-worker=4

# Kubernetes scale
kubectl scale deployment visual-worker --replicas=5 -n detector
kubectl scale deployment audio-worker --replicas=5 -n detector
```

### Vertical Scaling

Update resource requests in manifests:

```yaml
resources:
  requests:
    memory: "4Gi"      # Increase from 2Gi
    cpu: "2000m"       # Increase from 1000m
```

### Queue Tuning

```python
# In config/settings.py
NUM_WORKERS = 8              # More workers
INFERENCE_TIMEOUT = 600      # Longer timeout for GPU
GPU_ENABLED = True           # Use GPUs
```

---

## 8. SECURITY BEST PRACTICES

### Network Security

```bash
# Use firewall rules
ufw allow 22/tcp      # SSH only
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS

# Kubernetes Network Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: detector-policy
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: detector
```

### Secrets Management

```bash
# Use external secrets
helm repo add external-secrets https://external-secrets.io
helm install external-secrets external-secrets/external-secrets -n detector

# Or use cloud providers
# AWS Secrets Manager
# GCP Secret Manager
# Azure Key Vault
```

### SSL/TLS

```bash
# Use cert-manager
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager -n cert-manager --create-namespace
```

---

## 9. DEPLOYMENT CHECKLIST

- [ ] Environment variables configured
- [ ] Database initialized with schema
- [ ] Redis cache available
- [ ] API port accessible
- [ ] Workers can connect to queue
- [ ] Logging configured
- [ ] Backups scheduled
- [ ] Monitoring setup
- [ ] SSL/TLS certificates valid
- [ ] Firewall rules correct
- [ ] Resource limits set
- [ ] Health checks configured
- [ ] Auto-scaling rules enabled
- [ ] Rollback plan ready

---

## 10. TROUBLESHOOTING

### Common Issues

```bash
# API won't start
docker compose logs api
# Check: DATABASE_URL, REDIS_URL, port conflicts

# Database connection fails
docker compose exec postgres pg_isready
# Check: postgres service is running, credentials correct

# Workers not picking up tasks
docker compose logs detection-queue
docker compose exec redis redis-cli DBSIZE
# Check: Redis running, tasks being enqueued

# High memory usage
docker stats
# Scale up replicas or reduce batch size

# Slow inference
kubectl top pods -n detector
# Consider GPU, increase workers, optimize models
```

---

Choose the deployment option that best fits your scale, budget, and infrastructure requirements. Start with Docker Compose for development, scale to Kubernetes for production.
