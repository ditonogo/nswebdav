from datetime import datetime

from lxml import etree
from urllib.parse import unquote


def parse_ls(xml_content):
    t = etree.fromstring(xml_content)

    responses = t.xpath(".//d:response", namespaces=t.nsmap)

    results = []
    for response in responses:
        href = unquote(response.xpath(".//d:href/text()", namespaces=t.nsmap)[0])
        display_name = response.xpath(".//d:displayname/text()", namespaces=t.nsmap)[0]
        is_dir = bool(response.xpath(".//d:resourcetype/d:collection", namespaces=t.nsmap))
        content_length = int(response.xpath(".//d:getcontentlength/text()", namespaces=t.nsmap)[0])
        last_modified = datetime.strptime(
            response.xpath(".//d:getlastmodified/text()", namespaces=t.nsmap)[0],
            "%a, %d %b %Y %H:%M:%S %Z"
        ).timestamp()
        owner = response.xpath(".//d:owner/text()", namespaces=t.nsmap)[0]
        mime_type = response.xpath(".//d:getcontenttype/text()", namespaces=t.nsmap)[0]
        readable = bool(response.xpath(".//d:privilege/d:read", namespaces=t.nsmap))
        writable = bool(response.xpath(".//d:privilege/d:write", namespaces=t.nsmap))
        full_privilege = bool(response.xpath(".//d:privilege/d:all", namespaces=t.nsmap))
        read_acl = bool(response.xpath(".//d:privilege/d:read_acl", namespaces=t.nsmap))
        write_acl = bool(response.xpath(".//d:privilege/d:write_acl", namespaces=t.nsmap))

        entity = Entity(href=href,
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
                        write_acl=write_acl)
        results.append(entity)
    return results


def parse_search(xml_content):
    t = etree.fromstring(xml_content)

    responses = t.xpath(".//d:response", namespaces=t.nsmap)

    results = []
    for response in responses:
        href = unquote(response.xpath(".//d:href/text()", namespaces=t.nsmap)[0])
        is_dir = bool(response.xpath(".//d:resourcetype/d:collection", namespaces=t.nsmap))
        last_modified = datetime.strptime(
            response.xpath(".//d:getlastmodified/text()", namespaces=t.nsmap)[0],
            "%a, %d %b %Y %H:%M:%S %Z"
        ).timestamp()
        content_length = int(response.xpath(".//d:getcontentlength/text()", namespaces=t.nsmap)[0])
        resource_perm = response.xpath(".//s:resourceperm/text()", namespaces=t.nsmap)[0]
        owner = response.xpath(".//d:owner/text()", namespaces=t.nsmap)[0]
        mime_type = response.xpath(".//d:getcontenttype/text()", namespaces=t.nsmap)[0]

        entity = Entity(href=href,
                        is_dir=is_dir,
                        last_modified=last_modified,
                        owner=owner,
                        mime_type=mime_type,
                        resource_perm=resource_perm,
                        content_length=content_length)
        results.append(entity)
    return results


def parse_share_link(xml_content):
    t = etree.fromstring(xml_content)
    share_link = t.find("s:sharelink", t.nsmap).text.strip()
    return share_link


def parse_acl(xml_content):
    t = etree.fromstring(xml_content)
    results = Entity({
        "users": Entity(),
        "groups": Entity()
    })
    acls = t.findall("s:acl", t.nsmap)
    for acl in acls:
        user = acl.find("s:username", t.nsmap)
        perm = acl.find("s:perm", t.nsmap)
        if user is not None:
            results.users[user.text] = perm.text
        else:
            group = acl.find("s:group", t.nsmap)
            results.groups[group.text] = perm.text
    return results


def parse_latest_cursor(xml_content):
    t = etree.fromstring(xml_content)
    return int(t.find("s:cursor", t.nsmap).text, 16)


def parse_cp_shared_object(xml_content):
    t = etree.fromstring(xml_content)
    return t.find("s:copy_uuid", t.nsmap).text


def parse_content_url(xml_content):
    t = etree.fromstring(xml_content)
    href = unquote(t.find("s:href", t.nsmap).text)
    return href


def parse_team_members(xml_content):
    t = etree.fromstring(xml_content)

    results = []
    for member in t.getchildren():
        is_admin = bool("admin" in member.tag)
        user_name = member.find("s:username", t.nsmap).text
        nickname = member.find("s:nickname", t.nsmap).text
        storage_quota = int(member.find("s:storage_quota", t.nsmap).text)
        ldap_user_element = member.find("s:ldap_user", t.nsmap)
        ldap_user = None
        if ldap_user_element is not None:
            ldap_user = ldap_user_element.text == "true"
        disabled_element = member.find("s:disabled", t.nsmap)
        disabled = None
        if disabled_element is not None:
            disabled = disabled_element.text == "true"
        entity = Entity(admin=is_admin,
                        user_name=user_name,
                        nickname=nickname,
                        storage_quota=storage_quota,
                        ldap_user=ldap_user,
                        disabled=disabled)
        results.append(entity)
    return results


def parse_history(xml_content):
    t = etree.fromstring(xml_content)

    reset = t.find("s:reset", t.nsmap).text == "true"
    cursor = int(t.find("s:cursor", t.nsmap).text, 16)
    has_more = t.find("s:hasMore", t.nsmap).text == "true"

    history = Entity(reset=reset,
                     cursor=cursor,
                     has_more=has_more,
                     deltas=[])

    entries = t.findall("s:delta/s:entry", t.nsmap)
    for entry in entries:
        path = entry.xpath(".//s:path/text()", namespaces=t.nsmap)[0]
        size = int(entry.xpath(".//s:size/text()", namespaces=t.nsmap)[0])
        is_deleted = entry.xpath(".//s:isDeleted/text()", namespaces=t.nsmap)[0] == "true"
        is_dir = entry.xpath(".//s:isDir/text()", namespaces=t.nsmap)[0] == "true"
        modified = datetime.strptime(
            entry.xpath(".//s:modified/text()", namespaces=t.nsmap)[0],
            "%a, %d %b %Y %H:%M:%S %Z"
        ).timestamp()
        revision = int(entry.xpath(".//s:revision/text()", namespaces=t.nsmap)[0])
        entity = Entity(path=path,
                        size=size,
                        is_deleted=is_deleted,
                        is_dir=is_dir,
                        modified=modified,
                        revision=revision)
        history.deltas.append(entity)
    return history


def parse_user_info(xml_content):
    t = etree.fromstring(xml_content)
    user_name = t.find("s:username", t.nsmap).text
    is_admin = None
    state = t.find("s:account_state", t.nsmap).text
    team_id = None
    storage_quota = None
    used_storage = None
    expire_time = None
    if state not in ("frozen", "free"):
        storage_quota = int(t.find("s:storage_quota", t.nsmap).text)
        used_storage = int(t.find("s:used_storage", t.nsmap).text)
        if "team_edition" in state:
            _is_admin = t.find("s:team/s:is_admin", t.nsmap)
            if _is_admin is not None:
                is_admin = _is_admin.text == "true"
            team_id = int(t.find("s:team/s:id", t.nsmap).text)
            expire_time = int(t.find("s:expire_time", t.nsmap).text) / 1000  # convert to timestamp
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
    entity = Entity(user_name=user_name,
                    is_admin=is_admin,
                    state=state,
                    team_id=team_id,
                    storage_quota=storage_quota,
                    used_storage=used_storage,
                    expire_time=expire_time,
                    collections=collections)
    return entity


def parse_team_member_info(xml_content):
    t = etree.fromstring(xml_content)
    user_name = t.find("s:username", t.nsmap).text
    storage_quota = int(t.find("s:storageQuota", t.nsmap).text)
    expire_time = int(t.find("s:expireTime", t.nsmap).text) / 1000  # convert to timestamp

    _sandboxes = t.findall("s:sandbox", t.nsmap)
    sandboxes = []
    for _sandbox in _sandboxes:
        name = _sandbox.find("s:name", t.nsmap)
        storage_quota = _sandbox.find("s:storageQuota", t.nsmap)
        sandbox = Entity(name=name,
                         storage_quota=storage_quota)
        sandboxes.append(sandbox)
    entity = Entity(user_name=user_name,
                    storage_quota=storage_quota,
                    expire_time=expire_time,
                    sandboxes=sandboxes)
    return entity


def parse_group_members(xml_content):
    t = etree.fromstring(xml_content)

    _subgroups = t.findall("s:subgroup", t.nsmap)
    subgroups = []
    for _subgroup in _subgroups:
        group_id = int(_subgroup.find("s:id", t.nsmap).text)
        name = _subgroup.find("s:name", t.nsmap).text
        subgroup = Entity(group_id=group_id,
                          name=name)
        subgroups.append(subgroup)

    _admins = t.findall("s:admin", t.nsmap).text
    admins = []
    for _admin in _admins:
        user_name = _admin.find("s:username", t.nsmap).text
        nickname = _admin.find("s:nickname", t.nsmap).text
        admin = Entity(user_name=user_name,
                       nickname=nickname)
        admins.append(admin)

    _users = t.findall("s:user", t.nsmap)
    users = []
    for _user in _users:
        user_name = _user.find("s:username", t.nsmap).text
        nickname = _user.find("s:nickname", t.nsmap).text
        user = Entity(user_name=user_name,
                      nickname=nickname)
        users.append(user)

    entity = Entity(subgroups=subgroups,
                    admins=admins,
                    users=users)
    return entity


def parse_created_group(xml_content):
    t = etree.fromstring(xml_content)

    group_id = int(t.find("s:id", t.nsmap).text)
    return group_id


def parse_audit_logs(xml_content):
    t = etree.fromstring(xml_content)

    log_num = int(t.find("s:log_num", t.nsmap).text)
    first_operation_time = int(t.find("s:first_operation_time", t.nsmap).text) / 1000  # convert to timestamp
    last_operation_time = int(t.find("s:last_operation_time", t.nsmap).text) / 1000  # convert to timestamp
    has_more = t.find("s:has_more", t.nsmap) == "true"

    _activities = t.findall("s:activity", t.nsmap)
    activities = []
    for _activity in _activities:
        operator = _activity.find("s:operator", t.nsmap).text
        operation = _activity.find("s:operation", t.nsmap).text
        ip = _activity.find("s:ip", t.nsmap).text
        ip_location = _activity.find("s:ip_location", t.nsmap).text
        terminal = _activity.find("s:terminal", t.nsmap).text
        consuming = _activity.find("s:consuming", t.nsmap).text

        activity = Entity(operator=operator,
                          operation=operation,
                          ip=ip,
                          ip_location=ip_location,
                          terminal=terminal,
                          consuming=consuming)
        activities.append(activity)

    entity = Entity(log_num=log_num,
                    first_operation_time=first_operation_time,
                    last_operation_time=last_operation_time,
                    has_more=has_more,
                    activities=activities)
    return entity


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
