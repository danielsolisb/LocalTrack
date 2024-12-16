import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = '10cb57a98d6179f8f9c05379ea432eadb35232526a4de0f4'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "data.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

config = Config
