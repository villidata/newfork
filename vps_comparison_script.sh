#!/bin/bash

# VPS Comparison Script
# Run this script ON YOUR VPS to compare deployed files with emergent.sh preview
# Usage: bash vps_comparison_script.sh

echo "======================================"
echo "VPS DEPLOYMENT ANALYSIS REPORT"
echo "======================================"
echo ""
echo "Generated on: $(date)"
echo ""

# Define VPS directories
VPS_FRONTEND="/opt/frisor-frontend"
VPS_BACKEND="/opt/frisor-backend"
REPORT_FILE="vps_deployment_report.md"

# Initialize report
cat > "$REPORT_FILE" << 'EOF'
# VPS Deployment Analysis Report

**Generated:** $(date)

This report analyzes the current deployment on your VPS.

---

EOF

echo "## VPS DEPLOYMENT STATUS" | tee -a "$REPORT_FILE"
echo "========================" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Check frontend directory
echo "### Frontend Directory: $VPS_FRONTEND" | tee -a "$REPORT_FILE"
if [ -d "$VPS_FRONTEND" ]; then
    echo "✅ Directory exists" | tee -a "$REPORT_FILE"
    echo "📊 Total files: $(find $VPS_FRONTEND -type f | wc -l)" | tee -a "$REPORT_FILE"
    echo "📦 Size: $(du -sh $VPS_FRONTEND | cut -f1)" | tee -a "$REPORT_FILE"
else
    echo "❌ Directory NOT found" | tee -a "$REPORT_FILE"
fi
echo "" | tee -a "$REPORT_FILE"

# Check backend directory
echo "### Backend Directory: $VPS_BACKEND" | tee -a "$REPORT_FILE"
if [ -d "$VPS_BACKEND" ]; then
    echo "✅ Directory exists" | tee -a "$REPORT_FILE"
    echo "📊 Total files: $(find $VPS_BACKEND -type f | wc -l)" | tee -a "$REPORT_FILE"
    echo "📦 Size: $(du -sh $VPS_BACKEND | cut -f1)" | tee -a "$REPORT_FILE"
else
    echo "❌ Directory NOT found" | tee -a "$REPORT_FILE"
fi
echo "" | tee -a "$REPORT_FILE"

# Frontend structure analysis
if [ -d "$VPS_FRONTEND" ]; then
    echo "## FRONTEND STRUCTURE" | tee -a "$REPORT_FILE"
    echo "=====================" | tee -a "$REPORT_FILE"
    echo "" | tee -a "$REPORT_FILE"
    
    # Check critical directories
    for dir in "src" "src/components" "src/components/ui" "public" "build"; do
        if [ -d "$VPS_FRONTEND/$dir" ]; then
            echo "✅ $dir/ - $(find $VPS_FRONTEND/$dir -type f 2>/dev/null | wc -l) files" | tee -a "$REPORT_FILE"
        else
            echo "❌ $dir/ - NOT FOUND" | tee -a "$REPORT_FILE"
        fi
    done
    echo "" | tee -a "$REPORT_FILE"
    
    # List all components
    echo "### All Components:" | tee -a "$REPORT_FILE"
    if [ -d "$VPS_FRONTEND/src/components" ]; then
        find "$VPS_FRONTEND/src/components" -maxdepth 2 -name "*.js" -o -name "*.jsx" | sort | sed "s|$VPS_FRONTEND/src/components/||" | tee -a "$REPORT_FILE"
    fi
    echo "" | tee -a "$REPORT_FILE"
    
    # Check BookingSystem specifically
    echo "### 🎯 Booking Components:" | tee -a "$REPORT_FILE"
    if [ -f "$VPS_FRONTEND/src/components/BookingSystem.js" ]; then
        echo "✅ BookingSystem.js exists" | tee -a "$REPORT_FILE"
        echo "   Size: $(du -h $VPS_FRONTEND/src/components/BookingSystem.js | cut -f1)" | tee -a "$REPORT_FILE"
        echo "   Lines: $(wc -l < $VPS_FRONTEND/src/components/BookingSystem.js)" | tee -a "$REPORT_FILE"
    else
        echo "❌ BookingSystem.js NOT FOUND" | tee -a "$REPORT_FILE"
    fi
    
    if [ -f "$VPS_FRONTEND/src/components/BookingModal.js" ]; then
        echo "⚠️ BookingModal.js exists (may be outdated)" | tee -a "$REPORT_FILE"
        echo "   Size: $(du -h $VPS_FRONTEND/src/components/BookingModal.js | cut -f1)" | tee -a "$REPORT_FILE"
        echo "   Lines: $(wc -l < $VPS_FRONTEND/src/components/BookingModal.js)" | tee -a "$REPORT_FILE"
    fi
    echo "" | tee -a "$REPORT_FILE"
    
    # Check configuration files
    echo "### Configuration Files:" | tee -a "$REPORT_FILE"
    for file in "package.json" "tailwind.config.js" "postcss.config.js" "craco.config.js" ".env"; do
        if [ -f "$VPS_FRONTEND/$file" ]; then
            echo "✅ $file" | tee -a "$REPORT_FILE"
        else
            echo "❌ $file - NOT FOUND" | tee -a "$REPORT_FILE"
        fi
    done
    echo "" | tee -a "$REPORT_FILE"
    
    # Check build directory
    echo "### Build Status:" | tee -a "$REPORT_FILE"
    if [ -d "$VPS_FRONTEND/build" ]; then
        echo "✅ Build directory exists" | tee -a "$REPORT_FILE"
        echo "   Files: $(find $VPS_FRONTEND/build -type f | wc -l)" | tee -a "$REPORT_FILE"
        echo "   Size: $(du -sh $VPS_FRONTEND/build | cut -f1)" | tee -a "$REPORT_FILE"
        echo "   Last modified: $(stat -c %y $VPS_FRONTEND/build 2>/dev/null || stat -f %Sm $VPS_FRONTEND/build)" | tee -a "$REPORT_FILE"
    else
        echo "❌ Build directory NOT FOUND - run 'npm run build'" | tee -a "$REPORT_FILE"
    fi
    echo "" | tee -a "$REPORT_FILE"
fi

# Backend structure analysis
if [ -d "$VPS_BACKEND" ]; then
    echo "## BACKEND STRUCTURE" | tee -a "$REPORT_FILE"
    echo "====================" | tee -a "$REPORT_FILE"
    echo "" | tee -a "$REPORT_FILE"
    
    # List all Python files
    echo "### Python Files:" | tee -a "$REPORT_FILE"
    find "$VPS_BACKEND" -maxdepth 1 -name "*.py" | sort | sed "s|$VPS_BACKEND/||" | tee -a "$REPORT_FILE"
    echo "" | tee -a "$REPORT_FILE"
    
    # Check critical files
    echo "### Critical Files:" | tee -a "$REPORT_FILE"
    for file in "server.py" "requirements.txt" ".env" "database.py"; do
        if [ -f "$VPS_BACKEND/$file" ]; then
            echo "✅ $file" | tee -a "$REPORT_FILE"
        else
            echo "❌ $file - NOT FOUND" | tee -a "$REPORT_FILE"
        fi
    done
    echo "" | tee -a "$REPORT_FILE"
fi

# Service status
echo "## SERVICE STATUS" | tee -a "$REPORT_FILE"
echo "=================" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Check systemd service
if systemctl list-units --type=service | grep -q "frisor-backend"; then
    echo "### Backend Service (frisor-backend.service):" | tee -a "$REPORT_FILE"
    systemctl status frisor-backend.service --no-pager | head -20 | tee -a "$REPORT_FILE"
else
    echo "❌ Backend service not found" | tee -a "$REPORT_FILE"
fi
echo "" | tee -a "$REPORT_FILE"

# Check Nginx
if command -v nginx &> /dev/null; then
    echo "### Nginx Status:" | tee -a "$REPORT_FILE"
    systemctl status nginx --no-pager | head -10 | tee -a "$REPORT_FILE"
    echo "" | tee -a "$REPORT_FILE"
    
    echo "### Nginx Configuration:" | tee -a "$REPORT_FILE"
    if [ -f "/etc/nginx/sites-enabled/frisorlafata.dk" ]; then
        echo "✅ Site configuration exists" | tee -a "$REPORT_FILE"
    else
        echo "❌ Site configuration NOT FOUND" | tee -a "$REPORT_FILE"
    fi
fi
echo "" | tee -a "$REPORT_FILE"

# Check ports
echo "## PORT STATUS" | tee -a "$REPORT_FILE"
echo "==============" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

echo "### Listening Ports:" | tee -a "$REPORT_FILE"
ss -tlnp | grep -E ":(80|443|8001|3000)" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Recent logs
echo "## RECENT LOGS" | tee -a "$REPORT_FILE"
echo "==============" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

if [ -f "/var/log/nginx/error.log" ]; then
    echo "### Nginx Error Log (last 10 lines):" | tee -a "$REPORT_FILE"
    tail -10 /var/log/nginx/error.log | tee -a "$REPORT_FILE"
    echo "" | tee -a "$REPORT_FILE"
fi

if systemctl list-units --type=service | grep -q "frisor-backend"; then
    echo "### Backend Service Log (last 10 lines):" | tee -a "$REPORT_FILE"
    journalctl -u frisor-backend.service -n 10 --no-pager | tee -a "$REPORT_FILE"
    echo "" | tee -a "$REPORT_FILE"
fi

echo "---" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"
echo "## NEXT STEPS" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"
echo "1. Share this report with the AI engineer" | tee -a "$REPORT_FILE"
echo "2. If BookingSystem.js is missing, it needs to be copied from preview" | tee -a "$REPORT_FILE"
echo "3. Check if build directory is up to date" | tee -a "$REPORT_FILE"
echo "4. Verify all services are running" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

echo ""
echo "======================================"
echo "✅ ANALYSIS COMPLETE"
echo "======================================"
echo ""
echo "📄 Full report saved to: $REPORT_FILE"
echo ""
echo "Please share this report file contents with the AI engineer."
echo ""
