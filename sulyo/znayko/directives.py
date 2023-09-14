from .core.storage import Storage
from .models import CommandDef, ZSONMatcher, ZSONResponse
from fuzzelinho import Match, MatchMethod
from pydantic import BaseModel
from typing import Optional
from corestring import trns_bg_en


class NoDirective(Exception):
    pass


class PhraseMatch(Match):
    method = MatchMethod.WRATIO


class PhraseNeedle(BaseModel):
    text: str


class NameMatch(Match):
    method = MatchMethod.PARTIAL
    minRatio = 80


class NameNeedle(BaseModel):
    name: str


class Contact(BaseModel):
    name: str
    id: str


class DirectiveMeta(type):

    _directives: list = []
    _instances: dict[str, "Directive"] = {}
    KEY_CHATS = "Chats:BC"
    KEY_GROUPS = "Groups:BC"
    _groups: dict[str, str] = {}
    _chats: dict[str, str] = {}
    contacts: dict[str, str] = {}

    def __new__(metacls, cls, bases, classdict, **kwds):
        kls = super().__new__(metacls, cls, bases, classdict)
        metacls._directives.append(kls)
        return kls

    def __call__(cls, *args, **kwds):
        k = cls.__name__
        if cls not in cls._instances:
            cls._instances[k] = type.__call__(cls, *args, **kwds)
        return cls._instances[k]

    def load(
        cls,
        contacts: Optional[dict[str, str]] = None,
        groups: Optional[dict[str, str]] = None,
    ):
        cls._chats = {
            k.decode(): v.decode() for k, v in Storage.hgetall(cls.KEY_CHATS).items()
        }
        cls._groups = {
            k.decode(): v.decode() for k, v in Storage.hgetall(cls.KEY_GROUPS).items()
        }
        if contacts:
            cls.contacts = contacts
        if groups:
            cls.groups = groups

    def parse(
        cls,
        message: str,
        group: Optional[str] = None,
        source: Optional[str] = None,
    ) -> str:
        first = trns_bg_en(message).lower().split(" ")[0]
        d = next(
            filter(
                lambda x: x().trigger is not None and first == x().trigger,
                cls._directives,
            ),
            None,
        )
        if not d:
            raise NoDirective
        return d().execute(message, group, source)

    def isPermitted(cls, group: str) -> bool:
        return group in cls._groups

    def match(
        cls,
        commands: list[CommandDef],
        message: Optional[str] = None,
        group: Optional[str] = None,
        source: Optional[str] = None,
    ) -> tuple[Optional[CommandDef], Optional[str]]:
        chatMatch = source in cls._chats
        if not chatMatch:
            commands = list(
                filter(lambda x: ZSONMatcher(x.matcher) != ZSONMatcher.SOURCE, commands)
            )
        for cmd in commands:
            t = ZSONMatcher(cmd.matcher)
            if chatMatch and t == ZSONMatcher.SOURCE:
                return (cmd, cls._chats[source])
            if t == ZSONMatcher.PHRASE:
                try:
                    assert message
                    assert cmd.response
                    matcher = PhraseMatch([PhraseNeedle(text=message)])
                    matches = matcher.fuzzy(PhraseNeedle(text=cmd.response))
                    if matches:
                        return (cmd, "en")
                except AssertionError:
                    pass
        return (None, None)


class Directive(metaclass=DirectiveMeta):

    trigger = None

    def execute(self, msg, group, source):
        raise NotImplementedError


class Turn(Directive):
    def execute(self, msg, group, source):
        args = msg.strip().split(" ")
        if len(args) > 1:
            matcher = NameMatch(
                haystack=[Contact(name=n, id=p) for p, n in __class__.contacts.items()]
            )
            matches = matcher.fuzzy(NameNeedle(name=args[1]))
            lang = args[2] if len(args) > 2 else ""
            if len(matches):
                return self.handleContact(matches[0], lang)
            raise NoDirective
        else:
            return self.handleGroup(group)

    def handleGroup(self, group, lang: str = "en"):
        raise NotImplementedError

    def handleContact(self, contact: NameNeedle, lang: str = "en"):
        raise NotImplementedError


class TurnOn(Turn):

    trigger = "!on"

    def handleGroup(self, group: str, lang: str = "en"):
        Storage.pipeline().hset(__class__.KEY_GROUPS, group, lang).persist(
            __class__.KEY_GROUPS
        ).execute()
        __class__._groups[group] = lang
        return (CommandDef.textGenerate, "🛬 Botyo has entered")

    def handleContact(self, contact: Contact, lang: str = "en"):
        Storage.pipeline().hset(__class__.KEY_CHATS, contact.id, lang).persist(
            __class__.KEY_CHATS
        ).execute()
        __class__._chats[contact.id] = lang
        return (CommandDef.textGenerate, f"👉 {contact.name} is added")


class TurnOff(Turn):

    trigger = "!off"

    def handleGroup(self, group: str, *args, **kwargs):
        Storage.pipeline().hdel(__class__.KEY_GROUPS, group).persist(
            __class__.KEY_GROUPS
        ).execute()
        del __class__._groups[group]
        return (CommandDef.textGenerate, "🛫 Botyo has left")

    def handleContact(self, contact: Contact, *args, **kwargs):
        Storage.pipeline().hdel(__class__.KEY_CHATS, contact.id).persist(
            __class__.KEY_CHATS
        ).execute()
        try:
            del __class__._chats[contact.id]
        except KeyError:
            pass
            return CommandDef.textGenerate, f"👎 {contact.name} was removed"


class Listing(Directive):

    trigger = "!list"

    def execute(self, *args, **kwargs):
        rows = [
            *[
                f"🏢 {__class__.groups.get(id, id)} {lang.upper()}"
                for id, lang in __class__._groups.items()
            ],
            *[
                f"🙎🏽‍♂️ {__class__.contacts.get(id, id)} {lang.upper()}"
                for id, lang in __class__._chats.items()
            ],
        ]
        return ZSONResponse(message="\n".join(rows)), None
