from urllib.parse import urljoin

from lxml import etree
from datetime import datetime
from jinja2 import Template

PERM_MAP = {
    "1": "download and preview",
    "2": "upload",
    "3": "upload, download, preview, remove and move",
    "4": "upload, download, preview, remove, move and change acls of others",
    "5": "preview"
}


class NutstoreDavBase:
    """
    Base class for both sync subclass and async subclass

    :param base_url: The base url of nutstore website.
    :param dav_url: The dav url of nutstore website, which is used to access files.
    :param operation_url: The operation url of nutstore website, which is used to post operations.
    """
    def __init__(self, base_url, dav_url="/dav", operation_url="/nsdav"):
        self._base_url = base_url
        self._operation_url = operation_url
        self._dav_url = dav_url

    def _perform_dav_request(self, method, auth_tuple=None, client=None, **kwargs):
        auth_tuple = self._get_auth_tuple(auth_tuple)
        client = self._get_client(client)
        data = kwargs.get("data")
        headers = None
        url = None

        path = kwargs.get("path")
        if path:
            root_url = urljoin(self._base_url, self._dav_url)
            url = root_url + path

        from_path = kwargs.get("from_path")
        to_path = kwargs.get("to_path")
        if from_path and to_path:
            root_url = urljoin(self._base_url, self._dav_url)
            url = root_url + from_path
            destination = root_url + to_path

            headers = {
                "Destination": destination
            }

        return client.request(method, url, data=data, headers=headers, auth=auth_tuple)

    def _get_auth_tuple(self, auth_tuple=None):
        raise NotImplementedError("Should be implemented in subclass.")

    def _get_client(self, client=None):
        raise NotImplementedError("Should be implemented in subclass.")


class ItemList(list):
    """
    A class inherited from list. It will be returned by :meth:`nswebdav.sync.NutstoreDav.ls` or
    :meth:`nswebdav.async.AsyncNutstoreDav.ls` function.

    It works like a normal list, but accepts the xml response of PROPFIND.

    Then parse it into multiple :class:`.Item` s which are dict-like objects.
    """
    def __init__(self, xml_content):
        super().__init__()
        t = etree.fromstring(xml_content)

        responses = t.findall("d:response", t.nsmap)

        for response in responses:
            display_name = response.xpath(".//d:displayname/text()", namespaces=t.nsmap)[0]
            is_dir = bool(response.xpath(".//d:resourcetype/d:collection", namespaces=t.nsmap))
            content_length = int(response.xpath(".//d:getcontentlength/text()", namespaces=t.nsmap)[0])
            last_modified = datetime.strptime(
                response.xpath(".//d:getlastmodified/text()", namespaces=t.nsmap)[0],
                "%a, %d %b %Y %H:%M:%S %Z"
            )
            owner = response.xpath(".//d:owner/text()", namespaces=t.nsmap)[0]
            mime_type = response.xpath(".//d:getcontenttype/text()", namespaces=t.nsmap)[0]

            readable = bool(response.xpath(".//d:privilege/d:read", namespaces=t.nsmap))
            writable = bool(response.xpath(".//d:privilege/d:write", namespaces=t.nsmap))
            full_privilege = bool(response.xpath(".//d:privilege/d:all", namespaces=t.nsmap))
            read_acl = bool(response.xpath(".//d:privilege/d:read_acl", namespaces=t.nsmap))
            write_acl = bool(response.xpath(".//d:privilege/d:write_acl", namespaces=t.nsmap))

            item = Item(display_name, is_dir, content_length, last_modified, owner, mime_type, readable,
                        writable, full_privilege, read_acl, write_acl)
            self.append(item)


class Item(dict):
    """
    A class inherited from dict. It respects one result of dav.ls's response.

    It works like a normal dict but values can be accessed as attribute.

    Attributes
    ----------
    display_name : str
        the name of this item.
    is_dir : bool
        if this item is a directory.
    content_length : int
        the length of this item in bytes, a directory always has 0 length.
    last_modified : :class:`datetime.datetime`
        the last time this item was modified.
    owner : str
        the owner of this item.
    mime_type : str
        the mime type of this item.
    readable : bool
        if have read privilege on this item.
    writable : bool
        if have write privilege on this item.
    full_privilege : bool
        if have full privilege on this item.
    read_acl : bool
        if have privilege to read the privilege configuration of this item.
    write_acl : bool
        if have privilege to change the privilege configuration of this item.
    """
    def __init__(self, display_name, is_dir, content_length, last_modified, owner, mime_type, readable,
                 writable, full_privilege, read_acl, write_acl):
        super().__init__(
            display_name=display_name,
            is_dir=is_dir,
            content_length=content_length,
            last_modified=last_modified,
            owner=owner,
            mime_type=mime_type,
            readable=readable,
            writable=writable,
            full_privilege=full_privilege,
            read_acl=read_acl,
            write_acl=write_acl
        )

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError("No such key '%s'" % name)

    __setattr__ = dict.__setitem__

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError("No such key '%s'" % name)


def render_pubObject(path, users, groups, downloadable):
    users = users or []
    groups = groups or []
    downloadable = "false" if downloadable else "true"
    template = Template("""
        <?xml version="1.0" encoding="utf-8"?>
        <s:publish xmlns:s="http://ns.jianguoyun.com">
            <s:href>{{ path }}</s:href>
            {% if users or groups %}
            <s:acl>
            {% for user in users %}
                <s:username>{{ user }}</s:username>
            {% endfor %}
            {% for group in groups %}
                <s:group>{{ group }}</s:group>
            {% endfor %}
            </s:acl>
            {% endif %}
            <s:downloadDisabled>{{ downloadable }}</s:downloadDisabled>
        </s:publish>
    """.strip())
    return template.render(**locals())


def render_getSandboxAcl(path):
    template = Template("""
    <?xml version="1.0" encoding="utf-8"?>
    <s:get_acl xmlns:s="http://ns.jianguoyun.com">
        <s:href>{{ path }}</s:href>
    </s:get_acl>
    """.strip())
    return template.render(**locals())


def render_updateSandboxAcl(path, users, groups):
    users = users or []
    groups = groups or []
    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:sandbox xmlns:s="http://ns.jianguoyun.com">
                <s:href>{{ path }}</s:href>
                {% for user in users %}
                <s:acl>
                    <s:username>{{ user[0] }}</s:username>
                    <s:perm>{{ user[1] }}</s:perm>
                </s:acl>
                {% endfor %}
                {% for group in groups %}
                <s:acl>
                    <s:group>{{ group }}</s:group>
                    <s:perm>{{ group[1] }}</s:perm>
                </s:acl>
                {% endfor %}
            </s:sandbox>
        """.strip())
    return template.render(**locals())
