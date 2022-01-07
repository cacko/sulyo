from argparse import ArgumentTypeError
import validators
from .base import Base


class Traceroute(Base):

    command = "traceroute"

    def validate(self):
        if not any([validators.domain(x) for x in self.args]):
            raise ArgumentTypeError
        self.args = ["-q", "1", *self.args]
