from jinja2 import Template

from nswebdav.constants import OPERATION_TYPE


def render_pubObject(path, users, groups, downloadable):
    users = users or []
    groups = groups or []
    downloadable = str(downloadable).lower()
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


def render_directContentUrl(path, platform, link_type):
    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:direct_content_link xmlns:s="http://ns.jianguoyun.com">
                <s:href>{{ path }}</s:href>
                <s:platform>{{ platform }}</s:platform>
                <s:link_type>{{ link_type }}</s:link_type>
            </s:direct_content_link>
        """.strip())
    return template.render(**locals())


def render_directPubContentUrl(link, platform, link_type, relative_path, password):
    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:direct_content_link xmlns:s="http://ns.jianguoyun.com">
                <s:href>{{ link }}</s:href>
                <s:platform>{{ platform }}</s:platform>
                <s:link_type>{{ link_type }}</s:link_type>
                {% if relative_path %}<s:relative_path>{{ relative_path }}</s:relative_path>{% endif %}
                {% if password %}<s:password>{{ password }}</s:password>{% endif %}
            </s:direct_content_link>
        """.strip())
    return template.render(**locals())


def render_updateTeamInfo(name):
    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:team xmlns:s="http://ns.jianguoyun.com">
                <s:name>{{ name }}</s:name>
            </s:team>
        """.strip())
    return template.render(**locals())


def render_createEtpTeamMember(users):
    length = len(users)
    if length == 0:
        raise ValueError("Empty users")
    if length > 10:
        raise ValueError("Too many users at once.")
    for user in users:
        try:
            _ = user["user_name"]
            _ = user["password"]
            _ = user["storage_quota"]
        except KeyError as e:
            missing_key = e.args[0]
            raise KeyError("Missing %s" % missing_key)
        if "ldap_user" in user:
            user["ldap_user"] = str(user["ldap_user"]).lower()

    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:team xmlns:s="http://ns.jianguoyun.com">
                {% for user in users %}
                <s:user>
                    <s:username>{{ user["user_name"] }}</s:username>
                    <s:password>{{ user["password"] }}</s:password>
                    <s:storage_quota>{{ user["storage_quota"] }}</s:storage_quota>
                    {% if "nickname" in user %}
                        <s:nickname>{{ user["nickname"] }}</s:nickname>
                    {% endif %}
                    {% if "ldap_user" in user %}
                        <s:ldap_user>{{ user["ldap_user"] }}</s:ldap_user>
                    {% endif %}
                    {% if "ldap_id" in user %}
                        <s:ldap_id>{{ user["ldap_id"] }}</s:ldap_id>
                    {% endif %}
                </s:user>
                {% endfor %}
            </s:team>
    """.strip())
    return template.render(**locals())


def render_updateTeamMemberStorageQuota(user_name, storage_quota):
    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:team xmlns:s="http://ns.jianguoyun.com">
                <s:username>{{ user_name }}</s:username>
                <s:storageQuota>{{ storage_quota }}</s:storageQuota>
            </s:team>
    """.strip())
    return template.render(**locals())


def render_getTeamMemberInfo(user_name):
    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:team xmlns:s="http://ns.jianguoyun.com">
                <s:username>{{ user_name }}</s:username>
            </s:team>
    """.strip())
    return template.render(**locals())


def render_removeTeamMember(user_name, folder_receipt, clean_perms):
    if clean_perms:
        folder_receipt = None
    clean_perms = str(clean_perms).lower()
    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:team xmlns:s="http://ns.jianguoyun.com">
                <s:username>{{ user_name }}</s:username>
                {% if folder_receipt %}
                <s:folder_receipt>{{ folder_receipt }}</s:folder_receipt>
                {% endif %}
                <s:clean_perms>{{ clean_perms }}</s:clean_perms>
            </s:team>
    """.strip())
    return template.render(**locals())


def render_getGroupMembers(group_id):
    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:group xmlns:s="http://ns.jianguoyun.com">
                <s:id>{{ group_id }}</s:id>
            </s:group>
    """.strip())
    return template.render(**locals())


def render_createGroup(parent_group_id, name, admins, users):
    if isinstance(admins, str):
        admins = [admins]
    users = users or []

    if len(admins) == 0:
        raise ValueError("Empty admins")
    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:group xmlns:s="http://ns.jianguoyun.com">
                <s:id>{{ parent_group_id }}</s:id>
                <s:name>{{ name }}</s:name>
                {% for admin in admins %}
                <s:admin>
                    <s:username>{{ admin }}</s:username>
                </s:admin>
                {% endfor %}
                {% for user in users %}
                <s:user>
                    <s:username>{{ admin }}</s:username>
                </s:user>
                {% endfor %}
            </s:group>
    """.strip())
    return template.render(**locals())


def render_addMemberToGroup(group_id, users):
    if len(users) == 0:
        raise ValueError("Empty users")
    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:group xmlns:s="http://ns.jianguoyun.com">
                <s:id>{{ group_id }}</s:id>
                {% for user in users %}
                <s:user>
                    <s:username>{{ user }}</s:username>
                </s:user>
                {% endfor %}
            </s:group>
    """.strip())
    return template.render(**locals())


def render_removeMemberFromGroup(group_id, users, subgroups):
    users = users or []
    subgroups = subgroups or []
    if len(users) == len(subgroups) == 0:
        raise ValueError("Empty users and subgroups")
    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:group xmlns:s="http://ns.jianguoyun.com">
                <s:id>{{ group_id }}</s:id>
                {% for subgroup in subgroups %}
                <s:subGroup>
                    <s:id>{{ subgroup }}</s:id>
                </s:subGroup>
                {% endfor %}
                {% for user in users %}
                <s:user>
                    <s:username>{{ user }}</s:username>
                </s:user>
                {% endfor %}
            </s:group>
    """.strip())
    return template.render(**locals())


def render_updateTeamMemberStatus(users):
    for key in users.keys():
        users[key] = str(users[key]).lower()
    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:team xmlns:s="http://ns.jianguoyun.com">
                {% for user, disabled in users.items() %}
                <s:user>
                    <s:username>{{ user }}</s:username>
                    <s:disabled>{{ disabled }}</s:disabled>
                </s:user>
                {% endfor %}
            </s:team>
    """.strip())
    return template.render(**locals())


def render_queryAuditLogs(time_start, time_end, user_name, op_type, file_name):
    time_start = round(time_start * 1000)
    time_end = round(time_end * 1000)

    if op_type not in OPERATION_TYPE:
        raise ValueError("Invalid operation")

    template = Template("""
            <?xml version="1.0" encoding="utf-8"?>
            <s:search xmlns:s="http://ns.jianguoyun.com">
                <s:time_start>{{ time_start }}</s:time_start>
                <s:time_end>{{ time_end }}</s:time_end>
                {% if user_name %}
                <s:username>{{ user_name }}</s:username>
                {% endif %}
                {% if op_type %}
                <s:op_type>{{ op_type }}</s:op_type>
                {% endif %}
                {% if file_name %}
                <s:filename>{{ file_name }}</s:filename>
                {% endif %}
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
    "search": render_search,
    "directContentUrl": render_directContentUrl,
    "directPubContentUrl": render_directPubContentUrl,
    "updateTeamInfo": render_updateTeamInfo,
    "createEtpTeamMember": render_createEtpTeamMember,
    "updateTeamMemberStorageQuota": render_updateTeamMemberStorageQuota,
    "removeTeamMember": render_removeTeamMember,
    "getGroupMembers": render_getGroupMembers,
    "createGroup": render_createGroup,
    "addMemberToGroup": render_addMemberToGroup,
    "removeMemberFromGroup": render_removeMemberFromGroup,
    "updateTeamMemberStatus": render_updateTeamMemberStatus,
    "queryAuditLogs": render_queryAuditLogs,
}