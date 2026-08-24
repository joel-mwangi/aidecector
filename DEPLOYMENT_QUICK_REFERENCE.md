# Deployment Quick Reference

## 🎯 Choose Your Deployment

```
START
│
├─ Am I developing/testing?
│  └─ YES → Docker Desktop (Local)
│           • Zero setup
│           • No cost
│           • Best for dev/debug
│           ✓ docker compose up -d
│
├─ Do I need production-ready single deployment?
│  └─ YES → Single VM (Docker Compose)
│           • ~$5-20/month
│           • Simple scaling
│           • Easy backups
│           ✓ bash scripts/deploy-vm.sh
│
├─ Do I need enterprise-grade with auto-scaling?
│  └─ YES → Kubernetes
│           • ~$50-200/month
│           • Full control
│           • Global scaling
│           ✓ bash scripts/deploy-k8s.sh
│
├─ Am I already using AWS?
│  └─ YES → AWS ECS
│           • ~$50-200/month
│           • Managed services
│           • Integrated monitoring
│           ✓ bash scripts/deploy-aws-ecs.sh
│
└─ Do I want hands-off serverless?
   └─ YES → Cloud Run / App Engine
            • Pay per request
            • Zero management
            • Auto-scaling
            ✓ See DEPLOYMENT_GUIDE.md Section 5
```

---

## 📋 Deployment Comparison Table

| Factor | Local | Single VM | Kubernetes | AWS ECS | Cloud Run |
|--------|-------|-----------|-----------|---------|----------|
| **Setup Time** | 5 min | 30 min | 1 hour | 45 min | 20 min |
| **Cost** | Free | $5-20/mo | $50-200/mo | $50-200/mo | $0-100/mo |
| **Scaling** | Manual | Manual | Automatic | Automatic | Automatic |
| **Uptime SLA** | None | 95% | 99.9% | 99.95% | 99.95% |
| **Complexity** | Low | Medium | High | Medium | Low |
| **Best For** | Dev | Demo/Small | Production | AWS Shops | Serverless |
| **Failover** | None | Manual | Automatic | Automatic | Automatic |

---

## 🚀 Quick Start Commands

### 1️⃣ Local Development
```bash
# 30 seconds to running
docker compose up -d

# Test it
curl http://localhost:8000/health

# Stop
docker compose down
```

### 2️⃣ Single VM Production
```bash
# Prerequisites: Ubuntu 22.04 VM with public IP
# Time: ~10 minutes setup

# Copy deploy script to VM
scp scripts/deploy-vm.sh user@vm-ip:~/

# Run deployment
ssh user@vm-ip
chmod +x deploy-vm.sh
./deploy-vm.sh yourdomain.com

# Check status
curl http://yourdomain.com/health
```

### 3️⃣ Kubernetes (GKE Example)
```bash
# Prerequisites: GCP project, kubectl configured
# Time: ~20 minutes

# Create cluster
gcloud container clusters create detector --zone us-central1-a

# Deploy
bash scripts/deploy-k8s.sh detector

# Check status
kubectl get pods -n detector
```

### 4️⃣ AWS ECS
```bash
# Prerequisites: AWS account, docker configured
# Time: ~30 minutes

bash scripts/deploy-aws-ecs.sh detector detector-api us-east-1
```

---

## 🔒 Security Checklist by Deployment Type

### Local (Development Only)
- [ ] Use weak passwords (test only)
- [ ] Firewall allows localhost only
- [ ] No TLS needed
- [ ] Backups optional

### Single VM (Production)
- [ ] Generate strong passwords (openssl rand -base64 16)
- [ ] Enable UFW firewall
- [ ] Install Let's Encrypt SSL
- [ ] Setup daily backups
- [ ] Monitor disk usage
- [ ] Setup log rotation
- [ ] Restrict SSH access

### Kubernetes (Enterprise)
- [ ] Use managed secrets (not in git)
- [ ] Enable RBAC
- [ ] Setup network policies
- [ ] Install cert-manager
- [ ] Enable audit logging
- [ ] Setup pod security policies
- [ ] Configure resource quotas

### AWS ECS (Cloud)
- [ ] Use AWS Secrets Manager
- [ ] Enable VPC security groups
- [ ] Use IAM roles
- [ ] Enable ALB access logs
- [ ] Setup CloudTrail
- [ ] Enable RDS encryption
- [ ] Setup backup retention

---

## 📊 Cost Estimation

### Local Development
```
$0/month (just your laptop)
```

### Single VM (Small Scale, ~100 req/day)
```
Compute:        $5-10/mo  (t2.small instance)
Storage:        $2-5/mo   (50GB disk)
Bandwidth:      $0-5/mo
Total:          ~$10-20/mo
```

### Kubernetes (Medium Scale, ~1000 req/day)
```
3x API pods:         $30/mo    (0.5 CPU, 1GB RAM each)
2x Worker pods:      $30/mo    (1 CPU, 2GB RAM each)
PostgreSQL:          $15/mo    (minimal managed)
Redis:               $5/mo     (in-cluster)
Load Balancer:       $20/mo    (ingress)
Storage:             $5/mo     (50GB persistent)
Total:               ~$105/mo
```

### AWS ECS (Medium Scale, ~1000 req/day)
```
ECS Tasks:           $40/mo    (2x t3.small)
RDS PostgreSQL:      $30/mo    (db.t3.micro)
ElastiCache Redis:   $20/mo    (t3.micro)
ALB:                 $20/mo    (includes 100GB)
CloudWatch:          $5/mo     (logs)
Total:               ~$115/mo
```

### Cloud Run (Serverless, ~1000 req/day)
```
Compute:        $5-20/mo  (2M invocations @128MB)
PostgreSQL:     $20/mo    (managed instance)
Storage:        $5/mo     (uploads)
Total:          ~$30-45/mo
```

---

## 🛠️ Maintenance Tasks by Environment

### Local (Development)
Daily:
- Check services running
- Monitor logs for errors

Weekly:
- Delete test uploads
- Reset database if needed

### Single VM (Production)
Daily:
- Monitor disk usage
- Check systemd status
- Review error logs

Weekly:
- Verify backups created
- Check SSL certificate expiration (60+ days)
- Monitor Docker image sizes

Monthly:
- Security updates (apt upgrade)
- Database maintenance (VACUUM)
- Cleanup old uploads

### Kubernetes
Daily:
- Pod health checks
- Node health
- PVC usage

Weekly:
- Persistent volume backups
- Resource quota review
- Security audit

Monthly:
- Certificate renewal
- Node image updates
- Disaster recovery drill

### AWS ECS
Daily:
- CloudWatch alarms
- RDS backups verified
- Service replicas healthy

Weekly:
- Cost analysis
- Security group review
- IAM permissions audit

Monthly:
- RDS maintenance window
- ElastiCache parameter updates
- Reserved instance optimization

---

## 🐛 Troubleshooting by Deployment

### Local Issues
```bash
# API won't start
docker compose logs api

# Check port conflicts
docker ps
lsof -i :8000

# Restart everything
docker compose restart
```

### Single VM Issues
```bash
# Service health
systemctl status docker-detector
docker-compose logs -f

# Database connection
docker-compose exec postgres psql -U detector

# Disk space
df -h
docker system df

# Restart services
docker-compose restart
```

### Kubernetes Issues
```bash
# Pod status
kubectl describe pod <pod-name> -n detector

# Logs
kubectl logs <pod-name> -n detector

# Events
kubectl get events -n detector

# Delete and recreate
kubectl delete pod <pod-name> -n detector
```

### AWS ECS Issues
```bash
# View task details
aws ecs describe-tasks --cluster detector --tasks <task-arn>

# View logs
aws logs tail /ecs/detector --follow

# Force new deployment
aws ecs update-service --cluster detector --service detector-api --force-new-deployment

# Check service status
aws ecs describe-services --cluster detector --services detector-api
```

---

## 📈 Scaling Strategies

### When to Scale
```
API Response Time:     > 1s       → Add API replicas
Database Connections:  > 80%      → Upgrade RDS
Queue Depth:          > 1000      → Add workers
Memory Usage:         > 80%       → Increase pod memory
CPU Usage:            > 70%       → Add replicas or upgrade nodes
```

### How to Scale

**Horizontal (Add More Instances)**
```bash
# Kubernetes
kubectl scale deployment api --replicas=5 -n detector

# Docker Compose
docker-compose up -d --scale visual-worker=4

# AWS ECS
aws ecs update-service --cluster detector --service detector-api --desired-count 5
```

**Vertical (Bigger Machines)**
```bash
# Update Kubernetes resource requests
# Update ECS task definition CPU/memory
# Update RDS instance class
```

**Auto-Scaling**
```bash
# Kubernetes HPA (already configured)
# AWS ECS service autoscaling
# GCP Cloud Run (automatic)
```

---

## 🎓 Recommended Learning Path

1. **Start Local** (30 min)
   - Run locally with Docker Compose
   - Submit test analyses
   - Understand the architecture

2. **Deploy Single VM** (2 hours)
   - Get a cheap VPS ($5-10/mo)
   - Run deploy-vm.sh
   - Access from browser
   - Setup SSL

3. **Learn Kubernetes** (1 week)
   - Read Docker/Kubernetes docs
   - Practice local k8s with minikube
   - Deploy to managed k8s (GKE, EKS)

4. **Optimize for Scale** (ongoing)
   - Add monitoring
   - Setup alerting
   - Implement CI/CD
   - Performance tuning

---

## 📞 Need Help?

### Common Questions

**Q: Which should I choose?**
A: Start with Docker Desktop locally. If it works, use Single VM. If you need enterprise features, use Kubernetes.

**Q: Can I start with one and move later?**
A: Yes! All deployments use the same Docker image. Migration is just redeploying.

**Q: How do I handle database backups?**
A: Local (manual), VM (automated daily), Kubernetes (PVC backups), Cloud (managed backups).

**Q: Can I deploy to multiple regions?**
A: Yes with Kubernetes. Deploy to multiple clusters and use DNS routing.

**Q: What if I need GPU?**
A: VM: Use GPU instance type. K8s: Add GPU node pool. ECS: Use GPU-enabled instance.

---

## ✅ Deployment Checklist

Before going live:
- [ ] Passwords are strong and stored securely
- [ ] Database is initialized with schema
- [ ] Redis connection working
- [ ] API health check passes
- [ ] Sample analysis runs successfully
- [ ] Logs are being collected
- [ ] Backups are configured
- [ ] Monitoring/alerting is set up
- [ ] SSL/TLS certificate is valid
- [ ] Firewall rules are correct
- [ ] Resource limits are reasonable
- [ ] Load balancer/ingress configured
- [ ] Team has access to dashboards
- [ ] Runbook documented
- [ ] On-call rotation established
