#!/bin/bash
# Deploy to AWS ECS

set -e

CLUSTER=${1:-detector}
SERVICE=${2:-detector-api}
REGION=${3:-us-east-1}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🚀 Deploying to AWS ECS"
echo "======================="
echo "Cluster: $CLUSTER"
echo "Service: $SERVICE"
echo "Region: $REGION"
echo "AWS Account: $AWS_ACCOUNT_ID"
echo ""

# Create ECR repository
echo "Creating ECR repository..."
aws ecr create-repository \
  --repository-name misinformation-detector \
  --region $REGION \
  2>/dev/null || echo "Repository already exists"

# Login to ECR
echo "Logging in to ECR..."
aws ecr get-login-password --region $REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Build and push image
echo "Building and pushing Docker image..."
ECR_REPO="$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/misinformation-detector"

docker build -t $ECR_REPO:latest -f Dockerfile .
docker push $ECR_REPO:latest

echo "✓ Image pushed to $ECR_REPO:latest"

# Create RDS PostgreSQL
echo ""
echo "Creating RDS PostgreSQL..."
DB_PASS=$(openssl rand -base64 16)

aws rds create-db-instance \
  --db-instance-identifier detector-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 16.2 \
  --master-username detector \
  --master-user-password "$DB_PASS" \
  --allocated-storage 50 \
  --storage-type gp2 \
  --region $REGION \
  2>/dev/null || echo "Database already exists"

# Create ElastiCache Redis
echo "Creating ElastiCache Redis..."
REDIS_PASS=$(openssl rand -base64 16)

aws elasticache create-cache-cluster \
  --cache-cluster-id detector-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-nodes 1 \
  --region $REGION \
  2>/dev/null || echo "Redis cluster already exists"

# Create CloudWatch Log Group
echo "Creating CloudWatch Log Group..."
aws logs create-log-group \
  --log-group-name /ecs/detector \
  --region $REGION \
  2>/dev/null || echo "Log group already exists"

# Get RDS endpoint (wait a bit for it to be available)
echo ""
echo "Waiting for RDS to be available..."
sleep 10

RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier detector-db \
  --region $REGION \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

echo "RDS Endpoint: $RDS_ENDPOINT"

# Get Redis endpoint
REDIS_ENDPOINT=$(aws elasticache describe-cache-clusters \
  --cache-cluster-id detector-redis \
  --region $REGION \
  --show-cache-node-info \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' \
  --output text)

echo "Redis Endpoint: $REDIS_ENDPOINT"

# Create ECS Cluster
echo ""
echo "Creating ECS Cluster..."
aws ecs create-cluster --cluster-name $CLUSTER --region $REGION 2>/dev/null || \
  echo "Cluster already exists"

# Register Task Definition
echo "Registering ECS Task Definition..."
cat > /tmp/task-definition.json <<EOF
{
  "family": "detector-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "$ECR_REPO:latest",
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
          "name": "LOG_LEVEL",
          "value": "info"
        },
        {
          "name": "DATABASE_URL",
          "value": "postgresql://detector:$DB_PASS@$RDS_ENDPOINT:5432/misinformation"
        },
        {
          "name": "REDIS_URL",
          "value": "redis://:$REDIS_PASS@$REDIS_ENDPOINT:6379"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/detector",
          "awslogs-region": "$REGION",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

aws ecs register-task-definition \
  --cli-input-json file:///tmp/task-definition.json \
  --region $REGION

# Create ALB Target Group
echo "Creating ALB Target Group..."
aws elbv2 create-target-group \
  --name detector-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id $(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --region $REGION --query 'Vpcs[0].VpcId' --output text) \
  --target-type ip \
  --region $REGION \
  2>/dev/null || echo "Target group already exists"

# Create ALB
echo "Creating Application Load Balancer..."
LB_ARN=$(aws elbv2 create-load-balancer \
  --name detector-alb \
  --subnets $(aws ec2 describe-subnets --region $REGION --query 'Subnets[0:2].SubnetId' --output text) \
  --region $REGION \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text \
  2>/dev/null || \
  aws elbv2 describe-load-balancers \
    --names detector-alb \
    --region $REGION \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text)

# Create ECS Service
echo "Creating ECS Service..."
aws ecs create-service \
  --cluster $CLUSTER \
  --service-name $SERVICE \
  --task-definition detector-api \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$(aws ec2 describe-subnets --region $REGION --query 'Subnets[0:2].SubnetId' --output text | tr ' ' ',')],securityGroups=[$(aws ec2 describe-security-groups --filters "Name=group-name,Values=default" --region $REGION --query 'SecurityGroups[0].GroupId' --output text)],assignPublicIp=ENABLED}" \
  --region $REGION \
  2>/dev/null || echo "Service already exists"

# Print summary
echo ""
echo "=========================================="
echo "✓ ECS Deployment Complete!"
echo "=========================================="
echo ""
echo "Cluster: $CLUSTER"
echo "Service: $SERVICE"
echo "Region: $REGION"
echo ""
echo "RDS Database:"
echo "  Endpoint: $RDS_ENDPOINT"
echo "  Username: detector"
echo "  Password: (saved above - keep secure!)"
echo ""
echo "Redis Cache:"
echo "  Endpoint: $REDIS_ENDPOINT"
echo "  Password: (saved above - keep secure!)"
echo ""
echo "ECR Repository: $ECR_REPO"
echo ""
echo "View service status:"
echo "  aws ecs describe-services --cluster $CLUSTER --services $SERVICE --region $REGION"
echo ""
echo "View logs:"
echo "  aws logs tail /ecs/detector --follow --region $REGION"
echo ""
echo "Scale service:"
echo "  aws ecs update-service --cluster $CLUSTER --service $SERVICE --desired-count 5 --region $REGION"
echo ""
echo "Delete service:"
echo "  aws ecs delete-service --cluster $CLUSTER --service $SERVICE --force --region $REGION"
echo ""
