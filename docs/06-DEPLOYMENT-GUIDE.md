# Deployment Guide

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Docker Deployment](#docker-deployment)
3. [AWS Deployment](#aws-deployment)
4. [Azure Deployment](#azure-deployment)
5. [Production Checklist](#production-checklist)
6. [Monitoring & Maintenance](#monitoring--maintenance)

## Local Development Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 15
- Redis 7
- Git

### Backend Setup

```bash
# Clone repository
git clone https://github.com/yourname/teamflow-ai.git
cd teamflow-ai/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your configuration

# Initialize database
alembic upgrade head

# Run development server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Create .env.local
cp .env.example .env.local
# Edit .env.local with your configuration

# Run development server
npm run dev
```

### Database Setup

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE teamflow_ai;

# Connect to the database
\c teamflow_ai

# Run schema
\i database/schema.sql
```

## Docker Deployment

### Build and Run

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### Services

- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/api/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **ChromaDB**: http://localhost:8001

### Environment Configuration

Create `.env` file in project root:

```bash
# Database
DB_USER=postgres
DB_PASSWORD=secure_password
DB_NAME=teamflow_ai
DB_PORT=5432

# API
API_PORT=8000
FRONTEND_PORT=3000

# Keys
OPENAI_API_KEY=your_key
GITHUB_CLIENT_ID=your_id
GITHUB_CLIENT_SECRET=your_secret
SECRET_KEY=your_secret_key

# Feature Flags
DEBUG=false
ENABLE_GRAPHRAG=false
```

## AWS Deployment

### EC2 Setup

```bash
# Connect to EC2 instance
ssh -i your-key.pem ec2-user@your-instance-ip

# Install Docker
sudo yum update -y
sudo yum install docker -y
sudo systemctl start docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
git clone https://github.com/yourname/teamflow-ai.git
cd teamflow-ai

# Deploy
docker-compose up -d
```

### RDS Configuration

```bash
# Create PostgreSQL database
aws rds create-db-instance \
  --db-instance-identifier teamflow-ai-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password YOUR_PASSWORD \
  --allocated-storage 20

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://admin:password@teamflow-ai-db.xxx.rds.amazonaws.com:5432/teamflow_ai
```

### ElastiCache (Redis)

```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id teamflow-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0

# Update REDIS_URL
REDIS_URL=redis://teamflow-redis.xxx.ng.0001.useast1.cache.amazonaws.com:6379
```

### S3 Configuration

```bash
# Create bucket for file storage
aws s3 mb s3://teamflow-ai-storage

# Update .env
AWS_S3_BUCKET=teamflow-ai-storage
AWS_REGION=us-east-1
```

## Azure Deployment

### Container Registry Setup

```bash
# Login to Azure
az login

# Create resource group
az group create --name teamflow-rg --location eastus

# Create container registry
az acr create --resource-group teamflow-rg \
  --name teamflowareg --sku Basic

# Build and push images
docker build -f docker/Dockerfile.backend -t teamflowareg.azurecr.io/backend:latest .
docker build -f frontend/Dockerfile -t teamflowareg.azurecr.io/frontend:latest .

az acr login --name teamflowareg
docker push teamflowareg.azurecr.io/backend:latest
docker push teamflowareg.azurecr.io/frontend:latest
```

### App Service Deployment

```bash
# Create app service plan
az appservice plan create \
  --name teamflow-plan \
  --resource-group teamflow-rg \
  --sku B2

# Create app service
az webapp create \
  --resource-group teamflow-rg \
  --plan teamflow-plan \
  --name teamflow-app \
  --deployment-container-image-name teamflowareg.azurecr.io/backend:latest
```

### Azure Database for PostgreSQL

```bash
# Create PostgreSQL server
az postgres server create \
  --resource-group teamflow-rg \
  --name teamflow-db \
  --admin-user admin \
  --admin-password YOUR_PASSWORD \
  --sku-name B_Gen5_1
```

## Production Checklist

### Security

- [ ] Change all default passwords
- [ ] Enable HTTPS/TLS
- [ ] Setup firewall rules
- [ ] Enable database encryption
- [ ] Rotate API keys regularly
- [ ] Setup SSH key pairs
- [ ] Enable rate limiting
- [ ] Setup CORS properly
- [ ] Use secrets management (AWS Secrets Manager, Azure Key Vault)
- [ ] Enable VPC/VNet isolation

### Performance

- [ ] Setup CDN for static assets
- [ ] Enable database connection pooling
- [ ] Configure caching strategy
- [ ] Setup load balancing
- [ ] Enable database replication
- [ ] Optimize database indexes
- [ ] Setup query optimization

### Monitoring

- [ ] Setup CloudWatch/Application Insights
- [ ] Configure error tracking (Sentry)
- [ ] Setup health checks
- [ ] Configure alerting
- [ ] Setup log aggregation
- [ ] Enable performance monitoring

### Backup & Recovery

- [ ] Setup automated backups
- [ ] Test recovery procedures
- [ ] Document RTO/RPO
- [ ] Setup disaster recovery plan
- [ ] Document runbooks

### Compliance

- [ ] Enable audit logging
- [ ] Setup data retention policies
- [ ] Document data privacy
- [ ] Review compliance requirements
- [ ] Setup compliance monitoring

## Monitoring & Maintenance

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Readiness
curl http://localhost:8000/ready

# Frontend health
curl http://localhost:3000/api/health
```

### Database Maintenance

```bash
# Connect to PostgreSQL
psql -U postgres -d teamflow_ai

# Analyze tables
ANALYZE;

# Vacuum
VACUUM ANALYZE;

# Check index size
SELECT schemaname, tablename, indexname, pg_size_pretty(pg_relation_size(indexrelid)) 
FROM pg_indexes 
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Log Rotation

```bash
# Rotate logs
docker-compose exec backend logrotate -f /etc/logrotate.d/app

# View recent logs
docker-compose logs --tail 100 backend
```

### Scaling

```bash
# Scale backend services
docker-compose up -d --scale backend=3

# Update load balancer configuration to include all backend instances
```

### Updates & Patches

```bash
# Update dependencies
pip install --upgrade -r requirements.txt
npm update

# Rebuild containers
docker-compose build --no-cache

# Rolling deployment
docker-compose up -d --no-deps --build backend
```

## Troubleshooting

### Connection Issues

```bash
# Test database connection
psql -U postgres -h localhost -d teamflow_ai -c "SELECT 1"

# Test Redis connection
redis-cli ping

# Test API endpoint
curl -v http://localhost:8000/health
```

### Performance Issues

```bash
# Check container resource usage
docker stats

# Check database query performance
EXPLAIN ANALYZE SELECT ...;

# Monitor Redis memory
redis-cli INFO memory
```

### Common Issues

**Issue**: Database connection refused
```bash
# Solution: Ensure PostgreSQL is running and credentials are correct
docker-compose ps postgres
docker-compose logs postgres
```

**Issue**: API slow responses
```bash
# Solution: Check database performance and indexes
EXPLAIN ANALYZE SELECT ...;
VACUUM ANALYZE;
```

**Issue**: Vector search not working
```bash
# Solution: Verify ChromaDB is running and indexed
docker-compose ps chromadb
docker-compose logs chromadb
```

## Conclusion

This deployment guide covers:
- Local development setup
- Docker containerization
- Cloud deployment (AWS & Azure)
- Production best practices
- Monitoring and maintenance
- Troubleshooting

For production deployment, ensure all security checklist items are completed and monitoring is properly configured.
