from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from google.oauth2 import service_account
from pydantic_settings import BaseSettings
from src.config import settings
from src.utils import log
from datetime import date
from pydantic import Field
import os

SCOPES = ['https://www.googleapis.com/auth/drive']

class DriveSettings(BaseSettings):
	FOLDER_ID: str | None = Field(default=None)
	SERVICE_ACCOUNT_FILE: str | None = Field(default=None)

class DriveUploader:

	def __init__(self):

		drive_settings = DriveSettings()
		credentials_file = drive_settings.SERVICE_ACCOUNT_FILE
		folder_id = drive_settings.FOLDER_ID

		if not credentials_file or not folder_id:
			log.warning('Drive upload disabled: DRIVE_SERVICE_ACCOUNT_FILE or DRIVE_FOLDER_ID not set.')
			self.__enabled = False
			return

		credentials = service_account.Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
		self.__service = build('drive', 'v3', credentials=credentials)
		run_folder_id = self.__create_run_folder(folder_id)
		self.__samples_folder_id = self.__get_or_create_folder('samples', run_folder_id)
		self.__enabled = True

	def upload_sample(self, i: int, sample_dir: str):

		if not self.__enabled:
			return

		folder_id = self.__get_or_create_folder(f'sample_{i}', self.__samples_folder_id)

		for filename in os.listdir(sample_dir):
			path = f'{sample_dir}/{filename}'
			if os.path.isfile(path):
				self.__upload_file(path, filename, folder_id)

		log.info(f'Sample {i} uploaded to Drive.')

	def upload_sampling_json(self):
		self.__upload_to_samples('sampling.json')

	def upload_results_json(self):
		self.__upload_to_samples('results.json')

	def __upload_to_samples(self, filename: str):

		if not self.__enabled:
			return

		path = f'{settings.runtime.OUTPUT_DIR}/{filename}'

		if not os.path.exists(path):
			log.warning(f'{filename} not found, skipping Drive upload.')
			return

		self.__upload_file(path, filename, self.__samples_folder_id, replace=True)
		log.info(f'{filename} uploaded to Drive.')

	def __folder_query(self, name: str, parent_id: str) -> str:
		return f'name="{name}" and "{parent_id}" in parents and mimeType="application/vnd.google-apps.folder" and trashed=false'

	def __create_folder(self, name: str, parent_id: str) -> str:
		metadata = {
			'name': name,
			'mimeType': 'application/vnd.google-apps.folder',
			'parents': [parent_id],
		}
		folder = self.__service.files().create(body=metadata, fields='id').execute()
		return folder['id']

	def __create_run_folder(self, parent_id: str) -> str:

		today = date.today().isoformat()
		n = 0

		while True:
			name = f'{today}_{n}'
			results = self.__service.files().list(q=self.__folder_query(name, parent_id), fields='files(id)').execute()
			if not results.get('files'):
				break
			n += 1

		folder_id = self.__create_folder(name, parent_id)
		log.info(f'Drive run folder created: {name}')
		return folder_id

	def __get_or_create_folder(self, name: str, parent_id: str) -> str:

		results = self.__service.files().list(q=self.__folder_query(name, parent_id), fields='files(id)').execute()
		files = results.get('files', [])

		if files:
			return files[0]['id']

		return self.__create_folder(name, parent_id)

	def __upload_file(self, path: str, name: str, parent_id: str, replace: bool = False):

		if replace:
			query = f'name="{name}" and "{parent_id}" in parents and trashed=false'
			results = self.__service.files().list(q=query, fields='files(id)').execute()
			for f in results.get('files', []):
				self.__service.files().delete(fileId=f['id']).execute()

		metadata = {'name': name, 'parents': [parent_id]}
		media = MediaFileUpload(path, resumable=True)
		self.__service.files().create(body=metadata, media_body=media, fields='id').execute()
