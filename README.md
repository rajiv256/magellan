# Magellan

A wrapper over NUPACK for designing orthogonal DNA sequences with
enhanced usability and the ability to re-use Design specifications.

_Note: Hybrid development  between my natural intelligence and Claude's 
artificial intelligence._

## Features

- **Intuitive Web Interface**: Design DNA circuits through a modern React
  frontend
- **Custom Concentrations**: Specify custom concentration values for each 
  complex.
- **Reload Parameters**: Reload Parameters from an old Job into the Design Tab 
  in UI!
- **Job Queue Management**: Redis-backed asynchronous job processing
- **Results Visualization**: View and analyze design results through the web
  interface

## Quick Start

### Automated Setup (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd magellan

source venv/bin/activate

# You need to download NUPACK from the official website
# and substitute the root folder path with $NUPACK_ROOT
python3 -m pip install -U nupack -f $NUPACK_ROOT/package

# Run the setup script
chmod +x setup.sh
./setup.sh
```

The setup script will:

- Check and install system dependencies (Python, Node.js, Redis)
- Install Python packages
- Install frontend dependencies
- Verify NUPACK installation
- Start both backend and frontend servers

### Manual Setup

See the [Manual Installation](#manual-installation) section below.

## Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **Redis** (for job queue management)
- **NUPACK** (molecular design suite)

## Manual Installation

### 1. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify NUPACK is installed
python -c "import nupack; print(nupack.__version__)"

# Start Redis (if not already running)
redis-server

# Run the backend API (must run from project root)
python3 -m backend.api.main
```

The backend will start on `http://localhost:8000`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will start on `http://localhost:3000`

## Usage

### Basic Workflow

1. **Access the Interface**: Open `http://localhost:3000` in your browser

2. **Design Tab**: Configure your DNA circuit design
    - **Domains**: Define sequence domains with custom concentrations
    - **Strands**: Compose strands from domains
    - **Complexes**: Specify target complex structures
    - **Constraints**: Set design constraints (GC content, temperature, etc.)
    - **Off-Targets**: Define structures to avoid

3. **Submit Job**: Click "Run" to submit your design job to the queue

4. **Monitor Progress**: Switch to "Jobs" tab to view:
    - Job status (queued, running, completed, failed)
    - Real-time progress updates
    - Results and sequence outputs

## Architecture

### Backend

- **Framework**: FastAPI
- **Task Queue**: Redis + background workers
- **Design Engine**: NUPACK integration
- **API Endpoints**:
    - `POST /api/design` - Submit new design job
    - `GET /api/jobs` - List all jobs
    - `GET /api/jobs/{job_id}` - Get job details
    - `GET /api/jobs/{job_id}/results` - Retrieve results

### Frontend

- **Framework**: React
- **UI Library**: Bootstrap
- **State Management**: React hooks
- **API Client**: Axios

### Storage

- **Redis**: Job queue, status tracking, and results caching

### API Documentation

With the backend running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Environment Variables

Create a `.env` file in the project root:

```bash
# Backend
REDIS_HOST=localhost
REDIS_PORT=6379
NUPACK_HOME=/path/to/nupack
API_PORT=8000

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

## Troubleshooting

### NUPACK Not Found

Ensure NUPACK is properly installed and accessible:

```bash
# Check NUPACK installation
python -c "import nupack; print(nupack.__version__)"
# If not found, install NUPACK following official documentation
# http://www.nupack.org/downloads
```

### Redis Connection Error

```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Start Redis if not running
redis-server
```

### Port Already in Use

```bash
# Backend (port 8000)
lsof -ti:8000 | xargs kill -9

# Frontend (port 3000)
lsof -ti:3000 | xargs kill -9
```

### Module Import Errors

Ensure you're running the API from the project root:

```bash
python3 -m backend.api.main
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request