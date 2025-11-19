#!/bin/bash
# Enhanced Log Anomaly Detection System - Installation Script
# Run this script to set up the enhanced system

echo "=================================================="
echo "  Enhanced Log Anomaly Detection System"
echo "  Installation and Setup"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}[1/5] Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Upgrade pip
echo -e "${YELLOW}[2/5] Upgrading pip...${NC}"
python3 -m pip install --upgrade pip

# Install requirements
echo -e "${YELLOW}[3/5] Installing dependencies...${NC}"
pip install -r requirements_enhanced.txt

echo ""
echo -e "${YELLOW}[4/5] Installing additional ML packages...${NC}"
# Install specific packages that might be missing
pip install river==0.22.0
pip install "scikit-learn>=1.6.0"
pip install psutil==5.9.6
# Note: No database packages needed - system is file-based!

echo ""
echo -e "${YELLOW}[5/5] Running system verification...${NC}"
python3 verify_and_benchmark.py

echo ""
echo "=================================================="
echo -e "${GREEN}  Installation Complete!${NC}"
echo "=================================================="
echo ""
echo "Next steps:"
echo "  1. Start the API:"
echo "     python app_enhanced.py"
echo ""
echo "  2. In another terminal, test it:"
echo "     python test_enhanced_system.py"
echo ""
echo "  3. View statistics:"
echo "     curl http://localhost:8000/v1/ai/stats"
echo ""
echo "Documentation:"
echo "  - README_ENHANCED.md - Complete guide"
echo "  - QUICK_START_GUIDE.md - Quick start"
echo "  - SYSTEM_VERIFICATION_REPORT.md - Detailed analysis"
echo ""
echo "=================================================="

