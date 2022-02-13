from app.core.app import App
from app import log


try:
    app = App()
    from app.storage import Storage
    Storage.register(app)

    from app.commands.wiki import bp as wiki_bp
    from app.commands.avatar import bp as avatar_bp

    avatar_bp.register(app)
    wiki_bp.register(app)

    app.start()
except KeyboardInterrupt:
    import sys

    sys.exit(0)
except Exception as e:
    log.exception(e, exc_info=True)
