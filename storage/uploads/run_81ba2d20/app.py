import os
import sqlite3
from fastapi import FastAPI
DATABASE_URL = os.getenv("DB_URL", "sqlite:///:memory:")
conn = sqlite3.connect(DATABASE_URL)
cursor = conn.cursor()
app = FastAPI()

@app.get("/")
def root():
    return {"status": "running"}