from lxml import etree
from lxml.etree import XMLSyntaxError


class NSWebDavHTTPError(Exception):
    """
    Contains HTTP error's information.

    Attributes
    ----------
    code : int
        status code of HTTP error.
    message : str
        contains message which is extracted from server's xml response.
    detail : str
        contains detail message which is extracted from server's xml response.
    """
    def __init__(self, code, content):
        message, detail = self._parse_response(content)
        self.code = code
        self.message = message
        self.detail = detail

    def __str__(self):
        if self.detail:
            return "%s %s\ndetail: %s" % (self.code, self.message, self.detail)
        else:
            return "%s %s" % (self.code, self.message)

    def _parse_response(self, response):
        try:
            t = etree.fromstring(response)
        except XMLSyntaxError:
            return None, None
        message = t.find("s:exception", t.nsmap)
        if message is not None:
            message = message.text
        detail = t.find("s:message", t.nsmap)
        if detail is not None:
            detail = detail.text
        return message, detail

    __repr__ = __str__
