# 🔒 Security & Production Deployment Guide

## Production Environment Setup

### 1. Environment Variables Configuration

**CRITICAL:** Before production deployment, copy and configure environment files:

```bash
# Copy production environment template
cp backend/.env.prod.example backend/.env.prod

# Edit with secure values
nano backend/.env.prod
```

### 2. Required Environment Variables

Update the following **MANDATORY** values in `.env.prod`:

```bash
# CRITICAL: Generate a secure 64-character random string
SECRET_KEY=your-secure-secret-key-here

# CRITICAL: Use a strong database password (min 16 chars, mixed case, numbers, symbols)
DATABASE_PASSWORD=YourStrongDatabasePassword123!

# CRITICAL: Update with your actual production domains
CORS_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]

# OPTIONAL: Redis password for additional security
REDIS_PASSWORD=YourRedisPassword123!
```

### 3. Docker Environment Variables

Create a `.env` file in the project root for Docker Compose:

```bash
# Database Configuration
DATABASE_USER=postgres
DATABASE_PASSWORD=YourStrongDatabasePassword123!
DATABASE_NAME=kkua_prod

# Redis Configuration (if using Redis auth)
REDIS_PASSWORD=YourRedisPassword123!

# Frontend URLs
FRONTEND_API_URL=https://api.yourdomain.com
FRONTEND_WS_URL=wss://api.yourdomain.com
```

## Security Checklist

### ✅ Pre-Deployment Checklist

- [ ] **Environment Files**: `.env.prod` created with secure values
- [ ] **Passwords Changed**: No default/example passwords used
- [ ] **HTTPS Configured**: SSL/TLS certificates installed
- [ ] **CORS Updated**: Only production domains allowed
- [ ] **Session Security**: `SESSION_SECURE=true` and `SESSION_SAMESITE=strict`
- [ ] **Database Security**: Strong passwords, restricted access
- [ ] **Secret Management**: No secrets in version control
- [ ] **Backup Strategy**: Database backup system configured
- [ ] **Monitoring**: Error tracking and logging configured

### 🚨 Security Features

1. **Session-based Authentication**: HTTP-only cookies with secure flags
2. **CSRF Protection**: Built-in CSRF middleware
3. **Rate Limiting**: API endpoint protection
4. **Security Headers**: HSTS, CSP, and other security headers
5. **Input Validation**: Pydantic schema validation
6. **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries

## Production Deployment Commands

### 1. Initial Setup
```bash
# Clone repository
git clone <repository-url>
cd kkua

# Create production environment files
cp backend/.env.prod.example backend/.env.prod
# Edit .env.prod with your secure values

# Create Docker environment file
cp .env.example .env
# Edit .env with your production values
```

### 2. Deploy with Docker Compose
```bash
# Build and start production services
docker-compose -f docker-compose.prod.yml up -d --build

# Verify services are running
docker-compose -f docker-compose.prod.yml ps

# Check logs for any errors
docker-compose -f docker-compose.prod.yml logs -f
```

### 3. Database Migration (if using Alembic)
```bash
# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Security Best Practices

### 🔑 Password Requirements
- **Minimum 16 characters**
- **Mixed case letters, numbers, and symbols**
- **Unique for each service**
- **Regular rotation (every 90 days)**

### 🛡️ Network Security
- **Firewall Configuration**: Only expose necessary ports (80, 443)
- **Database Access**: Restrict PostgreSQL port (5432) to internal network only
- **Redis Access**: Restrict Redis port (6379) to internal network only
- **Load Balancer**: Use reverse proxy (Nginx/Apache) for SSL termination

### 📊 Monitoring & Logging
- **Application Logs**: Monitor for security events
- **Error Tracking**: Set up error reporting (Sentry recommended)
- **Performance Monitoring**: Track API response times
- **Database Monitoring**: Monitor query performance and connections

## Backup Strategy

### Database Backups
```bash
# Create backup directory
mkdir -p backups

# Manual backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres kkua_prod > backups/backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup (add to cron)
0 2 * * * /path/to/your/project/scripts/backup_database.sh
```

### Example Backup Script
```bash
#!/bin/bash
# backup_database.sh
cd /path/to/your/kkua/project
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U postgres kkua_prod > backups/auto_backup_$(date +%Y%m%d_%H%M%S).sql

# Keep only last 7 days of backups
find backups/ -name "auto_backup_*.sql" -mtime +7 -delete
```

## Incident Response

### In Case of Security Incident
1. **Immediate Actions**:
   - Take affected services offline
   - Change all passwords and secret keys
   - Check logs for signs of compromise

2. **Investigation**:
   - Analyze access logs
   - Check for data integrity
   - Review recent deployments

3. **Recovery**:
   - Restore from clean backups if necessary
   - Update security configurations
   - Deploy with new secrets

4. **Post-Incident**:
   - Document lessons learned
   - Update security procedures
   - Consider additional monitoring

## Contact & Support

For security issues or questions:
- **Security Issues**: Create a private issue or contact maintainers directly
- **Emergency**: Follow your organization's incident response procedures

---

**⚠️ WARNING: Never commit `.env.prod`, `.env`, or any files containing production secrets to version control!**