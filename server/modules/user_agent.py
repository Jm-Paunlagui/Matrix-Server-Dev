from ua_parser import user_agent_parser
from werkzeug.user_agent import UserAgent
from werkzeug.utils import cached_property


# desc: Get the User's browser and OS
class ParsedUserAgent(UserAgent):

    # desc: Parser for the User's browser and OS
    @cached_property
    def _details(self):
        return user_agent_parser.Parse(self.string)

    # desc: Get the User's OS
    @property
    def platform(self):
        return self._details['os']['family']

    # desc: Get the User's browser
    @property
    def browser(self):
        return self._details['user_agent']['family']

    # desc: Get the User's browser version
    @property
    def version(self):
        return '.'.join(
            part
            for key in ('major', 'minor', 'patch')
            if (part := self._details['user_agent'][key]) is not None
        )

    # desc: Get the User's OS version
    @property
    def os_version(self):
        return '.'.join(
            part
            for key in ('major', 'minor', 'patch')
            if (part := self._details['os'][key]) is not None
        )
