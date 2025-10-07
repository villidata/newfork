#!/bin/bash
set -e

echo "🚀 FRISOR LAFATA - COMPLETE DEPLOYMENT CHECK & FIX SCRIPT"
echo "=========================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -d "/opt/frisor-frontend" ] || [ ! -d "/opt/frisor-backend" ]; then
    print_error "Frisor directories not found in /opt/"
    exit 1
fi

print_info "Step 1: Stopping services..."
systemctl stop frisor-backend 2>/dev/null || true

print_info "Step 2: Installing missing frontend dependencies..."
cd /opt/frisor-frontend

# Install missing tailwind dependency
npm install tailwindcss-animate
npm install @tailwindcss/forms @tailwindcss/typography
npm install react-beautiful-dnd @tinymce/tinymce-react

# Install all other dependencies
npm install

print_info "Step 3: Checking backend dependencies..."
cd /opt/frisor-backend

# Activate virtual environment
source venv/bin/activate

# Install missing Python dependencies
pip install aiomysql pymysql passlib[bcrypt] python-jose[cryptography] python-multipart

print_info "Step 4: Checking database tables..."

# Get MySQL credentials from .env
if [ -f ".env" ]; then
    MYSQL_HOST=$(grep MYSQL_HOST .env | cut -d '=' -f2)
    MYSQL_USER=$(grep MYSQL_USER .env | cut -d '=' -f2)
    MYSQL_PASSWORD=$(grep MYSQL_PASSWORD .env | cut -d '=' -f2)
    MYSQL_DATABASE=$(grep MYSQL_DATABASE .env | cut -d '=' -f2)
    
    print_info "Found database: $MYSQL_DATABASE"
else
    print_error ".env file not found in backend directory"
    exit 1
fi

# Check if required tables exist
REQUIRED_TABLES=("users" "user_passwords" "staff" "services" "bookings" "settings" "pages" "gallery" "homepage_sections")

for table in "${REQUIRED_TABLES[@]}"; do
    if mysql -h"$MYSQL_HOST" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "DESCRIBE $table;" >/dev/null 2>&1; then
        print_status "Table '$table' exists"
    else
        print_error "Table '$table' missing - needs to be created"
    fi
done

print_info "Step 5: Building frontend..."
cd /opt/frisor-frontend
npm run build

if [ $? -eq 0 ]; then
    print_status "Frontend build successful"
else
    print_error "Frontend build failed"
    exit 1
fi

print_info "Step 6: Starting backend service..."
systemctl start frisor-backend

# Wait for service to start
sleep 5

if systemctl is-active --quiet frisor-backend; then
    print_status "Backend service started successfully"
else
    print_error "Backend service failed to start"
    journalctl -u frisor-backend --no-pager -n 10
    exit 1
fi

print_info "Step 7: Testing API endpoints..."

# Test login endpoint
LOGIN_RESPONSE=$(curl -s -X POST https://frisorlafata.dk/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@frisorlafata.dk","password":"admin123"}')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    print_status "Admin login working"
    
    # Extract token for further tests
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")
    
    if [ -n "$TOKEN" ]; then
        # Test protected endpoints
        USERS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" https://frisorlafata.dk/api/users)
        if echo "$USERS_RESPONSE" | grep -q -E '(\[|\{)'; then
            print_status "Users endpoint working"
        else
            print_error "Users endpoint not working"
        fi
        
        STAFF_RESPONSE=$(curl -s https://frisorlafata.dk/api/staff)
        if echo "$STAFF_RESPONSE" | grep -q -E '(\[|\{)'; then
            print_status "Staff endpoint working"
        else
            print_error "Staff endpoint not working"
        fi
        
        SERVICES_RESPONSE=$(curl -s https://frisorlafata.dk/api/services)
        if echo "$SERVICES_RESPONSE" | grep -q -E '(\[|\{)'; then
            print_status "Services endpoint working"
        else
            print_error "Services endpoint not working"
        fi
    fi
else
    print_error "Admin login not working"
    echo "Response: $LOGIN_RESPONSE"
fi

print_info "Step 8: Checking file permissions..."
chown -R www-data:www-data /opt/frisor-frontend/build 2>/dev/null || true

print_info "Step 9: Restarting nginx..."
systemctl restart nginx

if systemctl is-active --quiet nginx; then
    print_status "Nginx restarted successfully"
else
    print_error "Nginx failed to restart"
fi

echo ""
echo "=========================================================="
print_status "DEPLOYMENT CHECK COMPLETE!"
echo ""
print_info "Frontend URL: https://frisorlafata.dk"
print_info "Admin Panel: https://frisorlafata.dk/admin"
print_info "API Base: https://frisorlafata.dk/api"
echo ""
print_info "Test the admin login with: admin@frisorlafata.dk / admin123"
echo "=========================================================="