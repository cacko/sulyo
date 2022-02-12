from .base import Base
import validators
from argparse import ArgumentTypeError


class WhoIs(Base):

    command = "console/whois"

    def validate(self):
        if not any([validators.domain(x) for x in self.args]):
            raise ArgumentTypeError
