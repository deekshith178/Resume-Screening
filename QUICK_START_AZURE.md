# Quick Start: Connect to Azure Blob Storage

## ✅ What's Already Done
- ✅ Code integration complete
- ✅ Storage service created
- ✅ Upload/download endpoints updated
- ✅ Automatic fallback to local storage

## 📋 Next Steps (Do These Now)

### Step 1: Install Azure SDK (2 minutes)
```bash
pip install azure-storage-blob
```

### Step 2: Create Azure Storage Account (5 minutes)

1. **Go to Azure Portal**: https://portal.azure.com
2. **Create Storage Account**:
   - Click "Create a resource" → Search "Storage account" → Create
   - **Name**: `hireflowresumes` (must be unique, lowercase, no spaces)
   - **Region**: Choose closest to you
   - **Performance**: Standard
   - **Redundancy**: LRS (cheapest)
   - Click "Review + create" → "Create"

### Step 3: Get Connection String (2 minutes)

1. In your Storage Account → **"Access keys"** (left menu)
2. Click **"Show"** next to "key1"
3. **Copy** the "Connection string" (looks like: `DefaultEndpointsProtocol=https;AccountName=...`)

### Step 4: Create Container (1 minute)

1. In Storage Account → **"Containers"** (left menu)
2. Click **"+ Container"**
3. **Name**: `resumes`
4. **Public access**: **Private** ✅
5. Click **"Create"**

### Step 5: Add to .env File (2 minutes)

Create or edit `.env` file in project root (`F:\mini pro\.env`):

```env
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=YOUR_ACCOUNT_NAME;AccountKey=YOUR_KEY;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER_NAME=resumes
```

**Replace:**
- `YOUR_ACCOUNT_NAME` = Your storage account name
- `YOUR_KEY` = The key from Step 3

### Step 6: Restart Backend (1 minute)

```bash
# Stop current backend (Ctrl+C)
# Then restart:
cd backend
python main.py
```

### Step 7: Test It! (2 minutes)

1. Upload a resume through the app
2. Check Azure Portal → Containers → resumes
3. You should see the file there! ✅

## 🎯 Total Time: ~15 minutes

## ⚠️ Common Issues

**"Module not found"**
→ Run: `pip install azure-storage-blob`

**"Connection failed"**
→ Check connection string in .env (no extra spaces)

**"Container not found"**
→ Create it manually in Azure Portal (Step 4)

**Files still saving locally**
→ Restart backend after adding .env

## 📝 Example .env File

```env
# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=hireflowresumes;AccountKey=abc123xyz==;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER_NAME=resumes

# Other existing variables...
SERPAPI_KEY=your_serpapi_key
DATABASE_URL=sqlite:///./hireflow.db
```

## ✅ Verification Checklist

- [ ] Azure SDK installed
- [ ] Storage account created
- [ ] Connection string copied
- [ ] Container created (named "resumes")
- [ ] .env file created with connection string
- [ ] Backend restarted
- [ ] Test upload successful
- [ ] File visible in Azure Portal

## 🚀 You're Done!

Once all steps are complete, all new resume uploads will automatically go to Azure Blob Storage!

