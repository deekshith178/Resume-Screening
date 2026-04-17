# How to Start the Backend Server

## Quick Start

```powershell
# From project root directory
python -m uvicorn backend.main:app --reload --port 8000
```

Or if uvicorn is installed globally:
```powershell
uvicorn backend.main:app --reload --port 8000
```

## Verify Backend is Running

1. **Check Health Endpoint:**
   - Open browser: http://localhost:8000/health
   - Should return: `{"status":"ok"}`

2. **Check API Docs:**
   - Open browser: http://localhost:8000/docs
   - Should show FastAPI Swagger UI

## Backend Features

- ✅ CORS enabled (allows frontend connections)
- ✅ Authentication endpoints
- ✅ Job management
- ✅ Resume processing
- ✅ Guidance engine with SERP API

## Troubleshooting

**Port 8000 already in use:**
```powershell
# Use a different port
python -m uvicorn backend.main:app --reload --port 8001
```

Then update frontend `.env`:
```
VITE_API_URL=http://localhost:8001
```

**Module not found errors:**
```powershell
# Install dependencies
pip install -r requirements.txt
```

**Database errors:**
- Database file will be created automatically on first run
- Located at: `guidance_demo.db`

## Running Both Frontend and Backend

**Terminal 1 (Backend):**
```powershell
cd "C:\Users\deeks\OneDrive\Desktop\mini pro"
python -m uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```powershell
cd "C:\Users\deeks\OneDrive\Desktop\mini pro\frontend"
npm run dev
```

Then:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000 (or 3001, 3002, etc.)








