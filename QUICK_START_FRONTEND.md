# Quick Start - Frontend

## ⚠️ Node.js Required

The frontend requires **Node.js** to be installed. 

### Check if Node.js is Installed

Open PowerShell and run:
```powershell
node --version
```

If you see a version number (e.g., `v20.10.0`), Node.js is installed! ✅

If you get an error, Node.js is not installed. ❌

---

## 📥 Install Node.js (If Needed)

1. **Download:** https://nodejs.org/ (LTS version)
2. **Install:** Run the installer
3. **Restart:** Close and reopen your terminal
4. **Verify:** Run `node --version` again

---

## 🚀 Run Frontend (After Node.js Installation)

### Option 1: Step by Step
```powershell
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies (first time only)
npm install

# 3. Start development server
npm run dev
```

### Option 2: One Command (if already in frontend directory)
```powershell
npm install && npm run dev
```

---

## ✅ Success Indicators

After running `npm run dev`, you should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

Then open **http://localhost:3000** in your browser!

---

## 🔐 Login Credentials

- **Username:** `admin`
- **Password:** `admin123`

---

## 📝 Notes

- The frontend runs on port **3000**
- Backend should be running on port **8000**
- First `npm install` may take 1-2 minutes
- Development server auto-reloads on file changes

