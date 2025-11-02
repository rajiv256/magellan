#!/bin/bash

set -e  # Exit on error

# Print output functions (without colors)
print_status() {
    echo "[INFO] $1"
}

print_success() {
    echo "[SUCCESS] $1"
}

print_warning() {
    echo "[WARNING] $1"
}

print_error() {
    echo "[ERROR] $1"
}

# Banner
echo "================================================"
echo "         Magellan Run Script"
echo "    DNA Circuit Design Tool - NUPACK Wrapper"
echo "================================================"
echo ""

# Check if running from project root
if [ ! -f "run.sh" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to stop services
stop_services() {
    print_status "Stopping any running services..."

    # Check for PID files in the logs directory
    if [ -f "logs/backend.pid" ]; then
        BACKEND_PID=$(cat logs/backend.pid 2>/dev/null)
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            print_status "Stopping backend (PID: $BACKEND_PID)"
            kill $BACKEND_PID 2>/dev/null
            sleep 1
        else
            print_warning "Backend process not found"
        fi
        rm -f logs/backend.pid
    else
        print_warning "Backend PID file not found"
    fi

    if [ -f "logs/frontend.pid" ]; then
        FRONTEND_PID=$(cat logs/frontend.pid 2>/dev/null)
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            print_status "Stopping frontend (PID: $FRONTEND_PID)"
            kill $FRONTEND_PID 2>/dev/null
            sleep 1
        else
            print_warning "Frontend process not found"
        fi
        rm -f logs/frontend.pid
    else
        print_warning "Frontend PID file not found"
    fi

    # Find and kill any remaining processes by command pattern
    BACKEND_PIDS=$(pgrep -f "python3 -m backend.api.main" 2>/dev/null || true)
    if [ -n "$BACKEND_PIDS" ]; then
        print_status "Killing remaining backend processes..."
        echo $BACKEND_PIDS | xargs kill 2>/dev/null || true
    fi

    FRONTEND_PIDS=$(pgrep -f "npm run dev" 2>/dev/null || true)
    if [ -n "$FRONTEND_PIDS" ]; then
        print_status "Killing remaining frontend processes..."
        echo $FRONTEND_PIDS | xargs kill 2>/dev/null || true
    fi

    print_success "Services stopped"
}

# Function to start services
start_services() {
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi

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

    # Create logs directory if it doesn't exist
    if [ ! -d "logs" ]; then
        mkdir -p logs
        print_success "Logs directory created"
    fi

    # Create a hidden file to store last run time
    mkdir -p logs/.data
    TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
    echo $TIMESTAMP > logs/.data/last_run.txt

    # First stop any running services to avoid conflicts
    stop_services

    # Start backend in background
    print_status "Starting backend server..."
    python3 -m backend.api.main > logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > logs/backend.pid  # Write PID to logs directory

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
    echo $FRONTEND_PID > ../logs/frontend.pid  # Write PID to logs directory
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
    echo "Access Magellan at: http://localhost:3000"
    echo ""
}

# Function to display usage
show_usage() {
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start    Start all services"
    echo "  stop     Stop all services"
    echo "  help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run.sh start     # Start all services"
    echo "  ./run.sh stop      # Stop all services"
    echo ""
    echo "To view logs:"
    echo "  Backend: tail -f logs/backend.log"
    echo "  Frontend: tail -f logs/frontend.log"
    echo ""
}

# Main command processing
if [ $# -eq 0 ]; then
    # No arguments provided, show usage
    show_usage
    exit 0
fi

# Parse command
case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    help)
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac

exit 0