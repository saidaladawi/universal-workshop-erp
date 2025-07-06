# Production Deployment and Monitoring Infrastructure

This directory contains comprehensive production deployment configurations, monitoring setup, and infrastructure automation for the ERPNext/Frappe Workshop Management System.

## Directory Structure

```
deployment/
├── README.md                 # This file
├── docker/                   # Docker containerization
│   ├── Dockerfile.production # Production-optimized Dockerfile
│   ├── docker-compose.prod.yml # Production Docker Compose
│   └── nginx.conf           # Nginx configuration
├── kubernetes/              # Kubernetes orchestration
│   ├── namespace.yaml       # Namespace configuration
│   ├── configmap.yaml       # Configuration management
│   ├── secrets.yaml         # Secrets management
│   ├── deployment.yaml      # Application deployment
│   ├── service.yaml         # Service definitions
│   ├── ingress.yaml         # Ingress configuration
│   ├── pvc.yaml            # Persistent volume claims
│   └── helm/               # Helm charts
├── monitoring/              # Monitoring and alerting
│   ├── prometheus/          # Prometheus configuration
│   ├── grafana/            # Grafana dashboards
│   ├── alertmanager/       # Alert manager setup
│   └── loki/               # Log aggregation
├── ci-cd/                  # CI/CD pipeline configurations
│   ├── github-actions/     # GitHub Actions workflows
│   ├── gitlab-ci/          # GitLab CI configurations
│   └── jenkins/            # Jenkins pipeline scripts
└── scripts/                # Deployment and utility scripts
    ├── deploy.sh           # Main deployment script
    ├── backup.sh           # Backup automation
    ├── migrate.sh          # Database migration
    └── rollback.sh         # Rollback procedures
```

## Features

### 🐳 Docker Containerization
- Production-optimized Docker images
- Multi-stage builds for smaller images
- Security hardening and non-root execution
- Health checks and proper signal handling

### ☸️ Kubernetes Orchestration
- High availability deployment configurations
- Auto-scaling and load balancing
- Rolling updates with zero downtime
- Resource management and limits

### 📊 Monitoring & Alerting
- Prometheus metrics collection
- Grafana dashboards for visualization
- AlertManager for notification routing
- Loki for centralized log aggregation
- Custom ERPNext/Frappe metrics

### 🔄 CI/CD Pipeline
- Automated testing and deployment
- Multi-environment support (dev/staging/prod)
- Rollback capabilities
- Security scanning integration

### 🔒 Security & Compliance
- SSL/TLS certificate management
- Secrets encryption and rotation
- Network policies and RBAC
- Security scanning and hardening

### 💾 Data Management
- Automated backup strategies
- Database migration procedures
- Persistent storage configurations
- Disaster recovery planning

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Kubernetes cluster (minikube/kind for local, managed service for production)
- Helm 3.x
- kubectl configured

### Local Development
```bash
# Start local development environment
cd deployment/docker
docker-compose -f docker-compose.dev.yml up -d
```

### Production Deployment
```bash
# Deploy to Kubernetes
cd deployment/kubernetes
kubectl apply -f namespace.yaml
kubectl apply -f .

# Or use Helm
helm install workshop-erp ./helm/workshop-erp
```

### Monitoring Setup
```bash
# Deploy monitoring stack
cd deployment/monitoring
kubectl apply -f prometheus/
kubectl apply -f grafana/
kubectl apply -f alertmanager/
```

## Configuration

### Environment Variables
- `FRAPPE_SITE_NAME` - Site name for ERPNext
- `DB_HOST` - Database host
- `DB_PASSWORD` - Database password
- `REDIS_URL` - Redis connection URL
- `ADMIN_PASSWORD` - Administrator password

### Secrets Management
All sensitive data should be managed through Kubernetes secrets or external secret management systems like HashiCorp Vault.

### SSL Certificates
Use cert-manager for automatic SSL certificate provisioning and renewal with Let's Encrypt.

## Monitoring

### Key Metrics
- Application response time and throughput
- Database performance and query latency
- Redis performance and memory usage
- System resource utilization
- Workshop-specific metrics (appointments, services, inventory)

### Dashboards
- ERPNext Application Dashboard
- Infrastructure Monitoring
- Workshop Business Metrics
- Security and Compliance Dashboard

### Alerts
- High error rates
- Performance degradation
- Resource exhaustion
- Security incidents
- Backup failures

## Backup Strategy

### Automated Backups
- Daily database backups with 30-day retention
- File storage backups with versioning
- Configuration backups
- Offsite backup replication

### Recovery Procedures
- Point-in-time recovery capabilities
- Disaster recovery runbooks
- Regular recovery testing

## Security

### Security Hardening
- Container security scanning
- Network segmentation
- Access control and RBAC
- Audit logging
- Vulnerability management

### Compliance
- Data protection and privacy
- Audit trail maintenance
- Compliance reporting
- Security monitoring

## Maintenance

### Updates and Patches
- Regular security updates
- Automated dependency updates
- Canary deployments for testing
- Rollback procedures

### Performance Optimization
- Database query optimization
- Caching strategy tuning
- Resource scaling recommendations
- Performance monitoring

## Support

### Troubleshooting
- Common issues and solutions
- Log aggregation and analysis
- Performance debugging
- Health check endpoints

### Documentation
- Deployment guides
- Operational runbooks
- Architecture diagrams
- API documentation

## Contributing

1. Follow infrastructure as code best practices
2. Test all changes in staging environment
3. Document configuration changes
4. Follow security guidelines
5. Update monitoring and alerting as needed

---

**Note:** This infrastructure is designed for production-grade deployment of ERPNext/Frappe Workshop Management System with high availability, security, and monitoring capabilities.
