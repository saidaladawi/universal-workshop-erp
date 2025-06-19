# Universal Workshop ERP v2.0 Dockerfile
# نظام إدارة الورش الشامل - إعداد Docker
FROM ubuntu:22.04

LABEL maintainer="Eng. Saeed Al-Adawi <al.a.dawi@hotmail.com>"
LABEL description="Universal Workshop ERP - Arabic-first ERP for Omani automotive workshops"
LABEL version="2.0.0"

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8
ENV FRAPPE_USER=frappe
ENV BENCH_NAME=frappe-bench
ENV SITE_NAME=workshop.local

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    mariadb-client \
    redis-tools \
    libmysqlclient-dev \
    libffi-dev \
    libssl-dev \
    wkhtmltopdf \
    xvfb \
    libfontconfig \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fonts-liberation \
    locales \
    sudo \
    supervisor \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Setup Arabic locale
RUN locale-gen ar_OM.UTF-8 en_US.UTF-8 \
    && update-locale LANG=en_US.UTF-8

# Install Node.js 18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g yarn

# Create frappe user
RUN useradd -ms /bin/bash $FRAPPE_USER \
    && usermod -aG sudo $FRAPPE_USER \
    && echo "$FRAPPE_USER ALL=(ALL:ALL) NOPASSWD: ALL" > /etc/sudoers.d/$FRAPPE_USER

# Switch to frappe user
USER $FRAPPE_USER
WORKDIR /home/$FRAPPE_USER

# Install frappe-bench
RUN pip3 install --user frappe-bench

# Add pip bin to PATH
ENV PATH="/home/$FRAPPE_USER/.local/bin:$PATH"

# Initialize bench
RUN bench init --frappe-branch version-15 $BENCH_NAME \
    && cd $BENCH_NAME \
    && bench get-app --branch version-15 erpnext

# Copy Universal Workshop app
COPY --chown=$FRAPPE_USER:$FRAPPE_USER apps/universal_workshop /home/$FRAPPE_USER/$BENCH_NAME/apps/universal_workshop

# Switch back to root for system configuration
USER root

# Copy configuration files
COPY config/docker/nginx.conf /etc/nginx/sites-available/default
COPY config/docker/supervisor.conf /etc/supervisor/conf.d/frappe.conf

# Create nginx directories
RUN mkdir -p /var/log/nginx \
    && chown -R www-data:www-data /var/log/nginx

# Setup startup script
COPY scripts/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose ports
EXPOSE 80 8000 9000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/method/ping || exit 1

# Switch back to frappe user
USER $FRAPPE_USER
WORKDIR /home/$FRAPPE_USER/$BENCH_NAME

# Default command
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["bench", "start"] 