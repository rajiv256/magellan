## Step-by-Step Setup:

# 1. Create the project structure
mkdir -p {frontend/src/components,backend/core,backend/api,backend/data,scripts,docs}

# 2. Create React app
cd frontend
npx create-react-app . --template minimal
npm install lucide-react
cd ..

# 3. Create Python virtual environment
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install Flask Flask-CORS redis requests numpy biopython
pip freeze > requirements.txt
cd ..

## 4. Copy files from artifacts to their locations:
#
### FRONTEND FILES:
## Copy to: frontend/src/components/OligoDesignerV2.jsx
## Copy to: frontend/src/components/OligoDesignerV2.css
## Copy to: frontend/src/App.js
#
### BACKEND FILES:
## Copy to: backend/app.py
## Copy to: backend/config.py
#
### SETUP FILES:
## Copy to: scripts/setup.sh
#
## 5. Create empty __init__.py files
#touch backend/__init__.py
#touch backend/core/__init__.py
#touch backend/api/__init__.py
#
## 6. Make scripts executable
#chmod +x scripts/*.sh
#
### File Contents Guide:
#
#### frontend/src/index.js (create this):
#```javascript
#import React from 'react';
#import ReactDOM from 'react-dom/client';
#import './index.css';
#import App from './App';
#
#const root = ReactDOM.createRoot(document.getElementById('root'));
#root.render(
#  <React.StrictMode>
#    <App />
#  </React.StrictMode>
#);
#```
#
#### frontend/public/index.html (create this):
#```html
#<!DOCTYPE html>
#<html lang="en">
#  <head>
#    <meta charset="utf-8" />
#    <meta name="viewport" content="width=device-width, initial-scale=1" />
#    <title>OligoDesigner V2</title>
#  </head>
#  <body>
#    <div id="root"></div>
#  </body>
#</html>
#```
#
#### .env (create this):
#```bash
## Backend settings
#FLASK_ENV=development
#FLASK_DEBUG=True
#FLASK_HOST=localhost
#FLASK_PORT=5000
#
## Redis settings
#REDIS_HOST=localhost
#REDIS_PORT=6379
#REDIS_DB=0
#
## CORS settings
#CORS_ORIGINS=http://localhost:3000
#```
#
#### scripts/start-backend.sh:
#```bash
##!/bin/bash
#cd backend
#source venv/bin/activate
#echo "🐍 Starting Python backend on port 5000..."
#python app.py
#```
#
#### scripts/start-frontend.sh:
#```bash
##!/bin/bash
#cd frontend
#echo "⚛️ Starting React frontend on port 3000..."
#npm start
#```
#
### Quick Start Commands:
#
## Setup everything
#chmod +x scripts/setup.sh
#./scripts/setup.sh
#
## Start Redis (choose one):
#brew services start redis              # macOS
#sudo systemctl start redis-server     # Ubuntu
#docker run -d -p 6379:6379 redis     # Docker
#
## Start backend (Terminal 1)
#./scripts/start-backend.sh
#
## Start frontend (Terminal 2)
#./scripts/start-frontend.sh
#
## Access the app:
## Frontend: http://localhost:3000
## Backend API: http://localhost:5000
## Health check: http://localhost:5000/health