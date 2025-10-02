#!/bin/bash

#############################################################################
# Frisør LaFata Complete Server Setup Script
# Sets up: BIND DNS, MySQL, Nginx, Python/FastAPI, SSL, Security
# Domain: frisorlafata.dk
# Nameservers: ns1.frisorlafata.dk, ns2.frisorlafata.dk
# Hostname: server1.frisorlafata.dk
#############################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
DOMAIN="frisorlafata.dk"
HOSTNAME="server1.frisorlafata.dk"
SERVER_IP=$(curl -s ifconfig.me || curl -s icanhazip.com)
MYSQL_ROOT_PASSWORD=$(openssl rand -base64 32)
DB_PASSWORD=$(openssl rand -base64 16)
ADMIN_EMAIL="admin@frisorlafata.dk"

# Log file
LOG_FILE="/var/log/frisor_setup.log"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}" | tee -a "$LOG_FILE"
}

#############################################################################
# System Information and Preparation
#############################################################################

log "🚀 Starting Frisør LaFata Server Setup"
log "Server IP: $SERVER_IP"
log "Domain: $DOMAIN"
log "Hostname: $HOSTNAME"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root (use sudo)"
fi

# Detect OS
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    OS=$NAME
    VERSION=$VERSION_ID
else
    error "Cannot detect operating system"
fi

log "Detected OS: $OS $VERSION"

#############################################################################
# System Updates and Basic Packages
#############################################################################

log "📦 Updating system packages..."
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    apt update && apt upgrade -y
    PACKAGE_MANAGER="apt"
    BIND_SERVICE="bind9"
    MYSQL_SERVICE="mysql"
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Rocky"* ]] || [[ "$OS" == *"AlmaLinux"* ]]; then
    yum update -y || dnf update -y
    PACKAGE_MANAGER="yum"
    BIND_SERVICE="named"
    MYSQL_SERVICE="mysqld"
else
    error "Unsupported operating system: $OS"
fi

log "Installing essential packages..."
if [[ "$PACKAGE_MANAGER" == "apt" ]]; then
    apt install -y curl wget git unzip software-properties-common \
        ufw fail2ban htop nano vim certbot python3-certbot-nginx \
        build-essential python3-dev python3-pip python3-venv
elif [[ "$PACKAGE_MANAGER" == "yum" ]]; then
    yum install -y curl wget git unzip epel-release \
        firewalld fail2ban htop nano vim certbot python3-certbot-nginx \
        gcc python3-devel python3-pip python3-virtualenv
fi

#############################################################################
# Set Hostname
#############################################################################

log "🖥️ Setting hostname to $HOSTNAME..."
hostnamectl set-hostname "$HOSTNAME"
echo "127.0.0.1 $HOSTNAME" >> /etc/hosts
echo "$SERVER_IP $HOSTNAME $DOMAIN ns1.$DOMAIN ns2.$DOMAIN" >> /etc/hosts

#############################################################################
# Install and Configure BIND DNS Server
#############################################################################

log "🌐 Installing BIND DNS server..."
if [[ "$PACKAGE_MANAGER" == "apt" ]]; then
    apt install -y bind9 bind9utils bind9-doc dnsutils
elif [[ "$PACKAGE_MANAGER" == "yum" ]]; then
    yum install -y bind bind-utils
fi

log "Configuring BIND..."

# Create main named.conf
cat > /etc/bind/named.conf << EOF
options {
    directory "/var/cache/bind";
    listen-on port 53 { any; };
    listen-on-v6 port 53 { ::1; };
    allow-query { any; };
    allow-recursion { localhost; };
    recursion yes;
    
    forwarders {
        8.8.8.8;
        8.8.4.4;
        1.1.1.1;
    };
    
    auth-nxdomain no;
    dnssec-validation auto;
};

zone "$DOMAIN" {
    type master;
    file "/etc/bind/zones/db.$DOMAIN";
    allow-transfer { any; };
};

zone "$(echo $SERVER_IP | awk -F. '{print $3"."$2"."$1}').in-addr.arpa" {
    type master;
    file "/etc/bind/zones/db.$(echo $SERVER_IP | awk -F. '{print $3"."$2"."$1}')";
};

include "/etc/bind/named.conf.local";
include "/etc/bind/named.conf.default-zones";
EOF

# Create zones directory
mkdir -p /etc/bind/zones

# Create forward zone file
cat > /etc/bind/zones/db.$DOMAIN << EOF
\$TTL    604800
@       IN      SOA     ns1.$DOMAIN. admin.$DOMAIN. (
                     $(date +%Y%m%d)01         ; Serial
                         604800         ; Refresh
                          86400         ; Retry
                        2419200         ; Expire
                         604800 )       ; Negative Cache TTL

; Name servers
@       IN      NS      ns1.$DOMAIN.
@       IN      NS      ns2.$DOMAIN.

; A records
@       IN      A       $SERVER_IP
ns1     IN      A       $SERVER_IP
ns2     IN      A       $SERVER_IP
server1 IN      A       $SERVER_IP
www     IN      A       $SERVER_IP
api     IN      A       $SERVER_IP
admin   IN      A       $SERVER_IP

; CNAME records
mail    IN      CNAME   @
ftp     IN      CNAME   @

; MX record
@       IN      MX      10      mail.$DOMAIN.
EOF

# Create reverse zone file
REVERSE_ZONE=$(echo $SERVER_IP | awk -F. '{print $3"."$2"."$1}')
cat > /etc/bind/zones/db.$REVERSE_ZONE << EOF
\$TTL    604800
@       IN      SOA     ns1.$DOMAIN. admin.$DOMAIN. (
                     $(date +%Y%m%d)01         ; Serial
                         604800         ; Refresh
                          86400         ; Retry
                        2419200         ; Expire
                         604800 )       ; Negative Cache TTL

; Name servers
@       IN      NS      ns1.$DOMAIN.
@       IN      NS      ns2.$DOMAIN.

; PTR record
$(echo $SERVER_IP | awk -F. '{print $4}')      IN      PTR     $DOMAIN.
EOF

# Set permissions
chown -R bind:bind /etc/bind/zones
chmod 644 /etc/bind/zones/*

# Test BIND configuration
named-checkconf || error "BIND configuration error"
named-checkzone $DOMAIN /etc/bind/zones/db.$DOMAIN || error "Forward zone configuration error"

log "Starting BIND service..."
systemctl enable $BIND_SERVICE
systemctl restart $BIND_SERVICE

#############################################################################
# Install and Configure MySQL/MariaDB
#############################################################################

log "🗄️ Installing MySQL/MariaDB..."
if [[ "$PACKAGE_MANAGER" == "apt" ]]; then
    apt install -y mysql-server mysql-client
elif [[ "$PACKAGE_MANAGER" == "yum" ]]; then
    yum install -y mysql-server mysql
fi

log "Starting MySQL service..."
systemctl enable $MYSQL_SERVICE
systemctl start $MYSQL_SERVICE

log "Securing MySQL installation..."
# Set root password and secure installation
mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '$MYSQL_ROOT_PASSWORD';"
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "DELETE FROM mysql.user WHERE User='';"
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "DROP DATABASE IF EXISTS test;"
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';"
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "FLUSH PRIVILEGES;"

# Create application database and user
log "Creating application database..."
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "CREATE DATABASE IF NOT EXISTS target_lafata CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "CREATE USER IF NOT EXISTS 'target_lafata'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "GRANT ALL PRIVILEGES ON target_lafata.* TO 'target_lafata'@'localhost';"
mysql -u root -p$MYSQL_ROOT_PASSWORD -e "FLUSH PRIVILEGES;"

#############################################################################
# Install and Configure Nginx
#############################################################################

log "🌍 Installing Nginx..."
if [[ "$PACKAGE_MANAGER" == "apt" ]]; then
    apt install -y nginx
elif [[ "$PACKAGE_MANAGER" == "yum" ]]; then
    yum install -y nginx
fi

log "Configuring Nginx..."
# Remove default site
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

# Create main site configuration
cat > /etc/nginx/sites-available/$DOMAIN << EOF
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;
    
    # SSL certificates (will be configured by certbot)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload";
    
    # Document root for React app
    root /var/www/$DOMAIN/html;
    index index.html;
    
    # Serve static files
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # API proxy to FastAPI backend
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Static assets with long cache
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/

# Test Nginx configuration
nginx -t || error "Nginx configuration error"

# Create web directory
mkdir -p /var/www/$DOMAIN/html
chown -R www-data:www-data /var/www/$DOMAIN 2>/dev/null || chown -R nginx:nginx /var/www/$DOMAIN

log "Starting Nginx service..."
systemctl enable nginx
systemctl start nginx

#############################################################################
# Install Python and FastAPI Dependencies
#############################################################################

log "🐍 Setting up Python environment for FastAPI..."

# Install Python 3.9+ if not available
if [[ "$PACKAGE_MANAGER" == "apt" ]]; then
    add-apt-repository ppa:deadsnakes/ppa -y 2>/dev/null || true
    apt update
    apt install -y python3.9 python3.9-venv python3.9-dev || apt install -y python3 python3-venv python3-dev
elif [[ "$PACKAGE_MANAGER" == "yum" ]]; then
    yum install -y python39 python39-devel || yum install -y python3 python3-devel
fi

# Create application directory
mkdir -p /opt/frisor-backend
cd /opt/frisor-backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Create requirements.txt
cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-decouple==3.8
aiomysql==0.2.0
pymysql==1.1.0
cryptography==41.0.7
email-validator==2.1.0
jinja2==3.1.2
pydantic==2.5.0
pydantic-settings==2.1.0
motor==3.3.2
pymongo==4.6.0
aiofiles==23.2.1
pillow==10.1.0
EOF

# Install Python packages
pip install --upgrade pip
pip install -r requirements.txt

#############################################################################
# Setup Systemd Service for FastAPI
#############################################################################

log "⚙️ Creating FastAPI systemd service..."

cat > /etc/systemd/system/frisor-backend.service << EOF
[Unit]
Description=Frisor LaFata FastAPI Backend
After=network.target mysql.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/frisor-backend
Environment=PATH=/opt/frisor-backend/venv/bin
ExecStart=/opt/frisor-backend/venv/bin/uvicorn server:app --host 127.0.0.1 --port 8001 --workers 4
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

#############################################################################
# Configure Firewall
#############################################################################

log "🔥 Configuring firewall..."
if [[ "$PACKAGE_MANAGER" == "apt" ]]; then
    # UFW for Ubuntu/Debian
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 'Nginx Full'
    ufw allow 53/tcp
    ufw allow 53/udp
    ufw --force enable
elif [[ "$PACKAGE_MANAGER" == "yum" ]]; then
    # firewalld for CentOS/RHEL
    systemctl enable firewalld
    systemctl start firewalld
    firewall-cmd --permanent --add-service=ssh
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --permanent --add-service=dns
    firewall-cmd --reload
fi

#############################################################################
# Setup SSL with Let's Encrypt
#############################################################################

log "🔒 Setting up SSL certificates..."
# Create temporary index page
cat > /var/www/$DOMAIN/html/index.html << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Frisør LaFata - Setting Up</title>
</head>
<body>
    <h1>Frisør LaFata</h1>
    <p>Server setup in progress...</p>
</body>
</html>
EOF

# Disable SSL temporarily for certificate generation
sed -i 's/listen 443 ssl/listen 443/' /etc/nginx/sites-available/$DOMAIN
sed -i '/ssl_certificate/d' /etc/nginx/sites-available/$DOMAIN
systemctl reload nginx

# Get SSL certificate
certbot --nginx -d $DOMAIN -d www.$DOMAIN --email $ADMIN_EMAIL --agree-tos --non-interactive --redirect

#############################################################################
# Create Application Configuration Files
#############################################################################

log "📝 Creating application configuration files..."

# Create .env file for FastAPI
cat > /opt/frisor-backend/.env << EOF
# Database Configuration
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=target_lafata
MYSQL_PASSWORD=$DB_PASSWORD
MYSQL_DATABASE=target_lafata

# Application Configuration
CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
SECRET_KEY=$(openssl rand -base64 64)

# Email Configuration
EMAIL_USER=noreply@$DOMAIN
EMAIL_PASSWORD=
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587

# PayPal Configuration (optional)
PAYPAL_CLIENT_ID=
PAYPAL_CLIENT_SECRET=
PAYPAL_SANDBOX_MODE=true
EOF

# Set proper permissions
chown -R www-data:www-data /opt/frisor-backend 2>/dev/null || chown -R nginx:nginx /opt/frisor-backend
chmod 600 /opt/frisor-backend/.env

#############################################################################
# Create Database Schema Import Script
#############################################################################

log "📊 Creating database schema..."

cat > /opt/frisor-backend/init_database.sql << EOF
-- Frisor LaFata MySQL Database Schema
USE target_lafata;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Services table  
CREATE TABLE IF NOT EXISTS services (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    duration_minutes INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    description TEXT,
    category VARCHAR(100) DEFAULT 'general',
    icon VARCHAR(100) DEFAULT 'sparkles',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Staff table
CREATE TABLE IF NOT EXISTS staff (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    experience_years INT NOT NULL,
    bio TEXT,
    avatar_url TEXT,
    instagram_url VARCHAR(255),
    facebook_url VARCHAR(255),
    linkedin_url VARCHAR(255),
    twitter_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Site settings table
CREATE TABLE IF NOT EXISTS site_settings (
    id VARCHAR(36) PRIMARY KEY,
    site_title VARCHAR(255) DEFAULT 'Frisør LaFata',
    site_description TEXT DEFAULT 'Klassisk barbering siden 2010',
    contact_phone VARCHAR(50) DEFAULT '+45 12 34 56 78',
    contact_email VARCHAR(255) DEFAULT 'info@frisorlafata.dk',
    address TEXT DEFAULT 'Hovedgaden 123, 8000 Århus',
    hero_title VARCHAR(255) DEFAULT 'Frisør LaFata',
    hero_subtitle VARCHAR(255) DEFAULT 'Klassik Barbering',
    hero_description TEXT DEFAULT 'Oplev den autentiske barber-oplevelse hos Frisør LaFata.',
    hero_image TEXT,
    hero_video TEXT,
    hero_video_enabled BOOLEAN DEFAULT FALSE,
    hero_text_overlay_enabled BOOLEAN DEFAULT TRUE,
    hero_image_opacity DECIMAL(3,2) DEFAULT 0.70,
    booking_system_enabled BOOLEAN DEFAULT TRUE,
    social_media_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert default settings
INSERT IGNORE INTO site_settings (id, site_title, hero_title, hero_subtitle, hero_description) 
VALUES (UUID(), 'Frisør LaFata', 'Frisør LaFata', 'Klassik Barbering', 'Oplev den autentiske barber-oplevelse hos Frisør LaFata.');
EOF

# Import schema
mysql -u target_lafata -p$DB_PASSWORD target_lafata < /opt/frisor-backend/init_database.sql

#############################################################################
# Create Maintenance and Backup Scripts
#############################################################################

log "🔧 Creating maintenance scripts..."

# Database backup script
cat > /opt/frisor-backend/backup_database.sh << EOF
#!/bin/bash
BACKUP_DIR="/opt/frisor-backend/backups"
DATE=\$(date +%Y%m%d_%H%M%S)
mkdir -p \$BACKUP_DIR

mysqldump -u target_lafata -p$DB_PASSWORD target_lafata > \$BACKUP_DIR/frisor_backup_\$DATE.sql
gzip \$BACKUP_DIR/frisor_backup_\$DATE.sql

# Keep only last 30 days of backups
find \$BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Database backup completed: frisor_backup_\$DATE.sql.gz"
EOF

chmod +x /opt/frisor-backend/backup_database.sh

# Add to crontab for daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/frisor-backend/backup_database.sh") | crontab -

#############################################################################
# Setup Log Rotation
#############################################################################

cat > /etc/logrotate.d/frisor-backend << EOF
/var/log/frisor-backend/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload frisor-backend
    endscript
}
EOF

#############################################################################
# Final System Configuration
#############################################################################

log "⚡ Final system configuration..."

# Enable services
systemctl daemon-reload
systemctl enable frisor-backend
systemctl enable nginx
systemctl enable $MYSQL_SERVICE
systemctl enable $BIND_SERVICE

# Configure fail2ban
if [[ -f /etc/fail2ban/jail.conf ]]; then
    cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
EOF
    systemctl enable fail2ban
    systemctl restart fail2ban
fi

#############################################################################
# Create Admin Info File
#############################################################################

log "📋 Creating admin information file..."

cat > /root/frisor_server_info.txt << EOF
========================================
FRISØR LAFATA SERVER SETUP COMPLETE
========================================

Server Details:
- Hostname: $HOSTNAME
- Domain: $DOMAIN  
- Server IP: $SERVER_IP
- Setup Date: $(date)

DNS Configuration:
- Nameserver 1: ns1.$DOMAIN ($SERVER_IP)
- Nameserver 2: ns2.$DOMAIN ($SERVER_IP)

Database:
- MySQL Root Password: $MYSQL_ROOT_PASSWORD
- Application Database: target_lafata
- Application User: target_lafata
- Application Password: $DB_PASSWORD

Services Status:
- Nginx: Running on ports 80/443
- MySQL: Running on port 3306
- BIND DNS: Running on port 53
- FastAPI Backend: Will run on port 8001

Important Files:
- Nginx Config: /etc/nginx/sites-available/$DOMAIN
- Backend Code: /opt/frisor-backend/
- Database Backups: /opt/frisor-backend/backups/
- SSL Certificates: /etc/letsencrypt/live/$DOMAIN/
- Setup Log: $LOG_FILE

Next Steps:
1. Update your domain registrar to use nameservers:
   - ns1.$DOMAIN
   - ns2.$DOMAIN

2. Upload your FastAPI backend code to: /opt/frisor-backend/

3. Upload your frontend files to: /var/www/$DOMAIN/html/

4. Start the backend service: systemctl start frisor-backend

5. Test your website: https://$DOMAIN

Security Notes:
- SSH access is protected by fail2ban
- Firewall is configured and active
- SSL certificates auto-renew
- Database backups run daily at 2 AM

WARNING: Save this file securely - it contains sensitive passwords!
========================================
EOF

chmod 600 /root/frisor_server_info.txt

#############################################################################
# Display Final Summary
#############################################################################

log "🎉 Server setup completed successfully!"
info "============================================="
info "FRISØR LAFATA SERVER SETUP COMPLETE"
info "============================================="
info "Server IP: $SERVER_IP"
info "Domain: $DOMAIN"
info "Hostname: $HOSTNAME"
info ""
info "IMPORTANT: Update your domain's nameservers to:"
info "- ns1.$DOMAIN"
info "- ns2.$DOMAIN"
info ""
info "Server credentials saved to: /root/frisor_server_info.txt"
info "Setup log available at: $LOG_FILE"
info ""
info "Next steps:"
info "1. Upload backend code to /opt/frisor-backend/"
info "2. Upload frontend files to /var/www/$DOMAIN/html/"
info "3. Start backend: systemctl start frisor-backend"
info "4. Visit: https://$DOMAIN"
info "============================================="

# Create a simple status check script
cat > /usr/local/bin/frisor-status << EOF
#!/bin/bash
echo "Frisør LaFata Server Status"
echo "=========================="
echo "Nginx: \$(systemctl is-active nginx)"
echo "MySQL: \$(systemctl is-active $MYSQL_SERVICE)"
echo "BIND: \$(systemctl is-active $BIND_SERVICE)"
echo "Backend: \$(systemctl is-active frisor-backend)"
echo "SSL Cert: \$(certbot certificates 2>/dev/null | grep -o 'VALID: [0-9]*' | head -1 || echo 'Check manually')"
echo ""
echo "Disk Usage: \$(df -h / | tail -1 | awk '{print \$5}')"
echo "Memory: \$(free -m | grep Mem | awk '{printf \"%.1f%%\", \$3/\$2 * 100.0}')"
echo "Load: \$(uptime | awk -F'load average:' '{ print \$2 }')"
EOF

chmod +x /usr/local/bin/frisor-status

log "✅ Setup script completed! Run 'frisor-status' to check service status."
log "📁 All credentials and information saved in /root/frisor_server_info.txt"

exit 0