class HappyBDMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        id = hash(repr(kwargs.get("haystack")))
        if id not in cls._instances:
            cls._instances[id] = super(HappyBDMeta, cls).__call__(*args, **kwargs)
        return cls._instances[id]

    def message(cls, source):
        _self = cls(source)
        return _self.getMessage()


class HappyBD(object, metaclass=HappyBDMeta):

    MESSAGES = [
        "еее айдее ЧРД!",
        "жив и здрав...",
        "бе ти на колко стана, 50 май а ?",
        "чъ ръъ дъъъ, никулай",
        "назраве и за мноо години!",
        "ЧРД баце, жив и здрав",
    ]
    idx = 0
    source = None

    def __init__(self, source):
        self.source = source
        self.idx = 0

    def getMessage(self):
        if len(self.MESSAGES) > self.idx:
            res = self.MESSAGES[self.idx]
            self.idx += 1
            return res
        return None
