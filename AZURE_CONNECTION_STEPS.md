# Step-by-Step Guide: Connecting to Azure Blob Storage

Follow these steps to connect your application to Azure Blob Storage.

## Step 1: Install Azure Storage SDK

First, make sure the Azure Storage library is installed:

```bash
pip install azure-storage-blob>=12.19.0
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Step 2: Create Azure Storage Account

### 2.1 Sign in to Azure Portal
1. Go to https://portal.azure.com
2. Sign in with your Azure account

### 2.2 Create Storage Account
1. Click **"Create a resource"** (top left)
2. Search for **"Storage account"**
3. Click **"Create"**
4. Fill in the form:

   **Basics Tab:**
   - **Subscription**: Select your subscription
   - **Resource group**: 
     - Click "Create new"
     - Name: `hireflow-rg` (or any name)
   - **Storage account name**: 
     - Must be globally unique
     - Use lowercase letters and numbers only
     - Example: `hireflowresumes2024`
   - **Region**: Choose closest to you (e.g., `East US`, `West Europe`)
   - **Performance**: **Standard**
   - **Redundancy**: **Locally-redundant storage (LRS)** (cheapest option)

5. Click **"Review + create"**
6. Click **"Create"**
7. Wait for deployment (1-2 minutes)
8. Click **"Go to resource"**

## Step 3: Get Connection String

1. In your Storage Account, go to **"Access keys"** (left sidebar, under Security + networking)
2. Under **"key1"**, click **"Show"** next to "Connection string"
3. Click the **copy icon** to copy the connection string
   - It looks like: `DefaultEndpointsProtocol=https;AccountName=hireflowresumes2024;AccountKey=xxxxx...;EndpointSuffix=core.windows.net`

## Step 4: Create Container

1. In your Storage Account, go to **"Containers"** (left sidebar, under Data storage)
2. Click **"+ Container"**
3. Fill in:
   - **Name**: `resumes` (or any name you prefer)
   - **Public access level**: **Private (no anonymous access)** ✅ **IMPORTANT for security**
4. Click **"Create"**

## Step 5: Configure Environment Variables

### 5.1 Create/Update .env File

Create a `.env` file in your project root (`F:\mini pro\.env`) if it doesn't exist, or add these lines to your existing `.env`:

```env
# Azure Blob Storage Configuration
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=YOUR_ACCOUNT_NAME;AccountKey=YOUR_ACCOUNT_KEY;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER_NAME=resumes
```

**Replace:**
- `YOUR_ACCOUNT_NAME` with your storage account name
- `YOUR_ACCOUNT_KEY` with the key from Step 3

**Example:**
```env
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=hireflowresumes2024;AccountKey=abc123xyz789...;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER_NAME=resumes
```

### 5.2 Verify .env File Location

Make sure the `.env` file is in the project root:
```
F:\mini pro\
  ├── .env          ← Should be here
  ├── backend/
  ├── frontend 1/
  └── requirements.txt
```

## Step 6: Test the Connection

### 6.1 Restart Your Backend Server

Stop your current backend server (if running) and restart it:

```bash
# Navigate to project root
cd "F:\mini pro"

# Activate virtual environment (if using one)
# venv\Scripts\activate  (Windows)

# Start the backend
cd backend
python main.py
# OR
uvicorn main:app --reload
```

### 6.2 Check Startup Logs

Look for these messages in the console:

**✅ Success:**
```
[INFO] Azure Blob Storage initialized successfully
```

**⚠️ Fallback (if Azure not configured):**
```
Warning: Azure Blob Storage initialization failed: ...
Falling back to local file storage
```

### 6.3 Test Upload

1. Start your frontend application
2. Go to the candidate portal or recruiter dashboard
3. Upload a test resume
4. Check the database - the `resume_path` should now be an Azure URL like:
   ```
   https://hireflowresumes2024.blob.core.windows.net/resumes/12345678-1234-1234-1234-123456789abc.pdf
   ```

## Step 7: Verify Files in Azure

1. Go back to Azure Portal
2. Navigate to your Storage Account
3. Go to **"Containers"** → **"resumes"**
4. You should see uploaded files listed there

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'azure'"

**Solution:**
```bash
pip install azure-storage-blob
```

### Issue: "Azure Blob Storage initialization failed"

**Check:**
1. Connection string is correct (no extra spaces)
2. Storage account name matches
3. Account key is correct
4. Container name matches
5. Internet connection is working

**Test connection string manually:**
```python
from azure.storage.blob import BlobServiceClient

connection_string = "YOUR_CONNECTION_STRING"
blob_service = BlobServiceClient.from_connection_string(connection_string)
containers = blob_service.list_containers()
print("Connected! Containers:", [c.name for c in containers])
```

### Issue: "Container not found"

**Solution:**
- The code will try to create it automatically
- If it fails, manually create the container in Azure Portal (Step 4)

### Issue: Files still saving locally

**Check:**
1. `.env` file is in the correct location
2. Environment variables are loaded (restart backend after adding .env)
3. Connection string format is correct
4. No typos in variable names

## Security Checklist

- ✅ Never commit `.env` file to Git
- ✅ Use Private containers (not public)
- ✅ Keep connection string secret
- ✅ Consider using Azure Key Vault for production
- ✅ Add `.env` to `.gitignore` if not already there

## Next Steps After Connection

Once connected, you can:

1. **Monitor Usage**: Check Azure Portal → Storage account → Metrics
2. **Set Up Lifecycle Policies**: Automatically delete old files
3. **Enable CDN**: For faster file access globally
4. **Set Up Backups**: Configure backup policies
5. **Monitor Costs**: Check Azure Cost Management

## Cost Monitoring

Azure Blob Storage is very affordable:
- **Storage**: ~$0.0184 per GB/month
- **Transactions**: ~$0.004 per 10,000 operations
- **First 5GB data transfer free per month**

For 1000 resumes (~50MB):
- **Monthly cost: ~$0.001** (less than 1 cent!)

## Support

If you encounter issues:
1. Check Azure Portal → Storage account → Activity log
2. Check backend console logs
3. Verify `.env` file format
4. Test connection string manually (see troubleshooting above)

---

**Quick Reference:**

```bash
# Install
pip install azure-storage-blob

# .env file
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=xxx;AccountKey=xxx;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER_NAME=resumes

# Restart backend
python backend/main.py
```

