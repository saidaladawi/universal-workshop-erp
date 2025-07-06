#!/usr/bin/env python3
"""
Environment Configuration Management for ERPNext/Frappe Deployments
Manages configuration across different environments (staging, production)
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class EnvironmentManager:
    def __init__(self, config_dir=None):
        if config_dir is None:
            # Use local config directory within the project
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config" / "environments"
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.environments = ["development", "staging", "production"]
    
    def create_base_config(self):
        """Create base configuration template"""
        base_config = {
            "database": {
                "host": "${DB_HOST}",
                "port": "${DB_PORT}",
                "name": "${DB_NAME}",
                "user": "${DB_USER}",
                "password": "${DB_PASSWORD}"
            },
            "redis": {
                "cache_host": "${REDIS_CACHE_HOST}",
                "cache_port": "${REDIS_CACHE_PORT}",
                "queue_host": "${REDIS_QUEUE_HOST}",
                "queue_port": "${REDIS_QUEUE_PORT}"
            },
            "mail": {
                "server": "${MAIL_SERVER}",
                "port": "${MAIL_PORT}",
                "use_tls": "${MAIL_USE_TLS}",
                "username": "${MAIL_USERNAME}",
                "password": "${MAIL_PASSWORD}"
            },
            "security": {
                "encryption_key": "${ENCRYPTION_KEY}",
                "secret_key": "${SECRET_KEY}",
                "csrf_protection": True,
                "session_timeout": 3600
            },
            "logging": {
                "level": "${LOG_LEVEL}",
                "file": "${LOG_FILE}",
                "max_size": "100MB",
                "backup_count": 5
            }
        }
        
        config_file = self.config_dir / "base_config.json"
        with open(config_file, 'w') as f:
            json.dump(base_config, f, indent=2)
        
        return config_file
    
    def create_environment_configs(self):
        """Create environment-specific configurations"""
        configs = {
            "development": {
                "debug": True,
                "auto_reload": True,
                "developer_mode": True,
                "database": {
                    "host": "localhost",
                    "port": 3306,
                    "name": "workshop_dev",
                    "pool_size": 5
                },
                "redis": {
                    "cache_host": "localhost",
                    "cache_port": 6379,
                    "queue_host": "localhost",
                    "queue_port": 6380
                },
                "security": {
                    "csrf_protection": False,
                    "session_timeout": 7200
                },
                "logging": {
                    "level": "DEBUG",
                    "file": "/var/log/frappe/development.log"
                }
            },
            "staging": {
                "debug": False,
                "auto_reload": False,
                "developer_mode": False,
                "database": {
                    "host": "staging-db.internal",
                    "port": 3306,
                    "name": "workshop_staging",
                    "pool_size": 10,
                    "connection_timeout": 30
                },
                "redis": {
                    "cache_host": "staging-redis.internal",
                    "cache_port": 6379,
                    "queue_host": "staging-redis.internal",
                    "queue_port": 6380
                },
                "security": {
                    "csrf_protection": True,
                    "session_timeout": 3600,
                    "force_https": True
                },
                "logging": {
                    "level": "INFO",
                    "file": "/var/log/frappe/staging.log"
                },
                "monitoring": {
                    "enable_metrics": True,
                    "metrics_port": 9090
                }
            },
            "production": {
                "debug": False,
                "auto_reload": False,
                "developer_mode": False,
                "database": {
                    "host": "prod-db-cluster.internal",
                    "port": 3306,
                    "name": "workshop_production",
                    "pool_size": 20,
                    "connection_timeout": 30,
                    "read_replicas": [
                        "prod-db-read-1.internal",
                        "prod-db-read-2.internal"
                    ]
                },
                "redis": {
                    "cache_host": "prod-redis-cluster.internal",
                    "cache_port": 6379,
                    "queue_host": "prod-redis-cluster.internal",
                    "queue_port": 6380,
                    "sentinel": True
                },
                "security": {
                    "csrf_protection": True,
                    "session_timeout": 1800,
                    "force_https": True,
                    "rate_limiting": True,
                    "max_requests_per_minute": 1000
                },
                "logging": {
                    "level": "WARNING",
                    "file": "/var/log/frappe/production.log",
                    "syslog": True
                },
                "monitoring": {
                    "enable_metrics": True,
                    "metrics_port": 9090,
                    "health_check_endpoint": "/api/method/ping"
                },
                "performance": {
                    "worker_processes": 4,
                    "max_workers": 20,
                    "worker_timeout": 300,
                    "keep_alive": 2
                }
            }
        }
        
        created_files = []
        for env, config in configs.items():
            config_file = self.config_dir / f"{env}_config.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            created_files.append(config_file)
        
        return created_files
    
    def create_environment_files(self):
        """Create .env files for each environment"""
        env_vars = {
            "development": {
                "FRAPPE_ENV": "development",
                "DB_HOST": "localhost",
                "DB_PORT": "3306",
                "DB_NAME": "workshop_dev",
                "DB_USER": "frappe_dev",
                "DB_PASSWORD": "dev_password",
                "REDIS_CACHE_HOST": "localhost",
                "REDIS_CACHE_PORT": "6379",
                "REDIS_QUEUE_HOST": "localhost",
                "REDIS_QUEUE_PORT": "6380",
                "MAIL_SERVER": "localhost",
                "MAIL_PORT": "587",
                "MAIL_USE_TLS": "false",
                "MAIL_USERNAME": "",
                "MAIL_PASSWORD": "",
                "ENCRYPTION_KEY": "dev_encryption_key_12345",
                "SECRET_KEY": "dev_secret_key_12345",
                "LOG_LEVEL": "DEBUG",
                "LOG_FILE": "/var/log/frappe/development.log"
            },
            "staging": {
                "FRAPPE_ENV": "staging",
                "DB_HOST": "staging-db.internal",
                "DB_PORT": "3306",
                "DB_NAME": "workshop_staging",
                "DB_USER": "frappe_staging",
                "DB_PASSWORD": "${STAGING_DB_PASSWORD}",
                "REDIS_CACHE_HOST": "staging-redis.internal",
                "REDIS_CACHE_PORT": "6379",
                "REDIS_QUEUE_HOST": "staging-redis.internal",
                "REDIS_QUEUE_PORT": "6380",
                "MAIL_SERVER": "mail.staging.domain.com",
                "MAIL_PORT": "587",
                "MAIL_USE_TLS": "true",
                "MAIL_USERNAME": "${STAGING_MAIL_USERNAME}",
                "MAIL_PASSWORD": "${STAGING_MAIL_PASSWORD}",
                "ENCRYPTION_KEY": "${STAGING_ENCRYPTION_KEY}",
                "SECRET_KEY": "${STAGING_SECRET_KEY}",
                "LOG_LEVEL": "INFO",
                "LOG_FILE": "/var/log/frappe/staging.log"
            },
            "production": {
                "FRAPPE_ENV": "production",
                "DB_HOST": "prod-db-cluster.internal",
                "DB_PORT": "3306",
                "DB_NAME": "workshop_production",
                "DB_USER": "frappe_prod",
                "DB_PASSWORD": "${PROD_DB_PASSWORD}",
                "REDIS_CACHE_HOST": "prod-redis-cluster.internal",
                "REDIS_CACHE_PORT": "6379",
                "REDIS_QUEUE_HOST": "prod-redis-cluster.internal",
                "REDIS_QUEUE_PORT": "6380",
                "MAIL_SERVER": "mail.yourdomain.com",
                "MAIL_PORT": "587",
                "MAIL_USE_TLS": "true",
                "MAIL_USERNAME": "${PROD_MAIL_USERNAME}",
                "MAIL_PASSWORD": "${PROD_MAIL_PASSWORD}",
                "ENCRYPTION_KEY": "${PROD_ENCRYPTION_KEY}",
                "SECRET_KEY": "${PROD_SECRET_KEY}",
                "LOG_LEVEL": "WARNING",
                "LOG_FILE": "/var/log/frappe/production.log"
            }
        }
        
        created_files = []
        for env, vars_dict in env_vars.items():
            env_file = self.config_dir / f".env.{env}"
            with open(env_file, 'w') as f:
                for key, value in vars_dict.items():
                    f.write(f"{key}={value}\n")
            created_files.append(env_file)
        
        return created_files
    
    def create_docker_env_files(self):
        """Create Docker-specific environment files"""
        docker_configs = {
            "staging": {
                "COMPOSE_PROJECT_NAME": "workshop_staging",
                "FRAPPE_VERSION": "version-15",
                "ERPNEXT_VERSION": "version-15",
                "DB_ROOT_PASSWORD": "${STAGING_DB_ROOT_PASSWORD}",
                "NGINX_PORT": "80",
                "NGINX_SSL_PORT": "443",
                "WORKER_REPLICAS": "2",
                "SCHEDULER_REPLICAS": "1"
            },
            "production": {
                "COMPOSE_PROJECT_NAME": "workshop_production",
                "FRAPPE_VERSION": "version-15",
                "ERPNEXT_VERSION": "version-15",
                "DB_ROOT_PASSWORD": "${PROD_DB_ROOT_PASSWORD}",
                "NGINX_PORT": "80",
                "NGINX_SSL_PORT": "443",
                "WORKER_REPLICAS": "4",
                "SCHEDULER_REPLICAS": "2"
            }
        }
        
        created_files = []
        for env, config in docker_configs.items():
            docker_env_file = self.config_dir / f".env.docker.{env}"
            with open(docker_env_file, 'w') as f:
                for key, value in config.items():
                    f.write(f"{key}={value}\n")
            created_files.append(docker_env_file)
        
        return created_files
    
    def create_secrets_template(self):
        """Create secrets template for secure credential management"""
        secrets_template = {
            "staging": {
                "database": {
                    "password": "CHANGE_ME_STAGING_DB_PASSWORD",
                    "root_password": "CHANGE_ME_STAGING_DB_ROOT_PASSWORD"
                },
                "mail": {
                    "username": "staging@yourdomain.com",
                    "password": "CHANGE_ME_STAGING_MAIL_PASSWORD"
                },
                "encryption": {
                    "key": "CHANGE_ME_STAGING_ENCRYPTION_KEY_32_CHARS",
                    "secret": "CHANGE_ME_STAGING_SECRET_KEY_32_CHARS"
                }
            },
            "production": {
                "database": {
                    "password": "CHANGE_ME_PROD_DB_PASSWORD",
                    "root_password": "CHANGE_ME_PROD_DB_ROOT_PASSWORD"
                },
                "mail": {
                    "username": "noreply@yourdomain.com",
                    "password": "CHANGE_ME_PROD_MAIL_PASSWORD"
                },
                "encryption": {
                    "key": "CHANGE_ME_PROD_ENCRYPTION_KEY_32_CHARS",
                    "secret": "CHANGE_ME_PROD_SECRET_KEY_32_CHARS"
                }
            }
        }
        
        secrets_file = self.config_dir / "secrets_template.json"
        with open(secrets_file, 'w') as f:
            json.dump(secrets_template, f, indent=2)
        
        return secrets_file

def main():
    """Initialize configuration management"""
    manager = EnvironmentManager()
    
    print("Creating configuration management structure...")
    
    # Create base configuration
    base_config = manager.create_base_config()
    print(f"Created base configuration: {base_config}")
    
    # Create environment-specific configs
    env_configs = manager.create_environment_configs()
    print(f"Created environment configurations: {[str(f) for f in env_configs]}")
    
    # Create environment files
    env_files = manager.create_environment_files()
    print(f"Created environment files: {[str(f) for f in env_files]}")
    
    # Create Docker environment files
    docker_env_files = manager.create_docker_env_files()
    print(f"Created Docker environment files: {[str(f) for f in docker_env_files]}")
    
    # Create secrets template
    secrets_template = manager.create_secrets_template()
    print(f"Created secrets template: {secrets_template}")
    
    print("\nConfiguration management setup complete!")
    print("Don't forget to:")
    print("1. Update secrets in secrets_template.json")
    print("2. Set appropriate file permissions (600) for sensitive files")
    print("3. Use environment-specific .env files for deployments")

if __name__ == "__main__":
    main()
