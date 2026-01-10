# 🚀 Deployment Guide - Yield Guard Bot

Complete guide for deploying your DeFi Treasury Management Platform to production.

---

## 📋 Table of Contents

1. [Streamlit Cloud (Recommended - FREE)](#1-streamlit-cloud-recommended)
2. [Docker Deployment](#2-docker-deployment)
3. [Railway](#3-railway)
4. [Render](#4-render)
5. [AWS/GCP/Azure](#5-cloud-providers)
6. [Self-Hosted VPS](#6-self-hosted-vps)

---

## 1. Streamlit Cloud (Recommended) ☁️

**Best for:** Quick deployment, free hosting, no DevOps required

### Advantages
- ✅ **FREE** - Unlimited public apps
- ✅ **Zero configuration** - Just connect GitHub
- ✅ **Auto-deploy** - Updates on every git push
- ✅ **SSL included** - Automatic HTTPS
- ✅ **Resource limits** - 1GB RAM, 1 CPU (sufficient for this app)

### Prerequisites
- GitHub account
- Repository pushed to GitHub

### Step-by-Step Deployment

#### Step 1: Prepare Your Repository

```bash
# Make sure all changes are committed
git status

# Push to GitHub
git push origin main
```

#### Step 2: Create Streamlit Cloud Account

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Authorize Streamlit Cloud to access your repositories

#### Step 3: Deploy App

1. Click **"New app"**
2. Select your repository: `Enricrypto/yield-guard-bot`
3. Branch: `main`
4. Main file path: `app_enhanced.py`
5. Click **"Deploy!"**

#### Step 4: Configuration (Optional)

Create `.streamlit/config.toml` in your repo:

```toml
[theme]
primaryColor = "#00d4ff"
backgroundColor = "#0f1419"
secondaryBackgroundColor = "#1a1f26"
textColor = "#ffffff"
font = "sans serif"

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

#### Step 5: Add Secrets (if needed)

In Streamlit Cloud dashboard:
1. Go to app settings (⚙️)
2. Click "Secrets"
3. Add environment variables:

```toml
# .streamlit/secrets.toml format
DATABASE_PATH = "data/simulations.db"

[api_keys]
aave = "your_aave_api_key"
compound = "your_compound_api_key"
```

### Your App URL
```
https://yield-guard-bot-your-username.streamlit.app
```

---

## 2. Docker Deployment 🐳

**Best for:** Consistent environments, easy scaling, self-hosting

### Create Dockerfile

```dockerfile
# Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Initialize database
RUN python -c "from src.database.db import DatabaseManager; db = DatabaseManager(); db.init_db()"

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run Streamlit
ENTRYPOINT ["streamlit", "run", "app_enhanced.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Create docker-compose.yml

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_PATH=/app/data/simulations.db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Create .dockerignore

```
# .dockerignore
.git
.github
.venv
venv
__pycache__
*.pyc
*.pyo
*.pyd
.pytest_cache
.coverage
htmlcov
*.md
!README.md
.env
data/
*.db
app_enhanced.py.backup
test_*.py
```

### Build and Run

```bash
# Build Docker image
docker build -t yield-guard-bot .

# Run container
docker run -p 8501:8501 -v $(pwd)/data:/app/data yield-guard-bot

# Or use docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Push to Docker Hub

```bash
# Login
docker login

# Tag image
docker tag yield-guard-bot yourusername/yield-guard-bot:latest

# Push
docker push yourusername/yield-guard-bot:latest
```

---

## 3. Railway 🚂

**Best for:** Easy deployment, free tier, automatic scaling

### Advantages
- ✅ **$5/month free credit**
- ✅ **Automatic HTTPS**
- ✅ **GitHub integration**
- ✅ **Environment variables UI**
- ✅ **Custom domains**

### Deployment Steps

1. **Go to [railway.app](https://railway.app)**
2. **Sign in with GitHub**
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose `yield-guard-bot` repository**
6. **Railway auto-detects Python**

### Configure Railway

Create `railway.toml`:

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "streamlit run app_enhanced.py --server.port=$PORT --server.address=0.0.0.0"
healthcheckPath = "/_stcore/health"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### Add Environment Variables

In Railway dashboard:
- `PORT` = 8501 (auto-set)
- `DATABASE_PATH` = data/simulations.db
- Any API keys needed

### Your App URL
```
https://yield-guard-bot-production.up.railway.app
```

---

## 4. Render 🎨

**Best for:** Free tier, simple deployment, persistent storage

### Advantages
- ✅ **FREE tier** (with limitations)
- ✅ **Automatic SSL**
- ✅ **Custom domains**
- ✅ **Persistent disks** (paid feature)

### Deployment Steps

1. **Go to [render.com](https://render.com)**
2. **Sign up/Login**
3. **Click "New +"**
4. **Select "Web Service"**
5. **Connect GitHub repo**

### Configure Web Service

```yaml
# render.yaml
services:
  - type: web
    name: yield-guard-bot
    env: python
    region: oregon
    plan: free
    buildCommand: pip install -r requirements.txt && python -c "from src.database.db import DatabaseManager; db = DatabaseManager(); db.init_db()"
    startCommand: streamlit run app_enhanced.py --server.port=$PORT --server.address=0.0.0.0
    envVars:
      - key: PYTHON_VERSION
        value: 3.12.0
      - key: DATABASE_PATH
        value: /var/data/simulations.db
    disk:
      name: data
      mountPath: /var/data
      sizeGB: 1
```

### Your App URL
```
https://yield-guard-bot.onrender.com
```

### Note on Free Tier
- ⚠️ Spins down after 15 minutes of inactivity
- ⚠️ Cold start takes ~30 seconds
- ✅ Upgrade to paid ($7/month) for always-on

---

## 5. Cloud Providers (AWS/GCP/Azure) ☁️

**Best for:** Enterprise deployment, maximum control, scaling

### Option A: AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.12 yield-guard-bot

# Create environment
eb create yield-guard-bot-env

# Deploy
eb deploy

# Open in browser
eb open
```

Create `.ebextensions/python.config`:

```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: application:application
  aws:elasticbeanstalk:application:environment:
    STREAMLIT_SERVER_PORT: 8501
```

### Option B: AWS ECS (Docker)

1. Push Docker image to ECR
2. Create ECS cluster
3. Define task definition
4. Create service
5. Configure load balancer

### Option C: Google Cloud Run

```bash
# Build and deploy
gcloud run deploy yield-guard-bot \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## 6. Self-Hosted VPS 🖥️

**Best for:** Complete control, custom configuration

### Prerequisites
- VPS with Ubuntu 22.04+ (DigitalOcean, Linode, Vultr)
- Domain name (optional)
- SSH access

### Step-by-Step Setup

#### Step 1: Initial Server Setup

```bash
# SSH into server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3.12 python3-pip nginx git certbot python3-certbot-nginx

# Create app user
adduser yieldguard
usermod -aG sudo yieldguard
su - yieldguard
```

#### Step 2: Clone and Setup Application

```bash
# Clone repository
git clone https://github.com/Enricrypto/yield-guard-bot.git
cd yield-guard-bot

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from src.database.db import DatabaseManager; db = DatabaseManager(); db.init_db()"
```

#### Step 3: Create Systemd Service

Create `/etc/systemd/system/yield-guard-bot.service`:

```ini
[Unit]
Description=Yield Guard Bot Streamlit App
After=network.target

[Service]
Type=simple
User=yieldguard
WorkingDirectory=/home/yieldguard/yield-guard-bot
Environment="PATH=/home/yieldguard/yield-guard-bot/.venv/bin"
ExecStart=/home/yieldguard/yield-guard-bot/.venv/bin/streamlit run app_enhanced.py --server.port=8501 --server.address=localhost
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable yield-guard-bot
sudo systemctl start yield-guard-bot
sudo systemctl status yield-guard-bot
```

#### Step 4: Configure Nginx Reverse Proxy

Create `/etc/nginx/sites-available/yield-guard-bot`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/yield-guard-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 5: SSL Certificate (HTTPS)

```bash
# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (already set up by certbot)
sudo certbot renew --dry-run
```

### Your App URL
```
https://your-domain.com
```

---

## 📊 Deployment Comparison

| Platform | Cost | Setup Time | Scaling | SSL | Custom Domain | Best For |
|----------|------|------------|---------|-----|---------------|----------|
| **Streamlit Cloud** | FREE | 5 min | Auto | ✅ | Limited | Quick demo, MVP |
| **Docker** | Varies | 30 min | Manual | Manual | ✅ | Flexibility |
| **Railway** | $5/mo | 10 min | Auto | ✅ | ✅ | Production MVP |
| **Render** | FREE/$7 | 15 min | Auto | ✅ | ✅ | Small projects |
| **AWS/GCP** | $$$ | 2-4 hours | Enterprise | ✅ | ✅ | Large scale |
| **VPS** | $5-20/mo | 1-2 hours | Manual | ✅ | ✅ | Full control |

---

## 🔒 Production Checklist

### Security
- [ ] Set up environment variables (no hardcoded secrets)
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable security headers
- [ ] Regular dependency updates

### Performance
- [ ] Enable caching (already implemented)
- [ ] Monitor resource usage
- [ ] Set up CDN (if needed)
- [ ] Optimize database queries
- [ ] Configure appropriate timeouts

### Monitoring
- [ ] Set up error tracking (Sentry)
- [ ] Configure uptime monitoring
- [ ] Set up log aggregation
- [ ] Create alerts for failures
- [ ] Monitor API rate limits

### Backup
- [ ] Automated database backups
- [ ] Version control for all code
- [ ] Document configuration
- [ ] Test restore procedures

---

## 🎯 Recommended Setup by Use Case

### Personal/Demo Use
**→ Streamlit Cloud (FREE)**
- Easiest setup
- No maintenance
- Perfect for showcasing

### Small Team/Startup
**→ Railway ($5-10/month)**
- Easy scaling
- Good developer experience
- Reasonable pricing

### Production/Business
**→ AWS/GCP or VPS ($20-50/month)**
- Full control
- Professional setup
- Custom domain
- Monitoring

### Enterprise
**→ AWS ECS/EKS or GCP Cloud Run**
- High availability
- Auto-scaling
- Security compliance
- Dedicated support

---

## 🚀 Quick Deploy Commands

### Streamlit Cloud
```bash
git push origin main
# Then deploy via web UI
```

### Docker
```bash
docker-compose up -d
```

### Railway
```bash
# Push to GitHub, auto-deploys
git push origin main
```

### Render
```bash
# Connect GitHub repo via web UI
```

### VPS
```bash
ssh user@server
cd yield-guard-bot
git pull
sudo systemctl restart yield-guard-bot
```

---

## 📞 Support & Troubleshooting

### Common Issues

**Issue: Database not found**
```bash
# Initialize database
python -c "from src.database.db import DatabaseManager; db = DatabaseManager(); db.init_db()"
```

**Issue: Port already in use**
```bash
# Change port in command
streamlit run app_enhanced.py --server.port=8502
```

**Issue: Module not found**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 🔄 Continuous Deployment

### GitHub Actions Auto-Deploy

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Railway
        run: |
          curl -X POST ${{ secrets.RAILWAY_WEBHOOK_URL }}
```

---

## 📚 Additional Resources

- [Streamlit Deployment Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Railway Documentation](https://docs.railway.app/)
- [Render Documentation](https://render.com/docs)
- [AWS Elastic Beanstalk](https://docs.aws.amazon.com/elasticbeanstalk/)

---

**Recommended for You:** Start with **Streamlit Cloud** (FREE) for immediate deployment, then migrate to **Railway** or **VPS** when you need more control.

---

*Last Updated: January 10, 2026*
