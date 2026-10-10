import os
from pathlib import Path


class Config:
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'instance/huellasuy.db')
    SECRET_KEY = os.getenv('SECRET_KEY')
    PUBLIC_ORIGIN = os.getenv('PUBLIC_ORIGIN')
    REPORT_TTL_HOURS = 24
    MAX_TITLE_LENGTH = 80
    MAX_DESCRIPTION_LENGTH = 500
    MAX_CONTENT_LENGTH = 8192

    # Staged rollout: enable only after email and migration checks.
    AUTH_ENABLED = os.getenv('AUTH_ENABLED', '0') == '1'
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', '').lower()
    BREVO_CONFIG_PATH = os.getenv('BREVO_CONFIG_PATH', str(Path.home() / '.config/huellasuy/brevo.json'))
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', '1') == '1'
