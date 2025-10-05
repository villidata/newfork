#!/bin/bash

# Script to compare emergent.sh app preview vs VPS deployment
# This identifies differences in files and code between environments

echo "======================================"
echo "EMERGENT.SH vs VPS COMPARISON REPORT"
echo "======================================"
echo ""
echo "Generated on: $(date)"
echo ""

# Define directories
PREVIEW_FRONTEND="/app/frontend"
PREVIEW_BACKEND="/app/backend"
VPS_FRONTEND="/opt/frisor-frontend"
VPS_BACKEND="/opt/frisor-backend"

# Output file
REPORT_FILE="/app/comparison_report.md"

# Initialize report
cat > "$REPORT_FILE" << 'EOF'
# Emergent.sh Preview vs VPS Deployment Comparison Report

**Generated:** $(date)

---

## Executive Summary

This report compares the working app preview (emergent.sh) with the deployed VPS version to identify discrepancies.

---

EOF

echo "## FRONTEND COMPARISON" | tee -a "$REPORT_FILE"
echo "======================" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Check if directories exist
if [ ! -d "$PREVIEW_FRONTEND" ]; then
    echo "❌ Preview frontend directory not found: $PREVIEW_FRONTEND" | tee -a "$REPORT_FILE"
else
    echo "✅ Preview frontend found: $PREVIEW_FRONTEND" | tee -a "$REPORT_FILE"
fi

if [ ! -d "$VPS_FRONTEND" ]; then
    echo "❌ VPS frontend directory not found: $VPS_FRONTEND" | tee -a "$REPORT_FILE"
else
    echo "✅ VPS frontend found: $VPS_FRONTEND" | tee -a "$REPORT_FILE"
fi

echo "" | tee -a "$REPORT_FILE"

# Function to compare directories
compare_directories() {
    local preview_dir=$1
    local vps_dir=$2
    local label=$3
    
    echo "### $label Files Comparison" | tee -a "$REPORT_FILE"
    echo "" | tee -a "$REPORT_FILE"
    
    # Files only in preview (missing in VPS)
    echo "#### Files ONLY in Preview (Missing in VPS):" | tee -a "$REPORT_FILE"
    if [ -d "$preview_dir" ] && [ -d "$vps_dir" ]; then
        comm -23 <(cd "$preview_dir" && find . -type f | grep -v node_modules | grep -v build | grep -v dist | grep -v .git | sort) \
                 <(cd "$vps_dir" && find . -type f | grep -v node_modules | grep -v build | grep -v dist | grep -v .git | sort) | tee -a "$REPORT_FILE"
    else
        echo "Cannot compare - directory missing" | tee -a "$REPORT_FILE"
    fi
    echo "" | tee -a "$REPORT_FILE"
    
    # Files only in VPS (extra files)
    echo "#### Files ONLY in VPS (Extra files):" | tee -a "$REPORT_FILE"
    if [ -d "$preview_dir" ] && [ -d "$vps_dir" ]; then
        comm -13 <(cd "$preview_dir" && find . -type f | grep -v node_modules | grep -v build | grep -v dist | grep -v .git | sort) \
                 <(cd "$vps_dir" && find . -type f | grep -v node_modules | grep -v build | grep -v dist | grep -v .git | sort) | tee -a "$REPORT_FILE"
    else
        echo "Cannot compare - directory missing" | tee -a "$REPORT_FILE"
    fi
    echo "" | tee -a "$REPORT_FILE"
}

# Compare frontend directories
if [ -d "$PREVIEW_FRONTEND" ] && [ -d "$VPS_FRONTEND" ]; then
    compare_directories "$PREVIEW_FRONTEND" "$VPS_FRONTEND" "Frontend"
fi

echo "" | tee -a "$REPORT_FILE"
echo "## BACKEND COMPARISON" | tee -a "$REPORT_FILE"
echo "=====================" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Check backend directories
if [ ! -d "$PREVIEW_BACKEND" ]; then
    echo "❌ Preview backend directory not found: $PREVIEW_BACKEND" | tee -a "$REPORT_FILE"
else
    echo "✅ Preview backend found: $PREVIEW_BACKEND" | tee -a "$REPORT_FILE"
fi

if [ ! -d "$VPS_BACKEND" ]; then
    echo "❌ VPS backend directory not found: $VPS_BACKEND" | tee -a "$REPORT_FILE"
else
    echo "✅ VPS backend found: $VPS_BACKEND" | tee -a "$REPORT_FILE"
fi

echo "" | tee -a "$REPORT_FILE"

# Compare backend directories
if [ -d "$PREVIEW_BACKEND" ] && [ -d "$VPS_BACKEND" ]; then
    compare_directories "$PREVIEW_BACKEND" "$VPS_BACKEND" "Backend"
fi

echo "" | tee -a "$REPORT_FILE"
echo "## KEY FILES CONTENT COMPARISON" | tee -a "$REPORT_FILE"
echo "================================" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Compare critical files
compare_file() {
    local preview_file=$1
    local vps_file=$2
    local label=$3
    
    echo "### $label" | tee -a "$REPORT_FILE"
    
    if [ ! -f "$preview_file" ]; then
        echo "❌ Preview file not found: $preview_file" | tee -a "$REPORT_FILE"
    elif [ ! -f "$vps_file" ]; then
        echo "❌ VPS file not found: $vps_file" | tee -a "$REPORT_FILE"
    else
        # Check if files are identical
        if diff -q "$preview_file" "$vps_file" > /dev/null 2>&1; then
            echo "✅ Files are IDENTICAL" | tee -a "$REPORT_FILE"
        else
            echo "⚠️ Files are DIFFERENT" | tee -a "$REPORT_FILE"
            echo "" | tee -a "$REPORT_FILE"
            echo "**Line count difference:**" | tee -a "$REPORT_FILE"
            echo "- Preview: $(wc -l < "$preview_file") lines" | tee -a "$REPORT_FILE"
            echo "- VPS: $(wc -l < "$vps_file") lines" | tee -a "$REPORT_FILE"
            echo "" | tee -a "$REPORT_FILE"
            echo "**File size difference:**" | tee -a "$REPORT_FILE"
            echo "- Preview: $(du -h "$preview_file" | cut -f1)" | tee -a "$REPORT_FILE"
            echo "- VPS: $(du -h "$vps_file" | cut -f1)" | tee -a "$REPORT_FILE"
        fi
    fi
    echo "" | tee -a "$REPORT_FILE"
}

# Critical frontend files
echo "### Frontend Critical Files" | tee -a "$REPORT_FILE"
compare_file "$PREVIEW_FRONTEND/src/App.js" "$VPS_FRONTEND/src/App.js" "App.js"
compare_file "$PREVIEW_FRONTEND/src/index.js" "$VPS_FRONTEND/src/index.js" "index.js"
compare_file "$PREVIEW_FRONTEND/package.json" "$VPS_FRONTEND/package.json" "package.json"
compare_file "$PREVIEW_FRONTEND/.env" "$VPS_FRONTEND/.env" ".env"

# BookingSystem - the critical component
if [ -f "$PREVIEW_FRONTEND/src/components/BookingSystem.js" ] && [ -f "$VPS_FRONTEND/src/components/BookingSystem.js" ]; then
    echo "### 🎯 BookingSystem.js (CRITICAL)" | tee -a "$REPORT_FILE"
    compare_file "$PREVIEW_FRONTEND/src/components/BookingSystem.js" "$VPS_FRONTEND/src/components/BookingSystem.js" "BookingSystem.js"
fi

# Check for BookingModal vs BookingSystem confusion
if [ -f "$PREVIEW_FRONTEND/src/components/BookingModal.js" ]; then
    echo "### ⚠️ BookingModal.js in Preview" | tee -a "$REPORT_FILE"
    echo "Preview has BookingModal.js" | tee -a "$REPORT_FILE"
fi

if [ -f "$VPS_FRONTEND/src/components/BookingModal.js" ]; then
    echo "### ⚠️ BookingModal.js in VPS" | tee -a "$REPORT_FILE"
    echo "VPS has BookingModal.js" | tee -a "$REPORT_FILE"
fi

# Critical backend files
echo "### Backend Critical Files" | tee -a "$REPORT_FILE"
compare_file "$PREVIEW_BACKEND/server.py" "$VPS_BACKEND/server.py" "server.py"
compare_file "$PREVIEW_BACKEND/requirements.txt" "$VPS_BACKEND/requirements.txt" "requirements.txt"
compare_file "$PREVIEW_BACKEND/.env" "$VPS_BACKEND/.env" ".env"

echo "" | tee -a "$REPORT_FILE"
echo "## COMPONENT DIRECTORY COMPARISON" | tee -a "$REPORT_FILE"
echo "===================================" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# List all components in preview
echo "### Preview Components (/app/frontend/src/components/):" | tee -a "$REPORT_FILE"
if [ -d "$PREVIEW_FRONTEND/src/components" ]; then
    find "$PREVIEW_FRONTEND/src/components" -name "*.js" -o -name "*.jsx" | sort | sed 's|.*/||' | tee -a "$REPORT_FILE"
else
    echo "Directory not found" | tee -a "$REPORT_FILE"
fi
echo "" | tee -a "$REPORT_FILE"

# List all components in VPS
echo "### VPS Components (/opt/frisor-frontend/src/components/):" | tee -a "$REPORT_FILE"
if [ -d "$VPS_FRONTEND/src/components" ]; then
    find "$VPS_FRONTEND/src/components" -name "*.js" -o -name "*.jsx" | sort | sed 's|.*/||' | tee -a "$REPORT_FILE"
else
    echo "Directory not found" | tee -a "$REPORT_FILE"
fi
echo "" | tee -a "$REPORT_FILE"

echo "## PACKAGE DEPENDENCIES COMPARISON" | tee -a "$REPORT_FILE"
echo "====================================" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Compare package.json dependencies
if [ -f "$PREVIEW_FRONTEND/package.json" ] && [ -f "$VPS_FRONTEND/package.json" ]; then
    echo "### Frontend Dependencies Differences:" | tee -a "$REPORT_FILE"
    echo "" | tee -a "$REPORT_FILE"
    
    # Extract dependencies from both
    echo "**Preview package.json dependencies count:**" | tee -a "$REPORT_FILE"
    grep -c '"' "$PREVIEW_FRONTEND/package.json" | tee -a "$REPORT_FILE"
    
    echo "" | tee -a "$REPORT_FILE"
    echo "**VPS package.json dependencies count:**" | tee -a "$REPORT_FILE"
    grep -c '"' "$VPS_FRONTEND/package.json" | tee -a "$REPORT_FILE"
fi

echo "" | tee -a "$REPORT_FILE"
echo "## CONFIGURATION FILES" | tee -a "$REPORT_FILE"
echo "======================" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Check important config files
for config_file in "tailwind.config.js" "postcss.config.js" "craco.config.js"; do
    echo "### $config_file" | tee -a "$REPORT_FILE"
    
    preview_config="$PREVIEW_FRONTEND/$config_file"
    vps_config="$VPS_FRONTEND/$config_file"
    
    if [ -f "$preview_config" ] && [ -f "$vps_config" ]; then
        if diff -q "$preview_config" "$vps_config" > /dev/null 2>&1; then
            echo "✅ Identical" | tee -a "$REPORT_FILE"
        else
            echo "⚠️ Different" | tee -a "$REPORT_FILE"
        fi
    elif [ -f "$preview_config" ]; then
        echo "❌ Only in preview" | tee -a "$REPORT_FILE"
    elif [ -f "$vps_config" ]; then
        echo "❌ Only in VPS" | tee -a "$REPORT_FILE"
    else
        echo "❌ Not found in either location" | tee -a "$REPORT_FILE"
    fi
    echo "" | tee -a "$REPORT_FILE"
done

echo "" | tee -a "$REPORT_FILE"
echo "---" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"
echo "## RECOMMENDATIONS" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"
echo "1. Review files marked as 'DIFFERENT' or 'MISSING'" | tee -a "$REPORT_FILE"
echo "2. Pay special attention to BookingSystem.js differences" | tee -a "$REPORT_FILE"
echo "3. Check if any critical components are missing in VPS" | tee -a "$REPORT_FILE"
echo "4. Verify all dependencies are installed in VPS" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"
echo "**Report saved to:** $REPORT_FILE" | tee -a "$REPORT_FILE"

echo ""
echo "======================================"
echo "✅ COMPARISON COMPLETE"
echo "======================================"
echo ""
echo "📄 Full report saved to: $REPORT_FILE"
echo ""
echo "To view the report, run:"
echo "  cat $REPORT_FILE"
echo ""
