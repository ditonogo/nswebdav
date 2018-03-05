from lxml import etree
from urllib.parse import urljoin

import aiohttp

from nswebdav.base import NutstoreDavBase, ItemList, render_pubObject, render_getSandboxAcl, render_updateSandboxAcl


class AsyncNutstoreDav(NutstoreDavBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = None
        self._auth_tuple = None

    def config(self, client=None, auth_tuple=None):
        """
        Config global :code:`client` or :code:`auth_tuple`.

        :param client: Should be an :code:`aiohttp.ClientSession`.
        :param auth_tuple: Should be a tuple like :code:`(user_name, access_token)`
        """
        if client:
            self._client = client
        if auth_tuple:
            self._auth_tuple = aiohttp.BasicAuth(*auth_tuple)

    def _get_auth_tuple(self, auth_tuple=None):
        return aiohttp.BasicAuth(*auth_tuple) if auth_tuple else self._auth_tuple

    def _get_client(self, client=None):
        return client or self._client

    async def ls(self, path, auth_tuple=None, client=None):
        """
        Coroutine.

        List the items under given path.

        :param path: The absolute path of object such as :code:`/path/to/directory/object`
        :param auth_tuple: The auth_tuple overriding global config.
        :param client: The client overriding global config.
        :return: :class:`nswebdav.base.ItemList` or :code:`False`.
        """
        response = await self._perform_dav_request("PROPFIND", auth_tuple, client, path=path)

        if response.status == 207:
            return ItemList(await response.read())
        return False

    async def mkdir(self, path, auth_tuple=None, client=None):
        """
        Coroutine.

        Create a directory to given path.

        :param path: The absolute path of directory such as :code:`/path/to/directory`
        :param auth_tuple: The auth_tuple overriding global config.
        :param client: The client overriding global config.
        :return: :code:`True` or :code:`False`.
        """
        response = await self._perform_dav_request("MKCOL", auth_tuple, client, path=path)

        if response.status == 201:
            return True
        return False

    async def upload(self, content, path, auth_tuple=None, client=None):
        """
        Coroutine.

        Upload an object to given path.

        :param content: The bytes of uploaded object.
        :param path: The absolute path of uploaded object such as :code:`/path/to/directory/object`
        :param auth_tuple: The auth_tuple overriding global config.
        :param client: The client overriding global config.
        :return: "Upload" or "Overwrite" if success else :code:`False`.
        """
        response = await self._perform_dav_request("PUT", auth_tuple, client, path=path, data=content)

        if response.status == 201:
            return "Upload"
        elif response.status == 204:
            return "Overwrite"
        return False

    async def download(self, path, auth_tuple=None, client=None):
        """
        Coroutine.

        Download an object from given path.

        :param path: The absolute path of object such as :code:`/path/to/directory/object`
        :param auth_tuple: The auth_tuple overriding global config.
        :param client: The client overriding global config.
        :return: The bytes of object or :code:`None`.
        """
        response = await self._perform_dav_request("GET", auth_tuple, client, path=path)

        if response.status == 200:
            return await response.read()
        return None

    async def mv(self, from_path, to_path, auth_tuple=None, client=None):
        """
        Coroutine.

        Move or rename a file or directory.

        :param from_path: The original path of object.
        :param to_path: The destination path of object.
        :param auth_tuple: The auth_tuple overriding global config.
        :param client: The client overriding global config.
        :return: :code:`True` or :code:`False`.
        """
        response = await self._perform_dav_request("MOVE", auth_tuple, client, from_path=from_path, to_path=to_path)

        if response.status == 201:
            return True
        return False

    async def cp(self, from_path, to_path, auth_tuple=None, client=None):
        """
        Coroutine.

        Copy a file or directory.

        :param from_path: The original path of object.
        :param to_path: The destination path of object.
        :param auth_tuple: The auth_tuple overriding global config.
        :param client: The client overriding global config.
        :return: :code:`True` or :code:`False`.
        """
        response = await self._perform_dav_request("COPY", auth_tuple, client, from_path=from_path, to_path=to_path)

        if response.status == 201:
            return True
        return False

    async def rm(self, path, auth_tuple=None, client=None):
        """
        Coroutine.

        Remove a file or directory.

        :param path: The absolute path of object such as :code:`/path/to/directory/object`
        :param auth_tuple: The auth_tuple overriding global config.
        :param client: The client overriding global config.
        :return: :code:`True` or :code:`False`.
        """
        response = await self._perform_dav_request("DELETE", auth_tuple, client, path=path)

        if response.status == 204:
            return True
        return False

    async def share(self, path, users=None, groups=None, downloadable=True, auth_tuple=None, client=None):
        """
        Coroutine.

        Get the share link of given object.

        :param path: The absolute path of object such as :code:`/path/to/directory/object`
        :param users: A list contains which users to share as :code:`str`. :code:`None` means everyone.
        :param groups: A list contains which groups to share as :code:`str` or :code:`int`. :code:`None`
                       means every group.
        :param downloadable: If it can be downloaded.
        :param auth_tuple: The auth_tuple overriding global config.
        :param client: The client overriding global config.
        :return: share link as :code:`str` or :code:`False`.
        """
        auth_tuple = self._get_auth_tuple(auth_tuple)
        client = self._get_client(client)

        root_url = urljoin(self._base_url, self._operation_url)
        url = root_url + "/pubObject"

        path = self._dav_url + path

        xml = render_pubObject(path, users, groups, downloadable)

        response = await client.request("POST", url, data=xml, auth_tuple=auth_tuple)

        if response.status == 200:
            t = etree.fromstring(await response.read())
            share_link = t.find("s:sharelink", t.nsmap).text.strip()
            return share_link
        return False

    async def get_acl(self, path, auth_tuple=None, client=None):
        """
        Coroutine.

        Get the privilege configuration of given object.

        :param path: The absolute path of object such as :code:`/path/to/directory/object`
        :param auth_tuple: The auth_tuple overriding global config.
        :param client: The client overriding global config.
        :return: A :code:`dict` contains two :code:`dict` "users" and "groups".
        """
        auth_tuple = self._get_auth_tuple(auth_tuple)
        client = self._get_client(client)

        root_url = urljoin(self._base_url, self._operation_url)
        url = root_url + "/getSandboxAcl"

        path = self._dav_url + path

        xml = render_getSandboxAcl(path)

        response = await client.request("POST", url, data=xml, auth_tuple=auth_tuple)

        if response.status == 200:
            t = etree.fromstring(await response.read())
            results = {
                "users": {},
                "groups": {}
            }
            acls = t.findall("s:acl", t.nsmap)
            for acl in acls:
                user = acl.find("s:username", t.nsmap)
                perm = acl.find("s:perm", t.nsmap)
                if user:
                    results["users"][user] = perm
                else:
                    group = acl.find("s:group", t.nsmap)
                    results["groups"][group] = perm
            return results
        return False

    async def set_acl(self, path, users=None, groups=None, auth_tuple=None, client=None):
        """
        Coroutine.

        Set the privilege configuration of given object.

        :param path: The absolute path of object such as :code:`/path/to/directory/object`
        :param users: A list of tuples. Each tuple contains :code:`(user_name, perm)`.
        :param groups: A list of tuples. Each tuple contains :code:`(group_id, perm)`.
        :param auth_tuple: The auth_tuple overriding global config.
        :param client: The client overriding global config.
        :return: :code:`True` or :code:`False`.
        """
        auth_tuple = self._get_auth_tuple(auth_tuple)
        client = self._get_client(client)

        root_url = urljoin(self._base_url, self._operation_url)
        url = root_url + "/updateSandboxAcl"

        path = self._dav_url + path

        xml = render_updateSandboxAcl(path, users, groups)

        response = await client.request("POST", url, data=xml, auth_tuple=auth_tuple)

        if response.status == 200:
            return True
        return False
