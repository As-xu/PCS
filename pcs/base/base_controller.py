
class BaseController:
    def __init__(self, app, request):
        self.app = app
        self.request = request
        