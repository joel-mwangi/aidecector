#!/bin/bash
# Deploy to Kubernetes

set -e

NAMESPACE=${1:-detector}
DOMAIN=${2:-detector.example.com}
REGION=${3:-us-central1}

echo "🚀 Deploying to Kubernetes"
echo "=========================="
echo "Namespace: $NAMESPACE"
echo "Domain: $DOMAIN"
echo "Region: $REGION"
echo ""

# Check prerequisites
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl not installed"; exit 1; }

# Create namespace
echo "Creating namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Create secrets
echo "Creating secrets..."
DB_PASS=$(openssl rand -base64 16)
REDIS_PASS=$(openssl rand -base64 16)

kubectl create secret generic detector-secrets \
  --from-literal=db-password=$DB_PASS \
  --from-literal=redis-password=$REDIS_PASS \
  -n $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Create ConfigMap with environment variables
echo "Creating ConfigMap..."
kubectl create configmap detector-config \
  -n $NAMESPACE \
  --from-literal=ENVIRONMENT=production \
  --from-literal=LOG_LEVEL=info \
  --from-literal=GPU_ENABLED=false \
  --dry-run=client -o yaml | kubectl apply -f -

# Deploy PostgreSQL
echo "Deploying PostgreSQL..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: $NAMESPACE
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
  namespace: $NAMESPACE
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
  namespace: $NAMESPACE
spec:
  selector:
    app: postgres
  ports:
  - protocol: TCP
    port: 5432
    targetPort: 5432
  type: ClusterIP
EOF

# Deploy Redis
echo "Deploying Redis..."
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: $NAMESPACE
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
        - "--requirepass"
        - "\$(REDIS_PASSWORD)"
        - "--appendonly"
        - "yes"
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: detector-secrets
              key: redis-password
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
  namespace: $NAMESPACE
spec:
  selector:
    app: redis
  ports:
  - protocol: TCP
    port: 6379
    targetPort: 6379
  type: ClusterIP
EOF

# Deploy API
echo "Deploying API..."
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: $NAMESPACE
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
        imagePullPolicy: IfNotPresent
        env:
        - name: ENVIRONMENT
          valueFrom:
            configMapKeyRef:
              name: detector-config
              key: ENVIRONMENT
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: detector-config
              key: LOG_LEVEL
        - name: DATABASE_URL
          value: postgresql://detector:\$(DB_PASS)@postgres:5432/misinformation
        - name: REDIS_URL
          value: redis://::\$(REDIS_PASS)@redis:6379
        - name: DB_PASS
          valueFrom:
            secretKeyRef:
              name: detector-secrets
              key: db-password
        - name: REDIS_PASS
          valueFrom:
            secretKeyRef:
              name: detector-secrets
              key: redis-password
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
  namespace: $NAMESPACE
spec:
  selector:
    app: api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: $NAMESPACE
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
EOF

# Deploy Workers
echo "Deploying Workers..."
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: visual-worker
  namespace: $NAMESPACE
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
        - name: DATABASE_URL
          value: postgresql://detector:\$(DB_PASS)@postgres:5432/misinformation
        - name: REDIS_URL
          value: redis://::\$(REDIS_PASS)@redis:6379
        - name: DB_PASS
          valueFrom:
            secretKeyRef:
              name: detector-secrets
              key: db-password
        - name: REDIS_PASS
          valueFrom:
            secretKeyRef:
              name: detector-secrets
              key: redis-password
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
  namespace: $NAMESPACE
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
        - name: DATABASE_URL
          value: postgresql://detector:\$(DB_PASS)@postgres:5432/misinformation
        - name: REDIS_URL
          value: redis://::\$(REDIS_PASS)@redis:6379
        - name: DB_PASS
          valueFrom:
            secretKeyRef:
              name: detector-secrets
              key: db-password
        - name: REDIS_PASS
          valueFrom:
            secretKeyRef:
              name: detector-secrets
              key: redis-password
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
EOF

# Wait for deployments
echo ""
echo "Waiting for deployments to be ready..."
kubectl rollout status deployment/postgres -n $NAMESPACE --timeout=5m
kubectl rollout status deployment/redis -n $NAMESPACE --timeout=5m
kubectl rollout status deployment/api -n $NAMESPACE --timeout=5m

# Get LoadBalancer IP
echo ""
echo "=========================================="
echo "✓ Kubernetes Deployment Complete!"
echo "=========================================="
echo ""
kubectl get pods -n $NAMESPACE
echo ""
echo "LoadBalancer IP:"
kubectl get service api -n $NAMESPACE
echo ""
echo "View logs:"
echo "  kubectl logs -n $NAMESPACE -f deployment/api"
echo ""
echo "Scale API replicas:"
echo "  kubectl scale deployment api --replicas=5 -n $NAMESPACE"
echo ""
echo "Delete deployment:"
echo "  kubectl delete namespace $NAMESPACE"
echo ""
