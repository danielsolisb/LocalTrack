import os
import pymysql

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = '10cb57a98d6179f8f9c05379ea432eadb35232526a4de0f4'
    SQLALCHEMY_DATABASE_URI = 'mysql://root:daniel586@35.222.201.195/Localtrack'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #SQLALCHEMY_TRACK_MODIFICATIONS = False
    #SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "data.db")}'

config = Config
