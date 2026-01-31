#!/bin/bash

# Abby Unleashed Core - Setup Script

echo "🚀 Setting up Abby Unleashed Core..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama not found. Please install from https://ollama.ai/"
    echo "   After installation, run: ollama serve"
else
    echo "✓ Ollama found"
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✓ Created .env file"
else
    echo "✓ .env file already exists"
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/embeddings
mkdir -p logs
mkdir -p persona_library/personas

# Check if Ollama is running and pull default model
if command -v ollama &> /dev/null; then
    echo "🤖 Checking Ollama models..."
    
    # Try to pull default model
    if ollama list | grep -q "qwen2.5"; then
        echo "✓ Default model already available"
    else
        echo "📥 Pulling default model (this may take a while)..."
        ollama pull qwen2.5:latest
    fi
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To get started:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Start Ollama (if not running):"
echo "     ollama serve"
echo ""
echo "  3. Run Abby in text mode:"
echo "     python cli.py text"
echo ""
echo "  4. Or run tests:"
echo "     pytest tests/"
echo ""
echo "Enjoy using Abby Unleashed! 🚀"
