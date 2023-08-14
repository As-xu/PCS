import sys
from pcs.extensions.celery_extension.app import app

if __name__ == '__main__':
    argv = sys.argv
    app.start(argv=argv[1:])