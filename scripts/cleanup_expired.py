"""Run from repo root: python scripts/cleanup_expired.py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from database import connect, cleanup

if __name__ == '__main__':
    app = create_app()
    with connect(app.config['DATABASE_PATH']) as db:
        cleanup(db, app.config['CLOCK']())
    print('Limpieza completada.')
