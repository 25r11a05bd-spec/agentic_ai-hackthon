import os
DATABASE_URL = os.getenv('DB_URL', 'sqlite:///:memory:')
app = FastAPI()
