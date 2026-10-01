import os
from typing import Optional, List
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
from app.config import settings

SCOPES = ['https://www.googleapis.com/auth/drive']

class GoogleDriveManager:
    def __init__(self):
        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                settings.google_service_account_file,
                scopes=SCOPES
            )
            self.service = build('drive', 'v3', credentials=self.credentials)
        except Exception as e:
            print(f"Error al inicializar Google Drive: {e}")
            self.service = None
    
    def crear_carpeta(self, nombre: str, parent_id: Optional[str] = None) -> Optional[str]:
        if not self.service:
            raise Exception("Google Drive no está inicializado")
        file_metadata = {'name': nombre, 'mimeType': 'application/vnd.google-apps.folder'}
        if parent_id:
            file_metadata['parents'] = [parent_id]
        try:
            file = self.service.files().create(body=file_metadata, fields='id').execute()
            return file.get('id')
        except HttpError as error:
            print(f'Error al crear carpeta: {error}')
            return None
    
    def subir_archivo(self, archivo_ruta: str, nombre_archivo: str, parent_id: Optional[str] = None) -> Optional[str]:
        if not self.service:
            raise Exception("Google Drive no está inicializado")
        file_metadata = {'name': nombre_archivo}
        if parent_id:
            file_metadata['parents'] = [parent_id]
        media = MediaFileUpload(archivo_ruta, resumable=True)
        try:
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            return file.get('id')
        except HttpError as error:
            print(f'Error al subir archivo: {error}')
            return None
    
    def descargar_archivo(self, file_id: str, archivo_ruta_salida: str) -> bool:
        if not self.service:
            raise Exception("Google Drive no está inicializado")
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = open(archivo_ruta_salida, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            fh.close()
            return True
        except HttpError as error:
            print(f'Error al descargar archivo: {error}')
            return False
    
    def eliminar_archivo(self, file_id: str) -> bool:
        if not self.service:
            raise Exception("Google Drive no está inicializado")
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except HttpError as error:
            print(f'Error al eliminar archivo: {error}')
            return False
    
    def obtener_informacion_archivo(self, file_id: str) -> Optional[dict]:
        if not self.service:
            raise Exception("Google Drive no está inicializado")
        try:
            file = self.service.files().get(fileId=file_id, fields='id, name, size, mimeType, createdTime').execute()
            return file
        except HttpError as error:
            print(f'Error al obtener información: {error}')
            return None
    
    def listar_archivos_en_carpeta(self, folder_id: str) -> list:
        if not self.service:
            raise Exception("Google Drive no está inicializado")
        try:
            results = self.service.files().list(q=f"'{folder_id}' in parents and trashed=false", spaces='drive', fields='files(id, name, mimeType, size)', pageSize=100).execute()
            return results.get('files', [])
        except HttpError as error:
            print(f'Error al listar archivos: {error}')
            return []
    
    def vaciar_papelera(self) -> bool:
        if not self.service:
            raise Exception("Google Drive no está inicializado")
        try:
            results = self.service.files().list(q='trashed=true', spaces='drive', fields='files(id)', pageSize=1000).execute()
            files = results.get('files', [])
            for file in files:
                self.service.files().delete(fileId=file['id']).execute()
            return True
        except HttpError as error:
            print(f'Error al vaciar papelera: {error}')
            return False

drive_manager = GoogleDriveManager()
