#!/bin/bash

echo "======================================"
echo "FIXING BOOKING SYSTEM ISSUES"
echo "======================================"
echo ""

echo "Step 1: Backing up current files..."
cp /opt/frisor-backend/server.py /opt/frisor-backend/server.py.backup.$(date +%Y%m%d_%H%M%S)
cp /opt/frisor-frontend/src/components/BookingSystem.js /opt/frisor-frontend/src/components/BookingSystem.js.backup.$(date +%Y%m%d_%H%M%S)

echo "✅ Backups created"
echo ""

echo "Step 2: Updating backend server.py..."
echo "This will fix the Staff model validation errors"
echo ""

# The fixes will be applied via file replacement
echo "Please apply the backend changes manually or use the updated files"
echo ""

echo "Step 3: Updating frontend BookingSystem.js..."
echo "This will fix the TypeError: v.find is not a function"
echo ""

echo "======================================"
echo "MANUAL STEPS REQUIRED:"
echo "======================================"
echo ""
echo "1. Copy the updated server.py from emergent.sh to /opt/frisor-backend/"
echo "2. Copy the updated BookingSystem.js from emergent.sh to /opt/frisor-frontend/src/components/"
echo ""
echo "3. Restart backend:"
echo "   sudo systemctl restart frisor-backend"
echo ""
echo "4. Rebuild frontend:"
echo "   cd /opt/frisor-frontend"
echo "   npm run build"
echo "   sudo systemctl reload nginx"
echo ""
echo "5. Test the website:"
echo "   https://frisorlafata.dk"
echo ""
