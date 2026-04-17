# Azure Blob Storage Setup Guide

This guide explains how to configure Azure Blob Storage for resume file storage in the application.

## Overview

The application now supports storing resume files in Azure Blob Storage instead of local filesystem. When Azure is configured, all uploaded resumes are stored in Azure Blob Storage. If Azure is not configured, the system falls back to local file storage.

## Prerequisites

1. An Azure account with an active subscription
2. An Azure Storage Account
3. Python package: `azure-storage-blob>=12.19.0` (already added to requirements.txt)

## Setup Steps

### 1. Create Azure Storage Account

1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource"
3. Search for "Storage account" and select it
4. Click "Create"
5. Fill in the required details:
   - **Subscription**: Select your subscription
   - **Resource group**: Create new or use existing
   - **Storage account name**: Choose a unique name (e.g., `hireflowresumes`)
   - **Region**: Choose closest region
   - **Performance**: Standard
   - **Redundancy**: LRS (Locally Redundant Storage) is sufficient for most cases
6. Click "Review + create", then "Create"

### 2. Get Connection String

1. Navigate to your Storage Account in Azure Portal
2. Go to "Access keys" in the left menu
3. Click "Show" next to "key1" to reveal the connection string
4. Copy the connection string (it looks like: `DefaultEndpointsProtocol=https;AccountName=...`)

### 3. Create Container

1. In your Storage Account, go to "Containers" in the left menu
2. Click "+ Container"
3. Enter container name: `resumes` (or any name you prefer)
4. Set Public access level to "Private" (recommended for security)
5. Click "Create"

### 4. Configure Environment Variables

Create or update your `.env` file in the project root:

```env
# Azure Blob Storage Configuration
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=your_account_name;AccountKey=your_account_key;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER_NAME=resumes
```

**Important**: 
- Replace `your_account_name` and `your_account_key` with your actual values from Azure Portal
- Keep the connection string secure and never commit it to version control

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install `azure-storage-blob>=12.19.0`.

### 6. Verify Configuration

The application will automatically:
- Detect if Azure is configured on startup
- Create the container if it doesn't exist
- Fall back to local storage if Azure is not configured

## How It Works

### Storage Service

The `backend/storage_service.py` module provides a unified interface:

- **Upload**: Files are uploaded to Azure Blob Storage with unique UUID-based filenames
- **Download**: When processing resumes, files are temporarily downloaded from Azure
- **Path Storage**: Database stores Azure blob URLs (for Azure) or local paths (for local storage)

### Automatic Fallback

If Azure is not configured:
- Files are stored in the local `uploads/` directory
- All functionality works the same way
- No code changes needed

### File Processing

When a resume needs to be processed:
1. If stored in Azure: File is downloaded to a temporary location
2. NLP and ML processing happens on the local temp file
3. Temp file is cleaned up after processing
4. Database stores the Azure URL for future reference

## Benefits of Azure Blob Storage

1. **Scalability**: Handle unlimited file storage
2. **Reliability**: Azure's 99.9% uptime SLA
3. **Security**: Private containers with access control
4. **Cost-effective**: Pay only for what you use
5. **Backup**: Built-in redundancy options
6. **CDN Integration**: Can integrate with Azure CDN for faster access

## Cost Considerations

Azure Blob Storage pricing (approximate):
- **Storage**: ~$0.0184 per GB/month (Hot tier)
- **Transactions**: ~$0.004 per 10,000 transactions
- **Data Transfer**: First 5GB free per month, then ~$0.087 per GB

For a typical application with 1000 resumes (~50MB total):
- Storage cost: ~$0.001/month
- Transaction cost: ~$0.0004/month
- **Total: ~$0.001/month** (very affordable!)

## Security Best Practices

1. **Never commit connection strings** to version control
2. Use **Private containers** (not public)
3. Consider using **Azure Key Vault** for production
4. Enable **Storage Account firewall** to restrict access
5. Use **SAS tokens** for temporary access if needed
6. Regularly rotate access keys

## Troubleshooting

### Issue: "Azure Blob Storage initialization failed"

**Solution**: 
- Check your connection string is correct
- Verify the storage account exists and is accessible
- Check network connectivity

### Issue: "Container not found"

**Solution**:
- The service will try to create the container automatically
- Verify you have permissions to create containers
- Manually create the container in Azure Portal if needed

### Issue: Files not uploading

**Solution**:
- Check Azure Storage account quota
- Verify connection string is correct
- Check application logs for detailed error messages

## Migration from Local to Azure

If you have existing resumes in local storage:

1. Configure Azure as described above
2. The system will automatically use Azure for new uploads
3. Old files remain in local storage and will still work
4. Optionally, create a migration script to upload existing files to Azure

## Support

For Azure-specific issues, refer to:
- [Azure Blob Storage Documentation](https://docs.microsoft.com/azure/storage/blobs/)
- [Python SDK Documentation](https://docs.microsoft.com/python/api/azure-storage-blob/)

