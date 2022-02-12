from app.core.app import App
from app import log


try:
    app = App()
    from app.storage import Storage

    Storage.register(app)
    log.info("Init done")
    app.start()
except KeyboardInterrupt:
    import sys

    sys.exit(0)
except Exception as e:
    log.exception(e, exc_info=True)
