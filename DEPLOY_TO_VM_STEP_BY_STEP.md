# Deploy to Production VM - Step-by-Step Guide

Complete guide to deploy the misinformation detector to a single production VM in 30 minutes.

## Prerequisites

- Ubuntu 22.04 VM (or equivalent Linux)
- 4GB+ RAM
- 50GB+ disk space
- Public IP address or domain name
- SSH access to your VM
- Local machine with Docker installed

**Cost:** ~$5-20/month on DigitalOcean, Linode, AWS, etc.

---

## Step 1: Get a VM (5 minutes)

### Option A: DigitalOcean (Recommended for beginners)

```bash
# Go to https://www.digitalocean.com
# Click "Create" → "Droplets"
# Choose:
#   - Ubuntu 22.04 x64
#   - $6/month Basic plan (2GB RAM, 50GB SSD)
#   - Choose your region
#   - Add SSH key (or use password)
#   - Create

# Wait ~1 minute for VM to boot
# Copy the IP address shown
```

### Option B: Other Providers

- **AWS EC2:** t2.small (~$10/mo)
- **Linode:** Nanode 1GB (~$5/mo)
- **Azure:** B1s (~$7/mo)
- **Vultr:** Cloud Compute ($2.50/mo)

---

## Step 2: Connect to VM (2 minutes)

```bash
# From your local machine
# Replace 123.45.67.89 with your VM's IP

ssh root@123.45.67.89

# Or if using password
# ssh ubuntu@123.45.67.89
# (password provided by provider)
```

---

## Step 3: Install Docker & Dependencies (10 minutes)

**Copy and paste this entire block into your SSH session:**

```bash
#!/bin/bash
set -e

echo "🐳 Installing Docker and dependencies..."

# Update system
sudo apt update
sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L \
  "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install git
sudo apt install -y git

# Verify installations
docker --version
docker-compose --version
git --version

echo "✓ Installation complete!"
```

---

## Step 4: Clone Project (2 minutes)

```bash
# Clone the project
git clone https://github.com/YOUR_REPO/misinformation-detection.git
cd misinformation-detection

# Or if you uploaded files manually:
# (skip this step)
```

---

## Step 5: Configure Environment (2 minutes)

**Still in SSH session, run:**

```bash
# Generate strong passwords
DB_PASS=$(openssl rand -base64 16)
REDIS_PASS=$(openssl rand -base64 16)

# Create .env file
cat > .env <<EOF
ENVIRONMENT=production
LOG_LEVEL=info
DATABASE_URL=postgresql://detector:$DB_PASS@postgres:5432/misinformation
REDIS_URL=redis://:$REDIS_PASS@redis:6379
GPU_ENABLED=false
API_HOST=0.0.0.0
API_PORT=8000
EOF

# Save passwords to a local file for backup
cat > /tmp/credentials.txt <<EOF
=== MISINFORMATION DETECTOR CREDENTIALS ===
Database Password: $DB_PASS
Redis Password: $REDIS_PASS
Timestamp: $(date)
EOF

echo "✓ Configuration complete"
cat /tmp/credentials.txt

# IMPORTANT: Copy these credentials to somewhere safe
# You'll need them later if something breaks
```

---

## Step 6: Setup Reverse Proxy (Nginx) (5 minutes)

**Install Nginx:**

```bash
sudo apt install -y nginx

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/detector <<'EOF'
upstream detector_api {
    server localhost:8000;
}

server {
    listen 80;
    server_name _;
    client_max_body_size 500M;

    location / {
        proxy_pass http://detector_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Health endpoint (no logging)
    location /health {
        proxy_pass http://detector_api;
        access_log off;
    }
}
EOF

# Enable the site
sudo ln -s /etc/nginx/sites-available/detector /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test nginx config
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx

echo "✓ Nginx configured"
```

---

## Step 7: Setup SSL Certificate (Optional but Recommended) (5 minutes)

**If you have a domain name:**

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate (replace your.domain.com)
sudo certbot --nginx -d your.domain.com

# This will:
# 1. Create free SSL certificate
# 2. Auto-configure Nginx
# 3. Setup auto-renewal

# Verify renewal works
sudo certbot renew --dry-run

echo "✓ SSL certificate configured"
```

**If you don't have a domain name:**

```bash
# Skip SSL and use HTTP
# Visit http://YOUR_VM_IP:8000 directly
# Note: This is fine for internal/testing use
```

---

## Step 8: Build and Deploy (10 minutes)

**Back in SSH session:**

```bash
# Build Docker image
echo "🔨 Building Docker image (this takes ~5 minutes)..."
docker build -t misinformation-detector:latest -f Dockerfile .

# Start all services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to initialize
echo "⏳ Waiting for services (30 seconds)..."
sleep 30

# Check status
docker-compose ps

# Verify database initialized
docker-compose exec -T postgres psql -U detector -d misinformation -c "\dt"

echo "✓ Deployment complete!"
```

---

## Step 9: Test the Deployment (5 minutes)

**Test from your local machine:**

```bash
# Replace 123.45.67.89 with your VM IP
# Or your.domain.com if using domain

VM_IP="123.45.67.89"

# Test health endpoint
curl http://$VM_IP/health

# Expected response:
# {"status":"healthy","timestamp":"2024-..."}

# Submit a test analysis
curl -X POST http://$VM_IP/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "media_type": "image",
    "claim": "Test claim"
  }'

# Expected response:
# {"task_id":"...", "status":"queued", "message":"..."}

# Save the task_id
TASK_ID="<paste task_id from response>"

# Check status
curl http://$VM_IP/api/v1/status/$TASK_ID

# Get results (may take a minute)
curl http://$VM_IP/api/v1/results/$TASK_ID

echo "✓ All tests passed!"
```

---

## Step 10: Setup Monitoring & Backups (5 minutes)

### Setup Daily Backups

**In SSH session:**

```bash
# Create backup directory
mkdir -p /backups/detector
sudo chown $USER:$USER /backups/detector

# Create backup script
cat > /usr/local/bin/backup-detector.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/backups/detector"
mkdir -p $BACKUP_DIR
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup database
docker-compose exec -T postgres pg_dump -U detector misinformation | \
  gzip > $BACKUP_DIR/db_$TIMESTAMP.sql.gz

# Backup uploads
tar -czf $BACKUP_DIR/uploads_$TIMESTAMP.tar.gz uploads/ 2>/dev/null || true

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

echo "✓ Backup completed: $TIMESTAMP"
EOF

chmod +x /usr/local/bin/backup-detector.sh

# Test backup script
bash /usr/local/bin/backup-detector.sh

# Schedule daily backups (2 AM every day)
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-detector.sh") | crontab -

echo "✓ Backups scheduled for 2 AM daily"
```

### Setup Health Monitoring

```bash
# Create simple health check script
cat > /usr/local/bin/check-detector-health.sh <<'EOF'
#!/bin/bash
# This can be run by monitoring services like Uptime Robot, Healthchecks.io

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health)

if [ "$RESPONSE" -eq 200 ]; then
    echo "Healthy"
    exit 0
else
    echo "Unhealthy (HTTP $RESPONSE)"
    exit 1
fi
EOF

chmod +x /usr/local/bin/check-detector-health.sh

# Test it
bash /usr/local/bin/check-detector-health.sh
```

---

## Step 11: Access Your Deployment

**From your local machine:**

```bash
# Replace with your VM IP or domain
API_ENDPOINT="http://123.45.67.89"
# or
API_ENDPOINT="https://your.domain.com"

# Health check
curl $API_ENDPOINT/health

# Submit analysis (with a real media file)
curl -X POST $API_ENDPOINT/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "media_type": "image",
    "claim": "President gave a speech yesterday"
  }'

# Check status
curl $API_ENDPOINT/api/v1/status/{task_id}

# Get full results
curl $API_ENDPOINT/api/v1/results/{task_id}
```

---

## Step 12: Manage Your Deployment

### View Logs

```bash
# SSH into VM first
ssh root@123.45.67.89

# View live logs
docker-compose logs -f api

# View logs for specific service
docker-compose logs -f postgres
docker-compose logs -f redis

# View last 100 lines
docker-compose logs --tail=100 api
```

### Check Status

```bash
# See all services
docker-compose ps

# Check resource usage
docker stats

# Check disk space
df -h

# Check database
docker-compose exec postgres psql -U detector -d misinformation -c "\dt"

# Check queue depth
docker-compose exec redis redis-cli DBSIZE
```

### Restart Services

```bash
# Restart everything
docker-compose restart

# Restart specific service
docker-compose restart api

# Hard stop and restart
docker-compose down
docker-compose up -d

# Rebuild after code changes
docker-compose build
docker-compose up -d
```

### Update Code

```bash
# Pull latest changes
git pull

# Rebuild image
docker build -t misinformation-detector:latest -f Dockerfile .

# Restart service
docker-compose up -d api

# Verify health
curl http://localhost/health
```

---

## Step 13: Scaling & Performance

### Add More Workers

If processing is slow, add more workers:

```bash
# In SSH session
docker-compose up -d --scale visual-worker=3 --scale audio-worker=3

# Verify they started
docker-compose ps
```

### Monitor Performance

```bash
# Check what's using resources
docker stats

# If CPU high: Add more workers or upgrade VM
# If memory high: Reduce number of workers or upgrade VM
# If disk full: Run cleanup
docker system df
docker system prune -a
```

### Upgrade VM

If you need more resources:

1. Stop application
2. Take backup
3. Upgrade VM resources (usually 1-2 minutes downtime)
4. Start application

---

## Troubleshooting

### API Not Responding

```bash
# Check if container is running
docker-compose ps

# If not running, check logs
docker-compose logs api

# Common fixes
docker-compose restart api
docker-compose down && docker-compose up -d
```

### Database Connection Failed

```bash
# Check postgres is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U detector -d misinformation -c "SELECT 1"
```

### Disk Full

```bash
# Check space
df -h

# Find large items
du -sh /*

# Clean up Docker
docker system prune -a

# Remove old backups
rm /backups/detector/old_backup.sql.gz
```

### High Memory Usage

```bash
# See memory usage
docker stats

# Restart services
docker-compose restart

# Reduce workers temporarily
docker-compose down
docker-compose up -d --scale visual-worker=1
```

---

## Backup & Recovery

### Restore from Backup

```bash
# List backups
ls -lh /backups/detector/

# Stop application
docker-compose down

# Restore database
gunzip < /backups/detector/db_20240101_020000.sql.gz | \
  docker-compose exec -T postgres psql -U detector misinformation

# Restore uploads
cd /backups/detector
tar -xzf uploads_20240101_020000.tar.gz
# Files go back to uploads/

# Start application
docker-compose up -d
```

---

## Security Tips

### Change Default Passwords

```bash
# The .env file has auto-generated passwords
# But if you want to change them:

# Generate new password
NEW_PASS=$(openssl rand -base64 16)

# Update .env
sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PASS/" .env

# Restart services
docker-compose down
docker-compose up -d
```

### Restrict Access

```bash
# Only allow specific IPs
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp       # SSH
sudo ufw allow 80/tcp       # HTTP
sudo ufw allow 443/tcp      # HTTPS
sudo ufw enable

# Check firewall status
sudo ufw status
```

### Monitor Access

```bash
# View Nginx access logs
tail -f /var/log/nginx/access.log

# View Nginx errors
tail -f /var/log/nginx/error.log
```

---

## Next Steps

1. **Add Custom Domain** - Point DNS to your VM IP
2. **Setup Monitoring** - Use Uptime Robot or Healthchecks.io
3. **Integrate with Tools** - Add API keys for external integrations
4. **Scale Up** - Add more workers or upgrade VM
5. **Add Models** - Download and integrate detection models
6. **Customize** - Modify config/settings.py for your use case

---

## Support & Documentation

- **Full Deployment Guide:** See DEPLOYMENT_GUIDE.md
- **Quick Reference:** See DEPLOYMENT_QUICK_REFERENCE.md
- **API Documentation:** See README.md
- **Implementation Details:** See IMPLEMENTATION_SUMMARY.md

---

## Summary

You now have a production-ready misinformation detection system running on a $5-20/month VM!

**What you have:**
- ✓ FastAPI inference server on port 8000
- ✓ PostgreSQL database with persistent storage
- ✓ Redis queue for task processing
- ✓ Nginx reverse proxy on port 80/443
- ✓ Daily automated backups
- ✓ SSL certificate (optional)
- ✓ Health monitoring

**What to do next:**
- [ ] Download models and integrate them
- [ ] Test with real media files
- [ ] Setup monitoring and alerting
- [ ] Scale workers based on load
- [ ] Document your deployment

Enjoy! 🎉
