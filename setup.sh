#!/bin/bash

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo "================================================"
echo "         Magellan Setup Script"
echo "    DNA Circuit Design Tool - NUPACK Wrapper"
echo "================================================"
echo ""

# Check if running from project root
if [ ! -f "setup.sh" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Check Python
print_status "Checking Python installation..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
    print_success "Python $PYTHON_VERSION found"
else
    print_error "Python 3 not found. Please install Python 3.8 or higher"
    exit 1
fi

# Check Python version
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
    print_error "Python 3.8 or higher is required (found Python $PYTHON_MAJOR.$PYTHON_MINOR)"
    exit 1
fi

# Check Node.js
print_status "Checking Node.js installation..."
if command_exists node; then
    NODE_VERSION=$(node --version)
    print_success "Node.js $NODE_VERSION found"
else
    print_error "Node.js not found. Please install Node.js 16 or higher"
    exit 1
fi

# Check npm
print_status "Checking npm installation..."
if command_exists npm; then
    NPM_VERSION=$(npm --version)
    print_success "npm $NPM_VERSION found"
else
    print_error "npm not found. Please install npm"
    exit 1
fi

# Check Redis
print_status "Checking Redis installation..."
if command_exists redis-server; then
    REDIS_VERSION=$(redis-server --version | awk '{print $3}' | cut -d '=' -f 2)
    print_success "Redis $REDIS_VERSION found"

    # Check if Redis is running
    if redis-cli ping >/dev/null 2>&1; then
        print_success "Redis server is already running"
    else
        print_warning "Redis is not running. Starting Redis..."
        redis-server --daemonize yes
        sleep 2
        if redis-cli ping >/dev/null 2>&1; then
            print_success "Redis server started successfully"
        else
            print_error "Failed to start Redis server"
            exit 1
        fi
    fi
else
    print_error "Redis not found. Please install Redis"
    echo "  macOS: brew install redis"
    echo "  Ubuntu: sudo apt-get install redis-server"
    echo "  Other: https://redis.io/download"
    exit 1
fi

# Install Python dependencies
print_status "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Python dependencies installed"
else
    print_warning "requirements.txt not found, skipping Python dependencies"
fi

# Check NUPACK installation
print_status "Checking NUPACK installation..."
if python3 -c "import nupack" 2>/dev/null; then
    NUPACK_VERSION=$(python3 -c "import nupack; print(nupack.__version__)" 2>/dev/null || echo "unknown")
    print_success "NUPACK $NUPACK_VERSION found"
else
    print_error "NUPACK not found or not properly installed"
    echo "Please install NUPACK from: http://www.nupack.org/downloads"
    echo "After installation, add NUPACK to your Python path"
    exit 1
fi

# Install frontend dependencies
print_status "Installing frontend dependencies..."
if [ -d "frontend" ]; then
    cd frontend
    npm install
    print_success "Frontend dependencies installed"
    cd ..
else
    print_error "frontend directory not found"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating .env file..."
    cat > .env << EOF
# Backend Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
API_PORT=8000

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
EOF
    print_success ".env file created"
else
    print_warning ".env file already exists, skipping creation"
fi

# Create logs directory
if [ ! -d "logs" ]; then
    mkdir -p logs
    print_success "Logs directory created"
fi

echo ""
echo "================================================"
print_success "Setup completed successfully!"
echo "================================================"
echo ""
echo "To start Magellan:"
echo ""
echo "1. Start the backend (from project root):"
echo "   ${GREEN}python3 -m backend.api.main${NC}"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   ${GREEN}cd frontend && npm run dev${NC}"
echo ""
echo "3. Open your browser to:"
echo "   ${BLUE}http://localhost:3000${NC}"
echo ""
echo "For more information, see README.md"
echo ""

# Ask if user wants to start services now
read -p "Would you like to start the services now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Starting backend server..."

    # Start backend in background
    python3 -m backend.api.main > logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > .backend.pid

    sleep 3

    # Check if backend started successfully
    if ps -p $BACKEND_PID > /dev/null; then
        print_success "Backend server started (PID: $BACKEND_PID)"
        print_success "Backend logs: logs/backend.log"
    else
        print_error "Failed to start backend server. Check logs/backend.log for details"
        exit 1
    fi

    print_status "Starting frontend server..."
    cd frontend
    npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../.frontend.pid
    cd ..

    sleep 3

    if ps -p $FRONTEND_PID > /dev/null; then
        print_success "Frontend server started (PID: $FRONTEND_PID)"
        print_success "Frontend logs: logs/frontend.log"
    else
        print_error "Failed to start frontend server. Check logs/frontend.log for details"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi

    echo ""
    print_success "All services started successfully!"
    echo ""
    echo "Access Magellan at: ${BLUE}http://localhost:3000${NC}"
    echo ""
    echo "To stop services:"
    echo "  kill \$(cat .backend.pid .frontend.pid)"
    echo ""
else
    print_status "Services not started. Use the commands above to start manually."
fi