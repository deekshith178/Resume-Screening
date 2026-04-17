# Backend Start - Fixed Command

## ❌ Wrong Way (from backend directory):
```powershell
cd backend
python -m uvicorn backend.main:app --reload --port 8000
# Error: No module named 'backend'
```

## ✅ Correct Way (from project root):
```powershell
cd "C:\Users\deeks\OneDrive\Desktop\mini pro"
python -m uvicorn backend.main:app --reload --port 8000
```

## Why?

The command `backend.main:app` expects to find the `backend` module, which is only available when running from the **project root directory**, not from inside the `backend` folder.

## Directory Structure:
```
mini pro/                    ← Run command from HERE
├── backend/
│   ├── main.py
│   └── ...
├── frontend/
└── ...
```

## Quick Start:

1. **Open PowerShell**
2. **Navigate to project root:**
   ```powershell
   cd "C:\Users\deeks\OneDrive\Desktop\mini pro"
   ```
3. **Start backend:**
   ```powershell
   python -m uvicorn backend.main:app --reload --port 8000
   ```

## Expected Output:

```
INFO:     Will watch for changes in these directories: ['C:\\Users\\deeks\\OneDrive\\Desktop\\mini pro']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
[startup] Demo candidate 'cand_xyz' token...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## After Backend Starts:

1. Wait for "Application startup complete" message
2. Test: http://localhost:8000/health
3. Refresh frontend and try login








