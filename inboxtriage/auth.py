from __future__ import annotations

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from inboxtriage.config import get_settings

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_credentials_path() -> str:
    settings = get_settings()
    path = settings["gmail_credentials_path"]
    return str(Path(path).resolve())


def get_token_path() -> str:
    settings = get_settings()
    path = settings["gmail_token_path"]
    return str(Path(path).resolve())


def build_gmail_service() -> object:
    creds = None
    token_path = get_token_path()

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(get_credentials_path(), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)
