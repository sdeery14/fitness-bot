# Deployment Guide - AI-Powered Fitness Planner

**Version**: 1.0  
**Last Updated**: November 17, 2025

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Local Development Setup](#local-development-setup)
4. [Environment Configuration](#environment-configuration)
5. [Database Setup](#database-setup)
6. [Running with Docker](#running-with-docker)
7. [Production Deployment](#production-deployment)
8. [Monitoring & Health Checks](#monitoring--health-checks)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers deployment of the AI-Powered Fitness Planner application from local development through production. The application consists of:

- **Backend**: FastAPI (Python 3.12+)
- **Frontend**: Next.js 14+ (Node.js 20+)
- **Database**: PostgreSQL 15+
- **Cache/Queue**: Redis 7+
- **Background Workers**: Celery

**Deployment Options**:
- **Local Development**: Docker Compose (recommended)
- **Staging/Production**: AWS ECS with RDS/ElastiCache (recommended)
- **Alternative**: Kubernetes, DigitalOcean App Platform, Railway

---

## Prerequisites

### Required Software

**For Local Development**:
- **Docker Desktop 4.0+** (includes Docker Compose)
  - Download: https://www.docker.com/products/docker-desktop
  - Includes Docker Engine and Docker Compose
- **Git** for version control
- **VS Code** (recommended) with extensions:
  - Python, ESLint, Prettier, Docker

**For Manual Setup** (without Docker):
- **Python 3.12+** with pip and venv
- **Node.js 20+** with npm
- **PostgreSQL 15+** database server
- **Redis 7+** server

**For Production Deployment**:
- **AWS Account** with ECS/RDS/ElastiCache access
- **AWS CLI** configured with credentials
- **Docker** for building production images

### Required API Keys

Obtain the following API keys before deployment:

1. **OpenAI API Key**: https://platform.openai.com/api-keys
   - Required for AI agent functionality
   - Cost: ~$0.01-0.05 per conversation (GPT-4o)

2. **USDA FoodData Central API Key**: https://fdc.nal.usda.gov/api-key-signup.html
   - Free tier: 1000 requests/hour
   - Required for meal plan generation

---

## Local Development Setup

### Option 1: Docker Compose (Recommended)

**Step 1: Clone Repository**
```bash
git clone https://github.com/your-org/fitness-bot.git
cd fitness-bot
```

**Step 2: Configure Environment**
```bash
# Create backend .env file
cd backend
cp .env.example .env

# Edit .env with your API keys (see Environment Configuration section)
# Required variables:
# - OPENAI_API_KEY
# - USDA_API_KEY
# - JWT_SECRET
# - DATABASE_URL
# - REDIS_URL
```

**Step 3: Start All Services**
```bash
cd docker
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

**Step 4: Run Database Migrations**
```bash
# Backend migrations with Alembic
docker-compose exec backend alembic upgrade head
```

**Step 5: Access Application**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

**Step 6: Stop Services**
```bash
docker-compose down          # Stop containers
docker-compose down -v       # Stop and remove volumes (data loss!)
```

---

### Option 2: Manual Setup (Without Docker)

**Step 1: Install Dependencies**

Backend:
```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Frontend:
```bash
cd frontend
npm install
```

**Step 2: Start PostgreSQL and Redis**

Install and start PostgreSQL 15+:
```bash
# macOS (Homebrew):
brew install postgresql@15
brew services start postgresql@15

# Ubuntu/Debian:
sudo apt install postgresql-15
sudo systemctl start postgresql

# Windows:
# Download installer from https://www.postgresql.org/download/windows/
```

Install and start Redis:
```bash
# macOS (Homebrew):
brew install redis
brew services start redis

# Ubuntu/Debian:
sudo apt install redis-server
sudo systemctl start redis-server

# Windows:
# Download from https://redis.io/download or use WSL
```

**Step 3: Create Database**
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE fitness_bot;
CREATE USER fitness_bot WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE fitness_bot TO fitness_bot;
\q
```

**Step 4: Configure Environment Variables**
```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://fitness_bot:secure_password@localhost:5432/fitness_bot
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your_openai_key_here
USDA_API_KEY=your_usda_key_here
JWT_SECRET=your_secure_random_string_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENVIRONMENT=development
LOG_LEVEL=INFO
```

**Step 5: Run Database Migrations**
```bash
cd backend
alembic upgrade head
```

**Step 6: Start Services**

Terminal 1 - Backend:
```bash
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Celery Worker:
```bash
cd backend
celery -A src.workers.celery_app worker --loglevel=info
```

Terminal 3 - Frontend:
```bash
cd frontend
npm run dev
```

---

## Environment Configuration

### Backend Environment Variables (.env)

**Required Variables**:
```bash
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=fitness_bot
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/fitness_bot

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# OpenAI API
OPENAI_API_KEY=sk-proj-...your-key-here

# JWT Authentication
JWT_SECRET=your_64_character_random_string_here_use_secrets_token_hex(32)
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# USDA FoodData Central API
USDA_API_KEY=your_usda_key_here

# Application Settings
ENVIRONMENT=development  # development, staging, production
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
```

**Optional Variables**:
```bash
# Celery Configuration (defaults to REDIS_URL)
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Refresh Token Expiration
REFRESH_TOKEN_EXPIRE_DAYS=30
```

**Generating Secure JWT_SECRET**:
```bash
# Python method (recommended):
python -c "import secrets; print(secrets.token_hex(32))"

# Output: 64-character hex string
# Example: a1b2c3d4e5f6...
```

### Frontend Environment Variables

**Create `frontend/.env.local`**:
```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# NextAuth Configuration (for future social auth)
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_nextauth_secret_change_in_production
```

**Production Frontend (.env.production)**:
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
NEXTAUTH_URL=https://yourdomain.com
NEXTAUTH_SECRET=production_secure_secret_here
```

---

## Database Setup

### Initial Migration

After configuring environment variables, run migrations to create database schema:

```bash
# Using Docker Compose
docker-compose exec backend alembic upgrade head

# Manual setup
cd backend
alembic upgrade head
```

### Creating a New Migration

When you modify database models:

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Review the generated migration file in alembic/versions/
# Edit if needed, then apply:
alembic upgrade head
```

### Rollback Migration

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

### Seed Data (Optional)

Load initial exercise database and sample data:

```bash
# Using Docker Compose
docker-compose exec backend python -m src.scripts.seed_exercises

# Manual setup
cd backend
python -m src.scripts.seed_exercises
```

---

## Running with Docker

### Docker Compose Architecture

The `docker/docker-compose.yml` file defines 5 services:

1. **postgres**: PostgreSQL 15 database
2. **redis**: Redis 7 cache/message broker
3. **backend**: FastAPI application server
4. **celery_worker**: Background task processor
5. **frontend**: Next.js web application

### Docker Compose Commands

**Start all services**:
```bash
cd docker
docker-compose up -d
```

**View logs**:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery_worker
```

**Restart a service**:
```bash
docker-compose restart backend
docker-compose restart celery_worker
```

**Rebuild after code changes**:
```bash
# Rebuild all images
docker-compose build

# Rebuild specific service
docker-compose build backend

# Rebuild and restart
docker-compose up -d --build backend
```

**Execute commands in containers**:
```bash
# Run backend shell
docker-compose exec backend bash

# Run database migrations
docker-compose exec backend alembic upgrade head

# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d fitness_bot

# Access Redis CLI
docker-compose exec redis redis-cli
```

**Stop and clean up**:
```bash
# Stop containers (preserves data)
docker-compose down

# Stop and remove volumes (data loss!)
docker-compose down -v

# Remove all unused Docker resources
docker system prune -a
```

### Health Checks

Docker Compose includes health checks for dependencies:

- **PostgreSQL**: `pg_isready` check every 10 seconds
- **Redis**: `redis-cli ping` check every 10 seconds
- **Backend**: Depends on healthy postgres and redis

**Check service health**:
```bash
docker-compose ps

# Healthy output shows (healthy) status:
# NAME                  STATUS
# fitness-bot-db        Up (healthy)
# fitness-bot-redis     Up (healthy)
# fitness-bot-backend   Up
```

---

## Production Deployment

### AWS ECS Deployment (Recommended)

**Architecture Overview**:
```
Internet → ALB (HTTPS) → ECS Services → RDS PostgreSQL
                       ↓                 ElastiCache Redis
                     ECS Tasks (Backend, Frontend, Celery)
```

#### Step 1: Prerequisites

1. **AWS Account** with IAM user/role with permissions:
   - ECS (Fargate)
   - RDS
   - ElastiCache
   - ALB/Target Groups
   - VPC/Subnets
   - ECR (Container Registry)

2. **Install AWS CLI**:
```bash
# macOS
brew install awscli

# Windows
# Download from https://aws.amazon.com/cli/

# Configure credentials
aws configure
```

3. **Install ECS CLI** (optional):
```bash
# macOS
brew install amazon-ecs-cli
```

#### Step 2: Create RDS PostgreSQL Database

**Via AWS Console**:
1. Navigate to RDS → Create database
2. Choose PostgreSQL 15.x
3. Template: Production (or Dev/Test for staging)
4. Settings:
   - DB instance identifier: `fitness-bot-db`
   - Master username: `postgres`
   - Master password: (secure password)
5. Instance configuration:
   - Instance class: `db.t3.medium` (production) or `db.t3.micro` (staging)
6. Storage:
   - Allocated: 20 GB
   - Enable auto-scaling (max 100 GB)
7. Connectivity:
   - VPC: Choose your VPC
   - Public access: No
   - VPC security group: Create new (allow port 5432 from ECS tasks)
8. Additional configuration:
   - Initial database name: `fitness_bot`
   - Enable automated backups (7-day retention)
   - Enable encryption

**Via AWS CLI**:
```bash
aws rds create-db-instance \
  --db-instance-identifier fitness-bot-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.4 \
  --master-username postgres \
  --master-user-password YOUR_SECURE_PASSWORD \
  --allocated-storage 20 \
  --storage-encrypted \
  --vpc-security-group-ids sg-xxxxx \
  --db-subnet-group-name your-db-subnet-group \
  --backup-retention-period 7 \
  --no-publicly-accessible
```

#### Step 3: Create ElastiCache Redis Cluster

**Via AWS Console**:
1. Navigate to ElastiCache → Redis clusters → Create
2. Cluster mode: Disabled
3. Node type: `cache.t3.micro` (staging) or `cache.t3.medium` (production)
4. Number of replicas: 1 (for high availability)
5. Subnet group: Choose your VPC subnets
6. Security group: Allow port 6379 from ECS tasks

**Via AWS CLI**:
```bash
aws elasticache create-replication-group \
  --replication-group-id fitness-bot-redis \
  --replication-group-description "Redis for fitness bot" \
  --engine redis \
  --cache-node-type cache.t3.medium \
  --num-cache-clusters 2 \
  --cache-subnet-group-name your-subnet-group \
  --security-group-ids sg-xxxxx
```

#### Step 4: Build and Push Docker Images

**Create ECR Repositories**:
```bash
# Backend
aws ecr create-repository --repository-name fitness-bot/backend

# Frontend
aws ecr create-repository --repository-name fitness-bot/frontend
```

**Build and Push Images**:
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build backend
cd backend
docker build -t fitness-bot/backend:latest .

# Tag and push backend
docker tag fitness-bot/backend:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/fitness-bot/backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/fitness-bot/backend:latest

# Build and push frontend (similar steps)
cd ../frontend
docker build -t fitness-bot/frontend:latest .
docker tag fitness-bot/frontend:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/fitness-bot/frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/fitness-bot/frontend:latest
```

#### Step 5: Create ECS Task Definitions

**Backend Task Definition** (`backend-task-def.json`):
```json
{
  "family": "fitness-bot-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/fitness-bot/backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {"name": "DATABASE_URL", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "REDIS_URL", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "JWT_SECRET", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/fitness-bot-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**Register task definition**:
```bash
aws ecs register-task-definition --cli-input-json file://backend-task-def.json
```

#### Step 6: Create ECS Services

**Backend Service**:
```bash
aws ecs create-service \
  --cluster fitness-bot-cluster \
  --service-name backend \
  --task-definition fitness-bot-backend \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=backend,containerPort=8000"
```

**Celery Worker Service** (similar, without load balancer):
```bash
aws ecs create-service \
  --cluster fitness-bot-cluster \
  --service-name celery-worker \
  --task-definition fitness-bot-celery-worker \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=DISABLED}"
```

#### Step 7: Configure Application Load Balancer

1. **Create ALB** with HTTPS listener (port 443)
2. **Target Groups**:
   - Backend: Port 8000, health check `/health`
   - Frontend: Port 3000, health check `/`
3. **SSL Certificate**: Use ACM (AWS Certificate Manager)
4. **Routing Rules**:
   - `/api/*` → Backend target group
   - `/*` → Frontend target group

#### Step 8: Run Database Migrations

**One-time task**:
```bash
aws ecs run-task \
  --cluster fitness-bot-cluster \
  --task-definition fitness-bot-backend \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --overrides '{"containerOverrides":[{"name":"backend","command":["alembic","upgrade","head"]}]}'
```

#### Step 9: Configure Auto-Scaling

**Backend auto-scaling**:
```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/fitness-bot-cluster/backend \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# CPU-based scaling policy
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/fitness-bot-cluster/backend \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

**scaling-policy.json**:
```json
{
  "TargetValue": 70.0,
  "PredefinedMetricSpecification": {
    "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
  },
  "ScaleInCooldown": 300,
  "ScaleOutCooldown": 60
}
```

---

### Alternative: Kubernetes Deployment

**Prerequisites**:
- Kubernetes cluster (EKS, GKE, AKS, or self-hosted)
- kubectl configured
- Helm (optional, for package management)

**Kubernetes manifests** (example backend deployment):

```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fitness-bot-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: <registry>/fitness-bot/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: fitness-bot-secrets
              key: database-url
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 500m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: backend
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
```

**Apply manifests**:
```bash
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f celery-deployment.yaml
kubectl apply -f ingress.yaml
```

---

## Monitoring & Health Checks

### Health Check Endpoints

**Backend**:
- `/health`: Basic liveness check (returns 200 OK)
- `/health/ready`: Readiness check (verifies DB and Redis connectivity)

**Example**:
```bash
curl http://localhost:8000/health
# Response: {"status": "healthy"}

curl http://localhost:8000/health/ready
# Response: {"status": "ready", "database": "connected", "redis": "connected"}
```

### Application Logs

**Docker Compose**:
```bash
# View all logs
docker-compose logs -f

# Filter by service
docker-compose logs -f backend | grep ERROR
```

**AWS ECS**:
- Logs automatically sent to CloudWatch Logs
- Log group: `/ecs/fitness-bot-backend`
- Use CloudWatch Insights for queries

**Example CloudWatch Insights query**:
```
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

### Metrics to Monitor

**Application Metrics**:
- Request rate (requests/sec)
- Response latency (p50, p95, p99)
- Error rate (4xx, 5xx responses)
- AI agent response time
- Database query performance

**Infrastructure Metrics**:
- CPU utilization (ECS tasks)
- Memory utilization
- Database connections
- Redis memory usage
- Celery queue length

**Setup CloudWatch Alarms**:
```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name backend-high-error-rate \
  --alarm-description "Alert when error rate > 5%" \
  --metric-name 5XXError \
  --namespace AWS/ApplicationELB \
  --statistic Average \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

---

## Backup & Recovery

### Database Backups

**Automated RDS Backups**:
- Enabled by default with 7-day retention
- Daily automated snapshots during backup window
- Point-in-time recovery supported

**Manual Snapshot**:
```bash
# Create snapshot
aws rds create-db-snapshot \
  --db-instance-identifier fitness-bot-db \
  --db-snapshot-identifier fitness-bot-manual-$(date +%Y%m%d)

# List snapshots
aws rds describe-db-snapshots \
  --db-instance-identifier fitness-bot-db
```

**Restore from Snapshot**:
```bash
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier fitness-bot-db-restored \
  --db-snapshot-identifier fitness-bot-manual-20250117
```

### Redis Backup

**ElastiCache Automatic Backups**:
- Configure backup retention period (1-35 days)
- Daily backups during maintenance window

**Manual Backup**:
```bash
aws elasticache create-snapshot \
  --replication-group-id fitness-bot-redis \
  --snapshot-name redis-backup-$(date +%Y%m%d)
```

### Application Data Export

**User data export** (GDPR compliance):
```bash
# Run export script
docker-compose exec backend python -m src.scripts.export_user_data --user-id <uuid>
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Symptoms**: Backend fails to start, logs show connection errors

**Checks**:
```bash
# Verify DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql+asyncpg://user:pass@host:port/dbname

# Test PostgreSQL connectivity
docker-compose exec backend pg_isready -h postgres -U postgres

# Check PostgreSQL logs
docker-compose logs postgres
```

**Solutions**:
- Verify PostgreSQL container is running and healthy
- Check DATABASE_URL includes correct credentials
- Ensure database `fitness_bot` exists
- For RDS: Verify security group allows ECS task IPs on port 5432

#### 2. Redis Connection Failed

**Symptoms**: Backend starts but caching/sessions don't work

**Checks**:
```bash
# Test Redis connectivity
docker-compose exec redis redis-cli ping
# Expected: PONG

# Check Redis URL
echo $REDIS_URL
# Should be: redis://redis:6379/0
```

**Solutions**:
- Verify Redis container is running
- Check REDIS_URL format
- For ElastiCache: Verify security group and endpoint

#### 3. OpenAI API Errors

**Symptoms**: AI conversations fail, "Invalid API key" errors

**Checks**:
```bash
# Verify API key is set
docker-compose exec backend printenv OPENAI_API_KEY

# Test API key manually
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Solutions**:
- Verify OPENAI_API_KEY is correct and active
- Check OpenAI account has credits
- Review rate limits (https://platform.openai.com/account/limits)

#### 4. Frontend Can't Connect to Backend

**Symptoms**: API calls fail, CORS errors

**Checks**:
```bash
# Check backend is accessible
curl http://localhost:8000/health

# Verify NEXT_PUBLIC_API_URL
docker-compose exec frontend printenv NEXT_PUBLIC_API_URL
# Should be: http://localhost:8000/api/v1
```

**Solutions**:
- Verify backend is running on correct port
- Check NEXT_PUBLIC_API_URL matches backend URL
- For production: Ensure ALB routing is configured correctly

#### 5. Celery Workers Not Processing Tasks

**Symptoms**: Background tasks stuck, schedule not updating

**Checks**:
```bash
# Check Celery worker logs
docker-compose logs celery_worker

# Inspect Redis queue
docker-compose exec redis redis-cli llen celery
```

**Solutions**:
- Verify Celery worker is running
- Check CELERY_BROKER_URL and CELERY_RESULT_BACKEND
- Restart worker: `docker-compose restart celery_worker`

#### 6. Database Migrations Failed

**Symptoms**: Alembic errors, schema mismatch

**Checks**:
```bash
# Check current migration version
docker-compose exec backend alembic current

# Check migration history
docker-compose exec backend alembic history
```

**Solutions**:
```bash
# Revert one migration
docker-compose exec backend alembic downgrade -1

# Reapply migrations
docker-compose exec backend alembic upgrade head

# If completely broken, reset database (data loss!):
docker-compose down -v
docker-compose up -d postgres redis
docker-compose exec backend alembic upgrade head
```

### Performance Issues

#### High Memory Usage

**Check container memory**:
```bash
docker stats

# Expected limits (per docker-compose.yml):
# backend: ~1GB
# celery_worker: ~1GB
# frontend: ~512MB
```

**Solutions**:
- Increase container memory limits in docker-compose.yml
- For ECS: Increase task memory allocation
- Review slow queries causing memory spikes

#### Slow AI Responses

**Symptoms**: Conversations take >30 seconds

**Checks**:
- Verify parallel agent execution is working
- Check OpenAI API status (https://status.openai.com)
- Review AI agent logs for timeouts

**Solutions**:
- Switch to GPT-4o-mini for faster responses (lower quality)
- Increase agent timeout limits
- Implement request caching for similar queries

### Getting Help

**Resources**:
- **Documentation**: `backend/docs/` directory
- **GitHub Issues**: Report bugs and request features
- **Community**: Discord/Slack (if available)

**When reporting issues, include**:
1. Error messages from logs
2. Environment (local/staging/production)
3. Steps to reproduce
4. Expected vs actual behavior

---

## Security Checklist

**Before Production Deployment**:

- [ ] Change all default passwords (PostgreSQL, Redis)
- [ ] Generate secure JWT_SECRET (64+ characters)
- [ ] Use AWS Secrets Manager for sensitive environment variables
- [ ] Enable SSL/TLS for all connections (database, Redis, API)
- [ ] Configure firewall rules (security groups) restrictively
- [ ] Enable RDS encryption at rest
- [ ] Enable CloudWatch logging for all services
- [ ] Set up monitoring alerts for errors and performance
- [ ] Configure automated backups (database, Redis)
- [ ] Review and limit IAM permissions
- [ ] Enable multi-factor authentication for AWS root account
- [ ] Scan Docker images for vulnerabilities
- [ ] Implement rate limiting on API endpoints
- [ ] Review CORS settings (restrict to production domain)

---

## Additional Resources

- **Architecture Documentation**: `backend/docs/architecture.md`
- **API Documentation**: `backend/docs/api-guide.md`
- **External Integrations**: `backend/docs/external-integrations.md`
- **AWS ECS Guide**: https://docs.aws.amazon.com/ecs/
- **Docker Compose Reference**: https://docs.docker.com/compose/

---

**Last Updated**: November 17, 2025  
**Version**: 1.0  
**Maintained by**: Fitness Bot Development Team
