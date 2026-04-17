# Backend Server - Start Instructions

## ⚠️ Backend Not Running

The backend server needs to be started manually. Here's how:

## 🚀 Start Backend Server

### Option 1: Using Python Module (Recommended)
```powershell
# Navigate to project root
cd "C:\Users\deeks\OneDrive\Desktop\mini pro"

# Start backend server
python -m uvicorn backend.main:app --reload --port 8000
```

### Option 2: If uvicorn is installed globally
```powershell
cd "C:\Users\deeks\OneDrive\Desktop\mini pro"
uvicorn backend.main:app --reload --port 8000
```

## ⏱️ Initial Startup Time

**Important:** The backend takes 1-2 minutes to start because it:
- Trains ML pipelines
- Initializes database
- Loads models

You'll see output like:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## ✅ Verify Backend is Running

Once started, test these URLs:

1. **Health Check:**
   - http://localhost:8000/health
   - Should return: `{"status":"ok"}`

2. **API Documentation:**
   - http://localhost:8000/docs
   - Should show Swagger UI

## 🔄 After Backend Starts

1. **Refresh your frontend page**
2. **Try logging in again:**
   - Username: `admin`
   - Password: `admin123`

## 📝 Running Both Servers

You need **TWO terminal windows**:

**Terminal 1 - Backend:**
```powershell
cd "C:\Users\deeks\OneDrive\Desktop\mini pro"
python -m uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd "C:\Users\deeks\OneDrive\Desktop\mini pro\frontend"
npm run dev
```

## 🐛 Troubleshooting

**Error: "No module named 'uvicorn'"**
```powershell
pip install uvicorn fastapi
```

**Error: "Module not found"**
```powershell
pip install -r requirements.txt
```

**Port 8000 already in use:**
- Find what's using it: `netstat -ano | findstr :8000`
- Or use different port: `--port 8001`
- Update frontend `.env`: `VITE_API_URL=http://localhost:8001`

## ✅ Success!

When backend is running, you should see:
- ✅ Frontend can connect
- ✅ Login works
- ✅ API calls succeed








