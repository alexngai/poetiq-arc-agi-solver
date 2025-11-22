#!/bin/bash

# Setup script for Poetiq ARC-AGI Solver

set -e

echo "========================================="
echo "Poetiq ARC-AGI Solver Setup"
echo "========================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Detected Python version: $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created. Please edit it and add your API keys."
else
    echo ""
    echo "✓ .env file already exists."
fi

# Create output directory
mkdir -p output
echo "✓ Created output directory"

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Activate the virtual environment: source .venv/bin/activate"
echo "3. Run the solver: python main.py"
echo ""
echo "For more information, see the README.md file."
