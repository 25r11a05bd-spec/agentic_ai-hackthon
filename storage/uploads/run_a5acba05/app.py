from fastapi import FastAPI, UploadFile
import sqlite3
import subprocess
import asyncio
import yaml
import requests
import os
app = FastAPI()
DATABASE_URL = os.getenv("DB_URL", "sqlite:///:memory:")
conn = sqlite3.connect(DATABASE_URL)
cursor = conn.cursor()
API_SECRET = os.getenv("API_SECRET", "my_default_secret")
# rest of the code...