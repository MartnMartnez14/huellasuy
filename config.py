import os


class Config:
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'instance/huellasuy.db')
    SECRET_KEY = os.getenv('SECRET_KEY')
    PUBLIC_ORIGIN = os.getenv('PUBLIC_ORIGIN')
    REPORT_TTL_HOURS = 24
    MAX_TITLE_LENGTH = 80
    MAX_DESCRIPTION_LENGTH = 500
    MAX_CONTENT_LENGTH = 8192
