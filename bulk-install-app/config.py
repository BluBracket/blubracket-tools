import os
from os.path import join
from dotenv import load_dotenv

cwd = os.getcwd().rstrip('/')
dotenv_path = join(cwd, '.env')
load_dotenv(dotenv_path)

DOMAIN = os.environ.get('BLU_DOMAIN') or 'github.com'
GITHUB_APP_NAME = os.environ.get('BLU_GITHUB_APP_NAME')  # or 'blubracket-checks-app'
USERNAME = os.environ.get('BLU_USERNAME')
PASSWORD = os.environ.get('BLU_PASSWORD')
DEBUG = bool(int(os.environ.get('BLU_DEBUG'))) if os.environ.get('BLU_DEBUG') else False
