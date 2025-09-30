# magellan
A wrapper over NuPACK to design orthogonal sequences.

## DNA Circuit Design Tool

### Quick Start

#### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the backend server
python3 -m backend.api.main
```

The backend will start on `http://localhost:8000`

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend will start on `http://localhost:3000` (or similar)

### Prerequisites

- Python 3.8+
- Node.js 16+
- Redis (for job management)

## Usage

1. Open the frontend in your browser
2. Design tab: Configure domains, strands, complexes, constraints, and
   off-targets
3. Click "Run" to submit a design job
4. Jobs tab: View job status and results

## Architecture

- **Backend**: FastAPI with NUPACK integration
- **Frontend**: React with Bootstrap
- **Storage**: Redis for job queue and results