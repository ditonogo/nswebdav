from datetime import datetime
from urllib.parse import urljoin, unquote

from jinja2 import Template
from lxml import etree

#: This is a map of permission's number and its corresponding meanings.
#:
#: ================ =================================================================
#: number as string meanings
#: ================ =================================================================
#: "1"              download and preview
#: "2"              upload
#: "3"              upload, download, preview, remove and move
#: "4"              upload, download, preview, remove, move and change acls of others
#: "5"              preview
#: ================ =================================================================
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

    def _perform_operation_request(self, method, auth_tuple=None, client=None, **render_kwargs):
        auth_tuple = self._get_auth_tuple(auth_tuple)
        client = self._get_client(client)
        func = render_func.get(method)

        root_url = urljoin(self._base_url, self._operation_url)
        url = root_url + "/{method}".format(method=method)
        data = func(**render_kwargs)
        data = data.encode("utf-8")
        return client.request("POST", url, data=data, auth=auth_tuple)

    def _get_auth_tuple(self, auth_tuple=None):
        raise NotImplementedError("Should be implemented in subclass.")

    def _get_client(self, client=None):
        raise NotImplementedError("Should be implemented in subclass.")


class ItemList(list):
    """
    Contains multiple :class:`.Entity` s which are dict-like objects.

    Each Entity has the following values:

    href : str
        the relative url of this item.
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
    resource_perm : str
        the privilege of this tiem in str.
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

    def __init__(self, xml_content, ls=True):
        super().__init__()
        t = etree.fromstring(xml_content)

        responses = t.xpath(".//d:response", namespaces=t.nsmap)

        for response in responses:
            href = unquote(response.xpath(".//d:href/text()", namespaces=t.nsmap)[0])
            display_name = response.xpath(".//d:displayname/text()", namespaces=t.nsmap)[0] if ls else None
            is_dir = bool(response.xpath(".//d:resourcetype/d:collection", namespaces=t.nsmap))
            content_length = int(response.xpath(".//d:getcontentlength/text()", namespaces=t.nsmap)[0]) if ls else None
            last_modified = datetime.strptime(
                response.xpath(".//d:getlastmodified/text()", namespaces=t.nsmap)[0],
                "%a, %d %b %Y %H:%M:%S %Z"
            )
            owner = response.xpath(".//d:owner/text()", namespaces=t.nsmap)[0]
            mime_type = response.xpath(".//d:getcontenttype/text()", namespaces=t.nsmap)[0]

            readable = bool(response.xpath(".//d:privilege/d:read", namespaces=t.nsmap)) if ls else None
            writable = bool(response.xpath(".//d:privilege/d:write", namespaces=t.nsmap)) if ls else None
            full_privilege = bool(response.xpath(".//d:privilege/d:all", namespaces=t.nsmap)) if ls else None
            read_acl = bool(response.xpath(".//d:privilege/d:read_acl", namespaces=t.nsmap)) if ls else None
            write_acl = bool(response.xpath(".//d:privilege/d:write_acl", namespaces=t.nsmap)) if ls else None
            resource_perm = response.xpath(".//s:resourceperm/text()", namespaces=t.nsmap)[0] if not ls else None

            item = Entity(href=href,
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
                          write_acl=write_acl,
                          resource_perm=resource_perm)
            self.append(item)


class Entity(dict):
    """
    It works like a normal dict but values can be accessed as attribute.
    """

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


class History(list):
    """
    Contains multiple :class:`.Entity` s which are dict-like objects.

    History itself has the following values:

    reset : bool
        if histories are continuous, if is :code:`False`, all histories should be ignored and post again.

        :code:`reset is False` may caused by remote internal server error.
    cursor : int
        cursor of the last history.
    has_more : bool
        if histories are complete or there are more histories.

        if :code:`True`, you can call :code:`get_history` with :code:`cursor` to get the histories from :code:`cursor`.

    Each Entity has the following values:

    path : str
        the path of this item.
    size : int
        The size of this item represented in bytes.
    is_deleted : bool
        if this operation is deletion.
    is_dir : bool
        if this item is a directory.
    modified : :class:`datetime.datetime`
        The date of this operation.
    revision : int
        which revision of this operation.

    methods:
    """
    def __init__(self, xml_content):
        super().__init__()
        t = etree.fromstring(xml_content)

        self.reset = t.find("s:reset", t.nsmap).text == "true"
        self.cursor = int(t.find("s:cursor", t.nsmap).text, 16)
        self.has_more = t.find("s:hasMore", t.nsmap).text == "true"
        entries = t.findall("s:delta/s:entry", t.nsmap)

        for entry in entries:
            path = entry.xpath(".//s:path/text()", namespaces=t.nsmap)[0]
            size = int(entry.xpath(".//s:size/text()", namespaces=t.nsmap)[0])
            is_deleted = entry.xpath(".//s:isDeleted/text()", namespaces=t.nsmap)[0] == "true"
            is_dir = entry.xpath(".//s:isDir/text()", namespaces=t.nsmap)[0] == "true"
            modified = datetime.strptime(
                entry.xpath(".//s:modified/text()", namespaces=t.nsmap)[0],
                "%a, %d %b %Y %H:%M:%S %Z"
            )
            revision = int(entry.xpath(".//s:revision/text()", namespaces=t.nsmap)[0])
            item = Entity(path=path,
                          size=size,
                          is_deleted=is_deleted,
                          is_dir=is_dir,
                          modified=modified,
                          revision=revision)
            self.append(item)

    def next(self):
        """
        Call this function to get next cursor.

        Or get :code:`False` if there is no more history.

        :return: :code:`int` or :code:`False`.
        """
        if self.has_more:
            return self.cursor
        return False


class User(Entity):
    """
    It works like a normal dict but values can be accessed as attribute.

    It has the following values.

    user_name : str
        the user name.
    is_admin : bool
        if this user is admin of this team.
    state : str
        the account state of user. Could be "free_trial_team_edition", "advanced_team_edition",
        "preminum_team_edition", "standard_team_edition" or "frozen".
    team_id : int
        the team id of user. :code:`None` if state equals to "frozen".
    storage_quota : int
        the total storage quota in bytes. :code:`None` if state equals to "frozen".
    used_storage : int
        the used storage space in bytes. :code:`None` if state equals to "frozen".
    expire_time : int
        the left active time in milliseconds. :code:`None` if state equals to "frozen".
    collections : list
        a list contains all top folders. Each folder is an instance of :class:`.Entity` and
        has:

        :code:`href`: the absolute path of this top folder.

        :code:`used_storage`: the used storage space in bytes of this top folder.

        :code:`owner`: if user is the owner of this top folder.
    """
    def __init__(self, xml_content):
        t = etree.fromstring(xml_content)
        user_name = t.find("s:username", t.nsmap).text
        is_admin = None
        state = t.find("s:account_state", t.nsmap).text
        team_id = None
        storage_quota = None
        used_storage = None
        expire_time = None
        if state != "frozen":
            _is_admin = t.find("s:team/s:is_admin", t.nsmap)
            if _is_admin is not None:
                is_admin = _is_admin.text == "true"
            team_id = int(t.find("s:team/s:id", t.nsmap).text)
            storage_quota = int(t.find("s:storage_quota", t.nsmap).text)
            used_storage = int(t.find("s:used_storage", t.nsmap).text)
            expire_time = int(t.find("s:expire_time", t.nsmap).text)
        _collections = t.findall("s:collection", t.nsmap)

        collections = []
        for _collection in _collections:
            _href = _collection.xpath(".//s:href/text()", namespaces=t.nsmap)[0]
            _used_storage = int(_collection.xpath(".//s:used_storage/text()", namespaces=t.nsmap)[0])
            _owner = _collection.xpath(".//s:owner/text()", namespaces=t.nsmap)[0] == "true"
            collection = Entity(href=_href,
                                used_storage=_used_storage,
                                owner=_owner)
            collections.append(collection)
        super().__init__(user_name=user_name,
                         is_admin=is_admin,
                         state=state,
                         team_id=team_id,
                         storage_quota=storage_quota,
                         used_storage=used_storage,
                         expire_time=expire_time,
                         collections=collections)


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


def render_delta(folder, cursor):
    if cursor:
        cursor = "%X" % cursor
    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:delta xmlns:s="http://ns.jianguoyun.com">
                <s:folderName>{{ folder }}</s:folderName>
                {% if cursor %}<s:cursor>{{ cursor }}</s:cursor>{% endif %}
            </s:delta>
        """.strip())
    return template.render(**locals())


def render_latestDeltaCursor(folder):
    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:delta xmlns:s="http://ns.jianguoyun.com">
                <s:folderName>{{ folder }}</s:folderName>
            </s:delta>
        """.strip())
    return template.render(**locals())


def render_submitCopyPubObject(path, url, password):
    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:copy_pub xmlns:s="http://ns.jianguoyun.com">
                <s:href>{{ path }}</s:href>
                <s:published_object_url>{{ url }}</s:published_object_url>
                {% if password %}<s:copy_password>{{ password }}</s:copy_password>{% endif %}
            </s:copy_pub>
        """.strip())
    return template.render(**locals())


def render_pollCopyPubObject(copy_uuid):
    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:copy_pub xmlns:s="http://ns.jianguoyun.com">
                <s:copy_uuid>{{ copy_uuid }}</s:copy_uuid>
            </s:copy_pub>
        """.strip())
    return template.render(**locals())


def render_search(keywords, path):
    keywords = " ".join(keywords)
    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:search xmlns:s="http://ns.jianguoyun.com">
                <s:keywords>{{ keywords }}</s:keywords>
                <s:path>{{ path }}</s:path>
            </s:search>
        """.strip())
    return template.render(**locals())


render_func = {
    "pubObject": render_pubObject,
    "getSandboxAcl": render_getSandboxAcl,
    "updateSandboxAcl": render_updateSandboxAcl,
    "delta": render_delta,
    "latestDeltaCursor": render_latestDeltaCursor,
    "submitCopyPubObject": render_submitCopyPubObject,
    "pollCopyPubObject": render_pollCopyPubObject,
    "search": render_search
}
