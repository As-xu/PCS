import sys
from pcs.celery_app import app

if __name__ == '__main__':
    argv = sys.argv
    app.start(argv=argv[1:])