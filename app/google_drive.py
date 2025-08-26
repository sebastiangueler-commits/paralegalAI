import os
import json
import io
from typing import List, Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import PyPDF2
import logging
from app.config import settings
from pathlib import Path

class GoogleDriveService:
    def __init__(self):
        self.service = None
        self.credentials = None
        self.logger = logging.getLogger(__name__)
        
        # Google Drive API scopes
        self.SCOPES = [
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/drive.metadata.readonly'
        ]
        
        # Initialize the service
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive API."""
        try:
            creds = None
            
            # Check if token file exists
            if os.path.exists(settings.GOOGLE_DRIVE_TOKEN_PATH):
                creds = Credentials.from_authorized_user_file(
                    settings.GOOGLE_DRIVE_TOKEN_PATH, self.SCOPES
                )
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(settings.GOOGLE_DRIVE_CREDENTIALS_PATH):
                        raise FileNotFoundError(
                            f"Google Drive credentials file not found at {settings.GOOGLE_DRIVE_CREDENTIALS_PATH}"
                        )
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        settings.GOOGLE_DRIVE_CREDENTIALS_PATH, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                os.makedirs(os.path.dirname(settings.GOOGLE_DRIVE_TOKEN_PATH), exist_ok=True)
                with open(settings.GOOGLE_DRIVE_TOKEN_PATH, 'w') as token:
                    token.write(creds.to_json())
            
            self.credentials = creds
            self.service = build('drive', 'v3', credentials=creds)
            self.logger.info("Google Drive authentication successful")
            
        except Exception as e:
            self.logger.error(f"Google Drive authentication failed: {e}")
            raise
    
    def download_sentencias_json(self, output_path: str = None) -> List[Dict[str, Any]]:
        """Download and parse the sentencias JSON file."""
        try:
            if output_path is None:
                output_path = os.path.join(settings.DATA_DIR, "sentencias.json")
            
            self.logger.info(f"Downloading sentencias from file ID: {settings.SENTENCIAS_FILE_ID}")
            
            # Get file metadata
            file_metadata = self.service.files().get(
                fileId=settings.SENTENCIAS_FILE_ID
            ).execute()
            
            self.logger.info(f"File: {file_metadata['name']}, Size: {file_metadata['size']} bytes")
            
            # Download file
            request = self.service.files().get_media(fileId=settings.SENTENCIAS_FILE_ID)
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    self.logger.info(f"Downloaded {int(status.progress() * 100)}%")
            
            # Parse JSON
            file.seek(0)
            content = file.read().decode('utf-8')
            sentencias = json.loads(content)
            
            # Save to file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(sentencias, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Downloaded {len(sentencias)} sentencias to {output_path}")
            return sentencias
            
        except Exception as e:
            self.logger.error(f"Error downloading sentencias: {e}")
            raise
    
    def download_escritos_pdfs(self, output_dir: str = None) -> List[Dict[str, Any]]:
        """Download all PDF files from the escritos folder."""
        try:
            if output_dir is None:
                output_dir = os.path.join(settings.DATA_DIR, "escritos")
            
            os.makedirs(output_dir, exist_ok=True)
            
            self.logger.info(f"Downloading PDFs from folder ID: {settings.ESCRITOS_FOLDER_ID}")
            
            # List files in folder
            results = self.service.files().list(
                q=f"'{settings.ESCRITOS_FOLDER_ID}' in parents and mimeType contains 'application/pdf'",
                fields="files(id,name,mimeType,size)"
            ).execute()
            
            files = results.get('files', [])
            self.logger.info(f"Found {len(files)} PDF files")
            
            escritos_info = []
            
            for file in files:
                try:
                    file_id = file['id']
                    file_name = file['name']
                    file_size = int(file['size'])
                    
                    self.logger.info(f"Downloading: {file_name} ({file_size} bytes)")
                    
                    # Download file
                    request = self.service.files().get_media(fileId=file_id)
                    file_content = io.BytesIO()
                    downloader = MediaIoBaseDownload(file_content, request)
                    
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk()
                        if status:
                            self.logger.info(f"Downloaded {int(status.progress() * 100)}% of {file_name}")
                    
                    # Save file
                    output_path = os.path.join(output_dir, file_name)
                    file_content.seek(0)
                    with open(output_path, 'wb') as f:
                        f.write(file_content.read())
                    
                    # Extract text from PDF
                    pdf_text = self._extract_pdf_text(output_path)
                    
                    # Determine tipo from filename
                    tipo = self._determine_escrito_tipo(file_name)
                    
                    escritos_info.append({
                        'id': file_id,
                        'nombre': file_name,
                        'tipo': tipo,
                        'pdf_path': output_path,
                        'contenido_template': pdf_text,
                        'size': file_size
                    })
                    
                    self.logger.info(f"Successfully processed: {file_name}")
                    
                except Exception as e:
                    self.logger.error(f"Error processing file {file.get('name', 'unknown')}: {e}")
                    continue
            
            # Save metadata
            metadata_path = os.path.join(output_dir, "escritos_metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(escritos_info, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Downloaded and processed {len(escritos_info)} PDF files")
            return escritos_info
            
        except Exception as e:
            self.logger.error(f"Error downloading escritos PDFs: {e}")
            raise
    
    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text content from PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                return text.strip()
                
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            return ""
    
    def _determine_escrito_tipo(self, filename: str) -> str:
        """Determine the type of legal document from filename."""
        filename_lower = filename.lower()
        
        # Map common filename patterns to document types
        tipo_mapping = {
            'demanda': 'demanda',
            'contestacion': 'contestacion_demanda',
            'reconvencion': 'reconvencion',
            'replica': 'replica',
            'duplica': 'duplica',
            'alegato': 'alegato',
            'recurso': 'recurso',
            'apelacion': 'apelacion',
            'casacion': 'casacion',
            'amparo': 'amparo',
            'habeas': 'habeas_corpus',
            'medida': 'medida_cautelar',
            'inhibitoria': 'inhibitoria',
            'desistimiento': 'desistimiento',
            'allanamiento': 'allanamiento',
            'transaccion': 'transaccion',
            'acuerdo': 'acuerdo',
            'convenio': 'convenio'
        }
        
        for key, value in tipo_mapping.items():
            if key in filename_lower:
                return value
        
        # Default type
        return 'escrito_general'
    
    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Get information about a specific file."""
        try:
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields="id,name,mimeType,size,createdTime,modifiedTime,parents"
            ).execute()
            
            return file_metadata
            
        except Exception as e:
            self.logger.error(f"Error getting file info for {file_id}: {e}")
            raise
    
    def list_folder_contents(self, folder_id: str) -> List[Dict[str, Any]]:
        """List all contents of a folder."""
        try:
            results = self.service.files().list(
                q=f"'{folder_id}' in parents",
                fields="files(id,name,mimeType,size,createdTime,modifiedTime)"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            self.logger.error(f"Error listing folder contents for {folder_id}: {e}")
            raise
    
    def search_files(self, query: str, folder_id: str = None) -> List[Dict[str, Any]]:
        """Search for files with a specific query."""
        try:
            search_query = f"name contains '{query}'"
            if folder_id:
                search_query += f" and '{folder_id}' in parents"
            
            results = self.service.files().list(
                q=search_query,
                fields="files(id,name,mimeType,size,createdTime,modifiedTime)"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            self.logger.error(f"Error searching files with query '{query}': {e}")
            raise

# Global instance
google_drive_service = GoogleDriveService()