from fastapi import FastAPI, UploadFile
import sqlite3
import subprocess
import asyncio
import yaml
import requests
import os

app = FastAPI()

DATABASE_URL = os.getenv("DB_URL", "sqlite:///:memory:")

class DatabaseConnection:
    def __init__(self, database_url):
        self.database_url = database_url
        self.conn = None
        self.cursor = None
    
    def connect(self):
        try:
            self.conn = sqlite3.connect(self.database_url)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Error connecting to the database: {e}")
    
    def close(self):
        if self.conn:
            self.conn.close()

# Create a database connection object
db_connection = DatabaseConnection(DATABASE_URL)

db_connection.connect()
