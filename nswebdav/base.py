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
    def __init__(self, base_url, dav_url="/dav", operation_url="/nsdav"):
        self._base_url = base_url
        self._operation_url = operation_url
        self._dav_url = dav_url


class ItemList(list):
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
            mime_type = response.xpath(".//d:getcontenttype", namespaces=t.nsmap)[0]

            readable = bool(response.xpath(".//d:privilege/d:read", namespaces=t.nsmap))
            writable = bool(response.xpath(".//d:privilege/d:write", namespaces=t.nsmap))
            full_privilege = bool(response.xpath(".//d:privilege/d:all", namespaces=t.nsmap))
            read_acl = bool(response.xpath(".//d:privilege/d:read_acl", namespaces=t.nsmap))
            write_acl = bool(response.xpath(".//d:privilege/d:write_acl", namespaces=t.nsmap))

            item = Item(display_name, is_dir, content_length, last_modified, owner, mime_type, readable,
                        writable, full_privilege, read_acl, write_acl)
            self.append(item)


class Item(dict):
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
