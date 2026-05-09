import os
SECRET_TOKEN = os.getenv('SECRET_TOKEN', '')
API_KEY = os.getenv('API_KEY', '')
import os\nimport subprocess\nping(host: str):\n    try:\n        result = subprocess.run(['ping', host], capture_output=True, text=True)\n        return {'result': result.output}\n    except subprocess.CalledProcessError as e:\n        return {'error': f'ping process returned non-zero exit code {e.returncode}'}\n