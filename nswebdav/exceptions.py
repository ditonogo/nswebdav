from lxml import etree
from lxml.etree import XMLSyntaxError


class NSWebDavHTTPError(Exception):
    """
    Contains HTTP error's information.

    Attributes
    ----------
    code : int
        status code of HTTP error.
    exception : str
        contains exception which is extracted from server's xml response.
    message : str
        contains detail message which is extracted from server's xml response.
    """
    def __init__(self, code, content):
        exception, message = self._parse_response(content)
        self.code = code
        self.exception = exception
        self.message = message

    def __str__(self):
        return "%s %s\nmessage: %s" % (self.code, self.exception or "Empty exception", self.message or "Empty message")

    def _parse_response(self, response):
        try:
            t = etree.fromstring(response)
        except XMLSyntaxError:
            return None, None
        exception = t.find("s:exception", t.nsmap)
        if exception is not None:
            exception = exception.text
        message = t.find("s:message", t.nsmap)
        if message is not None:
            message = message.text
        return exception, message

    __repr__ = __str__
