import sys
from tts.celery_app import app

if __name__ == '__main__':
    argv = sys.argv
    app.start(argv=argv[1:])