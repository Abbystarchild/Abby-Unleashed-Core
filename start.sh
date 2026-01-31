#!/bin/bash
# Startup script for Abby Unleashed Core with validation

set -e

echo "🚀 Abby Unleashed Core - Startup Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check Python version
echo ""
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.9.0"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then 
    print_status "Python $PYTHON_VERSION detected"
else
    print_error "Python 3.9+ required. Found: $PYTHON_VERSION"
    exit 1
fi

# Check if .env exists
echo ""
echo "Checking environment configuration..."
if [ ! -f .env ]; then
    print_warning ".env file not found"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    print_status ".env file created"
    print_warning "Please edit .env file with your configuration"
else
    print_status ".env file found"
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Validate OLLAMA_HOST
echo ""
echo "Validating Ollama connection..."
OLLAMA_HOST=${OLLAMA_HOST:-"http://localhost:11434"}
echo "Checking Ollama at: $OLLAMA_HOST"

if command -v curl &> /dev/null; then
    if curl -s --connect-timeout 5 "$OLLAMA_HOST" > /dev/null 2>&1; then
        print_status "Ollama is accessible"
    else
        print_error "Cannot connect to Ollama at $OLLAMA_HOST"
        echo ""
        echo "Please ensure:"
        echo "  1. Ollama is installed (https://ollama.ai)"
        echo "  2. Ollama service is running: ollama serve"
        echo "  3. OLLAMA_HOST in .env is correct"
        exit 1
    fi
else
    print_warning "curl not found, skipping Ollama connectivity check"
fi

# Check if dependencies are installed
echo ""
echo "Checking Python dependencies..."
if python3 -c "import ollama, pyyaml, dotenv" 2>/dev/null; then
    print_status "Core dependencies installed"
else
    print_warning "Some dependencies missing"
    echo "Installing dependencies..."
    pip install -q -r requirements.txt
    print_status "Dependencies installed"
fi

# Create necessary directories
echo ""
echo "Setting up directories..."
mkdir -p memory/storage
mkdir -p persona_library/personas
mkdir -p logs
print_status "Directories created"

# Check for Ollama models
echo ""
echo "Checking Ollama models..."
if command -v ollama &> /dev/null; then
    MODEL_LIST=$(ollama list 2>/dev/null || echo "")
    if [ -z "$MODEL_LIST" ]; then
        print_warning "No Ollama models found"
        echo ""
        echo "Recommended models:"
        echo "  ollama pull qwen2.5:latest      # General purpose"
        echo "  ollama pull qwen2.5-coder:latest # Code generation"
        echo ""
    else
        print_status "Ollama models found"
    fi
else
    print_warning "ollama CLI not found"
fi

# Validate configuration files
echo ""
echo "Validating configuration files..."
for config_file in config/brain_clone.yaml config/system_config.yaml config/ollama_models.yaml; do
    if [ -f "$config_file" ]; then
        print_status "$config_file exists"
    else
        print_warning "$config_file not found"
    fi
done

# Check for audio devices (for voice mode)
echo ""
echo "Checking audio devices..."
if command -v pactl &> /dev/null; then
    if pactl list sources short > /dev/null 2>&1; then
        print_status "Audio input devices detected"
    else
        print_warning "No audio input devices found"
    fi
    if pactl list sinks short > /dev/null 2>&1; then
        print_status "Audio output devices detected"
    else
        print_warning "No audio output devices found"
    fi
else
    print_warning "PulseAudio not detected (voice mode may not work)"
fi

# Display startup options
echo ""
echo "========================================"
echo "Setup complete! 🎉"
echo ""
echo "Available modes:"
echo "  1. Text Mode (default):  python cli.py text"
echo "  2. Voice Mode:           python cli.py voice"
echo "  3. Direct Task:          python cli.py task --task 'your task'"
echo ""
echo "Docker options:"
echo "  - Build and run:         docker-compose up --build"
echo "  - Run in background:     docker-compose up -d"
echo "  - View logs:             docker-compose logs -f"
echo "  - Stop:                  docker-compose down"
echo ""

# Parse command line arguments
MODE=${1:-text}
TASK=${2:-}

# Start the application
if [ "$MODE" = "docker" ]; then
    echo "Starting with Docker..."
    docker-compose up --build
elif [ "$MODE" = "task" ] && [ ! -z "$TASK" ]; then
    echo "Executing task: $TASK"
    python3 cli.py task --task "$TASK"
else
    echo "Starting Abby Unleashed in $MODE mode..."
    python3 cli.py "$MODE"
fi

# Check if API server mode
if [ "$MODE" = "api" ]; then
    echo "Starting Abby Unleashed API Server..."
    echo ""
    echo "📱 Mobile Access:"
    echo "  1. Find your PC IP address"
    echo "  2. On your phone, navigate to: http://YOUR-PC-IP:8080"
    echo "  3. Make sure phone and PC are on same WiFi"
    echo ""
    python3 api_server.py --host 0.0.0.0 --port 8080
    exit 0
fi
