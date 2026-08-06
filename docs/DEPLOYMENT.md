# Production Deployment Guide

This document provides instructions for deploying the AI Classroom Assistant platform in production environments.

---

## 1. Production Docker Compose Deployment

```bash
# Clone production branch
git clone https://github.com/your-org/ai-classroom-assistant.git -b main
cd ai-classroom-assistant

# Create production environment configuration
cp .env.production .env

# Build and launch production containers
docker-compose -f docker-compose.yml up --build -d
```

---

## 2. Nginx SSL Reverse Proxy Setup

Place SSL certificates under `/etc/ssl/certs/` and configure Nginx:

```nginx
server {
    listen 443 ssl http2;
    server_name classroom.yourdomain.com;

    ssl_certificate /etc/ssl/certs/fullchain.pem;
    ssl_certificate_key /etc/ssl/certs/privkey.pem;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
