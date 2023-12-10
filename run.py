from pcs import create_app
from gevent.pywsgi import WSGIServer
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

app = create_app()
app.wsgi_app = ProxyFix(app.wsgi_app)
if __name__ == '__main__':
    if app.env == 'development':
        app.run(host='127.0.0.1', port=5000)
    else:
        server = WSGIServer(app.config['SERVER_NAME'],
                            log=logging.getLogger('pcs'),
                            error_log=logging.getLogger('pcs'),
                            application=app)
        server.serve_forever()