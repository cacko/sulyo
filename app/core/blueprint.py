from app.core.app import App


class Blueprint:

    _name: str = None
    _app: App = None

    def __init__(self, name):
        self._name = name

    def register(self, app: App):
        self._app = app
