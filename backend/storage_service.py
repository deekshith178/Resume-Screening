"""Azure Blob Storage service for resume file storage.

This module provides a unified interface for file storage that supports:
- Azure Blob Storage (when configured)
- Local file storage (fallback)
"""

import os
from pathlib import Path
from typing import Optional, BinaryIO
from io import BytesIO

# Azure Blob Storage imports (optional)
try:
    from azure.storage.blob import BlobServiceClient, BlobClient, generate_blob_sas, BlobSasPermissions
    from azure.core.exceptions import AzureError
    from datetime import datetime, timedelta
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    BlobServiceClient = None


class StorageService:
    """Unified storage service supporting Azure Blob Storage and local filesystem."""
    
    def __init__(self):
        """Initialize storage service with Azure or local fallback."""
        self.use_azure = False
        self.blob_service_client = None
        self.container_name = None
        self.local_uploads_dir = Path("uploads")
        
        # Check if Azure is configured
        azure_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "resumes")
        
        if AZURE_AVAILABLE and azure_connection_string:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    azure_connection_string
                )
                self.use_azure = True
                # Ensure container exists
                try:
                    container_client = self.blob_service_client.get_container_client(self.container_name)
                    if not container_client.exists():
                        container_client.create_container()
                except Exception as e:
                    print(f"Warning: Could not create/verify Azure container: {e}")
                    self.use_azure = False
            except Exception as e:
                print(f"Warning: Azure Blob Storage initialization failed: {e}")
                print("Falling back to local file storage")
                self.use_azure = False
        
        # Ensure local uploads directory exists
        if not self.use_azure:
            self.local_uploads_dir.mkdir(exist_ok=True)
    
    def upload_file(
        self, 
        file_content: bytes, 
        filename: str,
        content_type: Optional[str] = None
    ) -> str:
        """Upload a file and return its storage path/URL.
        
        Args:
            file_content: File content as bytes
            filename: Original filename (will be used to determine extension)
            content_type: MIME type of the file (optional)
            
        Returns:
            Storage path/URL that can be used to retrieve the file
        """
        import uuid
        from pathlib import Path
        
        # Generate unique filename
        file_ext = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        if self.use_azure:
            try:
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=unique_filename
                )
                
                # Upload to Azure
                blob_client.upload_blob(
                    file_content,
                    overwrite=True,
                    content_settings=None if not content_type else {
                        "content_type": content_type
                    }
                )
                
                # Return blob URL
                return blob_client.url
            except Exception as e:
                print(f"Error uploading to Azure: {e}")
                # Fallback to local storage
                return self._upload_local(file_content, unique_filename)
        else:
            return self._upload_local(file_content, unique_filename)
    
    def _upload_local(self, file_content: bytes, filename: str) -> str:
        """Upload file to local filesystem."""
        file_path = self.local_uploads_dir / filename
        with open(file_path, "wb") as f:
            f.write(file_content)
        return str(file_path)
    
    def download_file(self, file_path: str) -> bytes:
        """Download a file from storage.
        
        Args:
            file_path: Storage path/URL returned by upload_file
            
        Returns:
            File content as bytes
        """
        if self.use_azure and file_path.startswith("http"):
            # Azure blob URL
            try:
                # Extract blob name from URL
                blob_name = file_path.split(f"/{self.container_name}/")[-1].split("?")[0]
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=blob_name
                )
                return blob_client.download_blob().readall()
            except Exception as e:
                raise FileNotFoundError(f"Could not download from Azure: {e}")
        else:
            # Local file path
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            with open(file_path_obj, "rb") as f:
                return f.read()
    
    def get_file_path(self, file_path: str) -> str:
        """Get a file path that can be used for processing.
        
        For Azure, this downloads the file temporarily.
        For local, this returns the path directly.
        
        Args:
            file_path: Storage path/URL
            
        Returns:
            Local file path (temporary for Azure, permanent for local)
        """
        if not file_path:
            raise FileNotFoundError("Resume path is empty")
            
        if self.use_azure and file_path.startswith("http"):
            # Download from Azure to temp file
            try:
                import tempfile
                file_content = self.download_file(file_path)
                # Extract extension from original filename or URL
                ext = Path(file_path).suffix or ".pdf"
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                temp_file.write(file_content)
                temp_file.close()
                return temp_file.name
            except Exception as e:
                raise FileNotFoundError(f"Could not download file from Azure: {str(e)}")
        else:
            # Local file - verify it exists and return path directly
            file_path_obj = Path(file_path)
            # Handle relative paths
            if not file_path_obj.is_absolute():
                # Try relative to current working directory
                file_path_obj = Path.cwd() / file_path
            if not file_path_obj.exists():
                raise FileNotFoundError(f"Resume file not found at: {file_path}. Please upload a resume first.")
            return str(file_path_obj)
    
    def generate_sas_url(
        self, 
        file_path: str, 
        expiry_hours: int = 1
    ) -> Optional[str]:
        """Generate a SAS (Shared Access Signature) URL for temporary access.
        
        Args:
            file_path: Storage path/URL
            expiry_hours: Hours until URL expires
            
        Returns:
            SAS URL or None if not using Azure
        """
        if not self.use_azure or not file_path.startswith("http"):
            return None
        
        try:
            # Extract blob name from URL
            blob_name = file_path.split(f"/{self.container_name}/")[-1].split("?")[0]
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=self.blob_service_client.account_name,
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=self.blob_service_client.credential.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
            )
            
            return f"{blob_client.url}?{sas_token}"
        except Exception as e:
            print(f"Error generating SAS URL: {e}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file from storage.
        
        Args:
            file_path: Storage path/URL
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if self.use_azure and file_path.startswith("http"):
            try:
                blob_name = file_path.split(f"/{self.container_name}/")[-1].split("?")[0]
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=blob_name
                )
                blob_client.delete_blob()
                return True
            except Exception as e:
                print(f"Error deleting from Azure: {e}")
                return False
        else:
            try:
                file_path_obj = Path(file_path)
                if file_path_obj.exists():
                    file_path_obj.unlink()
                    return True
                return False
            except Exception as e:
                print(f"Error deleting local file: {e}")
                return False


# Global storage service instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get or create the global storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service

