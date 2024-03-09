from tts import create_app
from gevent.pywsgi import WSGIServer
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

app = create_app()
app.wsgi_app = ProxyFix(app.wsgi_app)
if __name__ == '__main__':
    if app.env == 'development':
        app.run()
    else:
        server = WSGIServer(app.config['SERVER_NAME'],
                            log=logging.getLogger('tts'),
                            error_log=logging.getLogger('tts'),
                            application=app)
        server.serve_forever()