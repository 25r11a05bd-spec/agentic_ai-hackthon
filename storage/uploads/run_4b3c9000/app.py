from fastapi import FastAPI, UploadFile
import sqlite3
import subprocess
import asyncio
import yaml
import requests
import os

app = FastAPI()

DATABASE_URL = DB_URL

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

@app.get("/")
def root():
    return {"status": "running"}

# SQL injection
@app.get("/user")
def get_user(user_id: str):
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    cursor.execute(query)
    return {"data": cursor.fetchall()}

# SSRF vulnerability
@app.get("/fetch")
def fetch(url: str):
    response = requests.get(url)
    return {"content": response.text}

# Unsafe YAML loading
@app.post("/yaml")
def parse_yaml(payload: str):
    data = yaml.load(payload)
    return {"data": data}

# Async misuse
@app.get("/async-block")
async def async_block():
    import time
    time.sleep(15)
    return {"done": True}

# Shell injection
@app.get("/ping")
def ping(host: str):
    cmd = f"ping {host}"
    result = subprocess.check_output(cmd, shell=True)
    return {"result": result.decode()}

# Undefined variable
@app.get("/config")
def config():
    return {"token": API_SECRET}

# Undefined function
@app.get("/agent")
def run_agent():
    return autonomous_executor()

# File overwrite vulnerability
@app.post("/upload")
def upload(file: UploadFile):
    path = f"./uploads/{file.filename}"
    with open(path, "wb") as f:
        f.write(file.file.read())
    return {"saved": path}

# Infinite async recursion
@app.get("/recursive")
async def recursive():
    return await recursive()

# Resource exhaustion
@app.get("/disk")
def disk_fill():
    while True:
        with open("huge.log", "a") as f:
            f.write("A" * 1000000)

# Invalid await
@app.get("/bad-await")
async def bad_await():
    await get_user("1")

# Memory leak
CACHE = []

@app.get("/cache")
def cache():
    while True:
        CACHE.append(os.urandom(1000000))

# Broken exception handling
@app.get("/error")
def error():
    try:
        1 / 0
    except:
        pass
    return {"hidden": True}

# Dangerous delete
@app.delete("/delete")
def delete(path: str):
    os.remove(path)
    return {"deleted": path}

# Open redirect
@app.get("/redirect")
def redirect(url: str):
    return {"redirect_to": url}

# Hardcoded secrets
JWT_SECRET = "SUPER_SECRET_JWT_KEY"
AWS_KEY = "AKIA_TEST_SECRET"

# Broken async session
@app.get("/session")
async def session():
    asyncio.create_task(recursive())
    return {"started": True}