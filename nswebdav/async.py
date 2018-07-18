import asyncio
from urllib.parse import urljoin

import aiohttp

from nswebdav.base import NutstoreDavBase
from nswebdav.exceptions import NSWebDavHTTPError
from nswebdav.parse import *


class AsyncNutstoreDav(NutstoreDavBase):
    """
    An implementation which supports async usage.

    By default, ``auth_tuple`` is :obj:`None`, you need to config it by calling :meth:`.config`
    or by passing a tuple in every methods.

    There is a default client :class:`aiohttp.ClientSession`, but you can still overwrite it by calling :meth:`.config`
    or passing a custom one in every methods.
    """
    def __init__(self, base_url="https://dav.jianguoyun.com", dav_url="/dav", operation_url="/nsdav"):
        super().__init__(base_url, dav_url, operation_url)
        loop = asyncio.get_event_loop()
        self._client = aiohttp.ClientSession(loop=loop)

    def _get_auth_tuple(self, auth_tuple=None):
        return aiohttp.BasicAuth(*(auth_tuple or self._auth_tuple))

    def close(self):
        self._client.loop.run_until_complete(self._client.close())

    async def ls(self, path, auth_tuple=None, client=None):
        response = await self._perform_dav_request("PROPFIND", auth_tuple, client, path=path)

        if response.status == 207:
            return parse_ls(await response.read())
        raise NSWebDavHTTPError(response.status, await response.read())

    async def mkdir(self, path, auth_tuple=None, client=None):
        response = await self._perform_dav_request("MKCOL", auth_tuple, client, path=path)

        if response.status == 201:
            return True
        raise NSWebDavHTTPError(response.status, await response.read())

    async def upload(self, content, path, auth_tuple=None, client=None):
        response = await self._perform_dav_request("PUT", auth_tuple, client, path=path, data=content)

        if response.status == 201:
            return "Upload"
        elif response.status == 204:
            return "Overwrite"
        raise NSWebDavHTTPError(response.status, await response.read())

    async def download(self, path, auth_tuple=None, client=None):
        response = await self._perform_dav_request("GET", auth_tuple, client, path=path)

        if response.status == 200:
            return await response.read()
        raise NSWebDavHTTPError(response.status, await response.read())

    async def mv(self, from_path, to_path, auth_tuple=None, client=None):
        response = await self._perform_dav_request("MOVE", auth_tuple, client, from_path=from_path, to_path=to_path)

        if response.status == 201:
            return True
        raise NSWebDavHTTPError(response.status, await response.read())

    async def cp(self, from_path, to_path, auth_tuple=None, client=None):
        response = await self._perform_dav_request("COPY", auth_tuple, client, from_path=from_path, to_path=to_path)

        if response.status == 201:
            return True
        raise NSWebDavHTTPError(response.status, await response.read())

    async def rm(self, path, auth_tuple=None, client=None):
        response = await self._perform_dav_request("DELETE", auth_tuple, client, path=path)

        if response.status == 204:
            return True
        raise NSWebDavHTTPError(response.status, await response.read())

    async def share(self, path, users=None, groups=None, downloadable=True, auth_tuple=None, client=None):
        path = self._dav_url + path
        response = await self._perform_operation_request("pubObject", auth_tuple, client,
                                                         path=path, users=users, groups=groups,
                                                         downloadable=downloadable)

        if response.status == 200:
            return parse_share_link(await response.read())
        raise NSWebDavHTTPError(response.status, await response.read())

    async def get_acl(self, path, auth_tuple=None, client=None):
        path = self._dav_url + path
        response = await self._perform_operation_request("getSandboxAcl", auth_tuple, client,
                                                         path=path)

        if response.status == 200:
            return parse_acl(await response.read())
        raise NSWebDavHTTPError(response.status, await response.read())

    async def set_acl(self, path, users=None, groups=None, auth_tuple=None, client=None):
        path = self._dav_url + path
        response = await self._perform_operation_request("updateSandboxAcl", auth_tuple, client,
                                                         path=path, users=users, groups=groups)

        if response.status == 200:
            return True
        raise NSWebDavHTTPError(response.status, await response.read())

    async def get_history(self, folder, cursor=None, auth_tuple=None, client=None):
        response = await self._perform_operation_request("delta", auth_tuple, client,
                                                         folder=folder, cursor=cursor)
        if response.status == 200:
            return parse_history(await response.read())
        raise NSWebDavHTTPError(response.status, await response.read())

    async def get_latest_cursor(self, folder, auth_tuple=None, client=None):
        response = await self._perform_operation_request("latestDeltaCursor", auth_tuple, client,
                                                         folder=folder)
        if response.status == 200:
            return parse_latest_cursor(await response.read())
        raise NSWebDavHTTPError(response.status, await response.read())

    async def cp_shared_object(self, path, url, password=None, auth_tuple=None, client=None):
        response = await self._perform_operation_request("submitCopyPubObject", auth_tuple, client,
                                                         path=path, url=url, password=password)

        if response.status == 201:
            return parse_cp_shared_object(await response.read())
        raise NSWebDavHTTPError(response.status, await response.read())

    async def poll_cp(self, copy_uuid, auth_tuple=None, client=None):
        response = await self. _perform_operation_request("pollCopyPubObject", auth_tuple, client,
                                                          copy_uuid=copy_uuid)

        if response.status == 201:
            return "In process"
        elif response.status == 200:
            return "Complete"
        raise NSWebDavHTTPError(response.status, await response.read())

    async def search(self, keywords, path, auth_tuple=None, client=None):
        if path:
            path = self._dav_url + path
        response = await self._perform_operation_request("search", auth_tuple, client,
                                                         keywords=keywords, path=path)
        if response.status == 207:
            return parse_search(await response.read())
        raise NSWebDavHTTPError(response.status, await response.read())

    async def get_content_url(self, path, platform="desktop", link_type="download", auth_tuple=None, client=None):
        path = self._dav_url + path
        response = await self._perform_operation_request("directContentUrl", auth_tuple, client,
                                                         path=path, platform=platform, link_type=link_type)
        if response.status == 200:
            return parse_content_url(await response.read())
        raise NSWebDavHTTPError(response.status, await response.read())

    async def get_shared_content_url(self, link, platform="desktop", link_type="download", relative_path=None,
                                     password=None, auth_tuple=None, client=None):
        response = await self._perform_operation_request("directPubContentUrl", auth_tuple, client,
                                                         link=link, platform=platform, link_type=link_type,
                                                         relative_path=relative_path, password=password)
        if response.status == 200:
            return parse_content_url(await response.read())
        raise NSWebDavHTTPError(response.status, await response.read())

    async def get_user_info(self, auth_tuple=None, client=None):
        auth_tuple = self._get_auth_tuple(auth_tuple)
        client = self._get_client(client)

        root_url = urljoin(self._base_url, self._operation_url)
        url = root_url + "/getUserInfo"
        response = await client.request("GET", url, auth=auth_tuple)

        if response.status == 200:
            return parse_user_info(await response.read())
        raise NSWebDavHTTPError(response.status, await response.read())

    async def update_team_info(self, name, auth_tuple=None, client=None):
        response = await self._perform_operation_request("updateTeamInfo", auth_tuple, client, name=name)

        if response.status == 204:
            return True
        raise NSWebDavHTTPError(response.status, await response.read())

    async def get_team_members(self, auth_tuple=None, client=None):
        auth_tuple = self._get_auth_tuple(auth_tuple)
        client = self._get_client(client)

        root_url = urljoin(self._base_url, self._operation_url)
        url = root_url + "/getTeamMembers"
        response = await client.request("GET", url, auth=auth_tuple)

        if response.status == 200:
            return parse_team_members(await response.read())
        raise NSWebDavHTTPError(response.status, await response.read())

    async def create_team_member(self, users, auth_tuple=None, client=None):
        response = await self._perform_operation_request("createEtpTeamMember", auth_tuple, client,
                                                         users=users)
        if response.status == 204:
            return True
        raise NSWebDavHTTPError(response.status, await response.read())

    async def update_team_member_storage_quota(self, user_name, storage_quota, auth_tuple=None, client=None):
        response = await self._perform_operation_request("updateTeamMemberStorageQuota", auth_tuple, client,
                                                         user_name=user_name, storage_quota=storage_quota)
        if response.status == 204:
            return True
        raise NSWebDavHTTPError(response.status, await response.read())

    async def get_team_member_info(self, user_name, auth_tuple=None, client=None):
        response = await self._perform_operation_request("getTeamMemberInfo", auth_tuple, client,
                                                         user_name=user_name)
        if response.status == 200:
            return parse_team_member_info(await response.read())
        raise NSWebDavHTTPError(response.status, await response.read())

    async def remove_team_member(self, user_name, folder_receipt, clean_perms=False, auth_tuple=None, client=None):
        response = await self._perform_operation_request("removeTeamMember", auth_tuple, client,
                                                         user_name=user_name, folder_receipt=folder_receipt,
                                                         clean_perms=clean_perms)
        if response.status == 204:
            return True
        raise NSWebDavHTTPError(response.status, await response.read())

    async def get_group_members(self, group_id, auth_tuple=None, client=None):
        response = await self._perform_operation_request("getGroupMembers", auth_tuple, client,
                                                         group_id=group_id)
        if response.status == 200:
            return parse_group_members(await response.read())
        raise NSWebDavHTTPError(response.status, await response.read())

    async def create_group(self, parent_group_id, name, admins, users=None, auth_tuple=None, client=None):
        response = await self._perform_operation_request("createGroup", auth_tuple, client,
                                                         parent_group_id=parent_group_id, name=name, admins=admins,
                                                         users=users)
        if response.status == 200:
            return parse_created_group(await response.read())
        raise NSWebDavHTTPError(response.status, await response.read())

    async def add_member_to_group(self, group_id, users, auth_tuple=None, client=None):
        response = await self._perform_operation_request("addMemberToGroup", auth_tuple, client,
                                                         group_id=group_id, users=users)
        if response.status == 204:
            return True
        raise NSWebDavHTTPError(response.status, await response.read())

    async def remove_member_from_group(self, group_id, users=None, subgroups=None, auth_tuple=None, client=None):
        response = await self._perform_operation_request("removeMemberFromGroup", auth_tuple, client,
                                                         group_id=group_id, users=users, subgroups=subgroups)
        if response.status == 204:
            return True
        raise NSWebDavHTTPError(response.status, await response.read())

    async def dismiss_team(self, auth_tuple=None, client=None):
        auth_tuple = self._get_auth_tuple(auth_tuple)
        client = self._get_client(client)

        root_url = urljoin(self._base_url, self._operation_url)
        url = root_url + "/dismissTeam"
        response = await client.request("POST", url, auth=auth_tuple)

        if response.status == 204:
            return True
        raise NSWebDavHTTPError(response.status, await response.read())

    async def update_team_member_status(self, users, auth_tuple=None, client=None):
        response = await self._perform_operation_request("updateTeamMemberStatus", auth_tuple, client,
                                                         users=users)
        if response.status == 204:
            return True
        raise NSWebDavHTTPError(response.status, await response.read())

    async def query_audit_logs(self, time_start, time_end, user_name=None, op_type=None, file_name=None,
                               auth_tuple=None, client=None):
        response = await self._perform_operation_request("queryAuditLogs", auth_tuple, client,
                                                         time_start=time_start, time_end=time_end, user_name=user_name,
                                                         op_type=op_type, file_name=file_name)
        if response.status == 200:
            return parse_audit_logs(await response.read())
        raise NSWebDavHTTPError(response.status, await response.read())
