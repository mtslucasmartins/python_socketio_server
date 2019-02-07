import os
from os.path import join, dirname
from dotenv import load_dotenv

load_dotenv(join(dirname(__file__), '.env'))

print(os.environ.get("PORT"))

SECRET_KEY = os.environ.get("SECRET_KEY")
DATABASE_URI = os.environ.get("DATABASE_URI")
PORT = int(os.environ.get("PORT", 5000))
