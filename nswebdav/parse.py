from datetime import datetime

from lxml import etree
from urllib.parse import unquote


def parse_ls(xml_content):
    t = etree.fromstring(xml_content)

    responses = t.findall(".//d:response", t.nsmap)

    results = []
    for response in responses:
        href = response.findtext(".//d:href", None, t.nsmap)
        href = unquote(href) if href else None
        display_name = response.findtext(".//d:displayname", None, t.nsmap)
        is_dir = response.find(".//d:resourcetype/d:collection", t.nsmap) is not None
        content_length = response.findtext(".//d:getcontentlength", None, t.nsmap)
        content_length = int(content_length) if content_length else None
        last_modified = response.findtext(".//d:getlastmodified", None, t.nsmap)
        last_modified = datetime.strptime(
            last_modified,
            "%a, %d %b %Y %H:%M:%S %Z"
        ).timestamp() if last_modified else None
        owner = response.findtext(".//d:owner", None, t.nsmap)
        mime_type = response.findtext(".//d:getcontenttype", None, t.nsmap)
        readable = response.find(".//d:privilege/d:read", t.nsmap) is not None
        writable = response.find(".//d:privilege/d:write", t.nsmap) is not None
        full_privilege = response.find(".//d:privilege/d:all", t.nsmap) is not None
        read_acl = response.find(".//d:privilege/d:read_acl", t.nsmap) is not None
        write_acl = response.find(".//d:privilege/d:write_acl", t.nsmap) is not None

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

    responses = t.findall(".//d:response", t.nsmap)

    results = []
    for response in responses:
        href = response.findtext(".//d:href", None, t.nsmap)
        href = unquote(href) if href else None
        is_dir = response.find(".//d:resourcetype/d:collection", t.nsmap) is not None
        last_modified = response.findtext(".//d:getlastmodified", None, t.nsmap)
        last_modified = datetime.strptime(
            last_modified,
            "%a, %d %b %Y %H:%M:%S %Z"
        ).timestamp() if last_modified else None
        content_length = response.findtext(".//d:getcontentlength", None, t.nsmap)
        content_length = int(content_length) if content_length else None
        resource_perm = response.findtext(".//s:resourceperm", None, t.nsmap)
        owner = response.findtext(".//d:owner", None, t.nsmap)
        mime_type = response.findtext(".//d:getcontenttype", None, t.nsmap)

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
    share_link = t.findtext("s:sharelink", "", t.nsmap).strip()
    return share_link


def parse_acl(xml_content):
    t = etree.fromstring(xml_content)
    results = Entity({
        "users": Entity(),
        "groups": Entity()
    })
    acls = t.findall("s:acl", t.nsmap)
    for acl in acls:
        user = acl.findtext("s:username", None, t.nsmap)
        perm = acl.findtext("s:perm", "", t.nsmap)
        if user is not None:
            results.users[user] = perm
        else:
            group = acl.findtext("s:group", "", t.nsmap)
            results.groups[group] = perm
    return results


def parse_latest_cursor(xml_content):
    t = etree.fromstring(xml_content)
    cursor = t.findtext("s:cursor", None, t.nsmap)
    return int(cursor, 16) if cursor is not None else None


def parse_cp_shared_object(xml_content):
    t = etree.fromstring(xml_content)
    return t.findtext("s:copy_uuid", "", t.nsmap)


def parse_content_url(xml_content):
    t = etree.fromstring(xml_content)
    href = unquote(t.findtext("s:href", "", t.nsmap))
    return href


def parse_team_members(xml_content):
    t = etree.fromstring(xml_content)

    results = []
    for member in t.getchildren():
        is_admin = bool("admin" in member.tag)
        user_name = member.findtext("s:username", None, t.nsmap)
        nickname = member.findtext("s:nickname", None, t.nsmap)
        storage_quota = member.findtext("s:storage_quota", None, t.nsmap)
        storage_quota = int(storage_quota) if storage_quota else None
        ldap_user = member.findtext("s:ldap_user", None, t.nsmap)
        ldap_user = ldap_user == "true" if ldap_user else None
        disabled = member.findtext("s:disabled", None, t.nsmap)
        disabled = disabled == "true" if disabled else None
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

    reset = t.findtext("s:reset", None, t.nsmap)
    reset = reset == "true" if reset else None
    cursor = t.findtext("s:cursor", None, t.nsmap)
    cursor = int(cursor, 16) if cursor else None
    has_more = t.findtext("s:hasMore", None, t.nsmap)
    has_more = has_more == "true" if has_more else None

    history = Entity(reset=reset,
                     cursor=cursor,
                     has_more=has_more,
                     deltas=[])

    entries = t.findall("s:delta/s:entry", t.nsmap)
    for entry in entries:
        path = entry.findtext(".//s:path", None, t.nsmap)
        size = entry.findtext(".//s:size", None, t.nsmap)
        size = int(size) if size else None
        is_deleted = entry.findtext(".//s:isDeleted", None, t.nsmap)
        is_deleted = is_deleted == "true" if is_deleted else None
        is_dir = entry.findtext(".//s:isDir", None, t.nsmap)
        is_dir = is_dir == "true" if is_dir else None
        modified = entry.findtext(".//s:modified", None, t.nsmap)
        modified = datetime.strptime(
            modified,
            "%a, %d %b %Y %H:%M:%S %Z"
        ).timestamp() if modified else None
        revision = entry.findtext(".//s:revision", None, t.nsmap)
        revision = int(revision) if revision else None
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
    user_name = t.findtext("s:username", None, t.nsmap)
    state = t.findtext("s:account_state", None, t.nsmap)
    storage_quota = t.findtext("s:storage_quota", None, t.nsmap)
    storage_quota = int(storage_quota) if storage_quota else None
    used_storage = t.findtext("s:used_storage", None, t.nsmap)
    used_storage = int(used_storage) if used_storage else None
    is_admin = t.findtext("s:team/s:is_admin", None, t.nsmap)
    is_admin = is_admin.text == "true" if is_admin else None
    team_id = t.findtext("s:team/s:id", None, t.nsmap)
    expire_time = t.findtext("s:expire_time", None, t.nsmap)
    expire_time = int(expire_time) / 1000 if expire_time else None  # convert to timestamp

    _collections = t.findall("s:collection", t.nsmap)
    collections = []
    for _collection in _collections:
        href = _collection.findtext(".//s:href", None, t.nsmap)
        href = unquote(href) if href else None
        used_storage = _collection.findtext(".//s:used_storage", None, t.nsmap)
        used_storage = int(used_storage) if used_storage else None
        is_owner = _collection.findtext(".//s:owner", None, t.nsmap)
        is_owner = is_owner == "true" if is_owner else None
        collection = Entity(href=href,
                            used_storage=used_storage,
                            is_owner=is_owner)
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
    user_name = t.findtext("s:username", None, t.nsmap)
    storage_quota = t.findtext("s:storageQuota", None, t.nsmap)
    storage_quota = int(storage_quota) if storage_quota else None
    expire_time = t.findtext("s:expireTime", None, t.nsmap)
    expire_time = int(expire_time) / 1000 if expire_time else None  # convert to timestamp

    _sandboxes = t.findall("s:sandbox", t.nsmap)
    sandboxes = []
    for _sandbox in _sandboxes:
        name = _sandbox.findtext("s:name", None, t.nsmap)
        storage_quota = _sandbox.findtext("s:storageQuota", None, t.nsmap)
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
        group_id = _subgroup.findtext("s:id", None, t.nsmap)
        group_id = int(group_id) if group_id else None
        name = _subgroup.findtext("s:name", None, t.nsmap)
        subgroup = Entity(group_id=group_id,
                          name=name)
        subgroups.append(subgroup)

    _admins = t.findall("s:admin", t.nsmap)
    admins = []
    for _admin in _admins:
        user_name = _admin.findtext("s:username", None, t.nsmap)
        nickname = _admin.findtext("s:nickname", None, t.nsmap)
        admin = Entity(user_name=user_name,
                       nickname=nickname)
        admins.append(admin)

    _users = t.findall("s:user", t.nsmap)
    users = []
    for _user in _users:
        user_name = _user.findtext("s:username", None, t.nsmap)
        nickname = _user.findtext("s:nickname", None, t.nsmap)
        user = Entity(user_name=user_name,
                      nickname=nickname)
        users.append(user)

    entity = Entity(subgroups=subgroups,
                    admins=admins,
                    users=users)
    return entity


def parse_created_group(xml_content):
    t = etree.fromstring(xml_content)

    group_id = t.findtext("s:id", None, t.nsmap)
    group_id = int(group_id) if group_id else None
    return group_id


def parse_audit_logs(xml_content):
    t = etree.fromstring(xml_content)

    log_num = t.findtext("s:log_num", None, t.nsmap)
    log_num = int(log_num) if log_num else None
    first_operation_time = t.findtext("s:first_operation_time", None, t.nsmap)
    first_operation_time = int(first_operation_time) / 1000 if first_operation_time else None  # convert to timestamp
    last_operation_time = t.findtext("s:last_operation_time", None, t.nsmap)
    last_operation_time = int(last_operation_time) / 1000 if last_operation_time else None  # convert to timestamp
    has_more = t.findtext("s:has_more", None, t.nsmap)
    has_more = has_more == "true" if has_more else None

    _activities = t.findall("s:activity", t.nsmap)
    activities = []
    for _activity in _activities:
        operator = _activity.findtext("s:operator", None, t.nsmap)
        operation = _activity.findtext("s:operation", None, t.nsmap)
        ip = _activity.findtext("s:ip", None, t.nsmap)
        ip_location = _activity.findtext("s:ip_location", None, t.nsmap)
        terminal = _activity.findtext("s:terminal", None, t.nsmap)
        consuming = _activity.findtext("s:consuming", None, t.nsmap)

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
