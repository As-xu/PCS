from pcs import create_app
from gevent.pywsgi import WSGIServer
from gevent.pywsgi import LoggingLogAdapter
import logging

if __name__ == '__main__':
    app = create_app()
    if app.env == 'development':
        app.run()
    else:
        server = WSGIServer(app.config['SERVER_NAME'],
                            log=logging.getLogger('pcs'),
                            error_log=logging.getLogger('pcs'),
                            application=app)
        server.serve_forever()