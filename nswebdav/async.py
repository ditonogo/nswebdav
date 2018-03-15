from urllib.parse import urljoin, unquote

import aiohttp
from lxml import etree

from nswebdav.base import NutstoreDavBase, ItemList, History, User


class AsyncNutstoreDav(NutstoreDavBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = None
        self._auth_tuple = None

    def config(self, client=None, auth_tuple=None, **kwargs):
        """
        Config global :code:`client` or :code:`auth_tuple`.

        :code:`kwargs` will be passed to :meth:`nswebdav.base.NutstoreDavBase.config`.

        :param client: Should be an :code:`aiohttp.ClientSession`.
        :param auth_tuple: Should be a tuple like :code:`(user_name, access_token)`
        """
        super().config(**kwargs)
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
        path = self._dav_url + path
        response = await self._perform_operation_request("pubObject", auth_tuple, client,
                                                         path=path, users=users, groups=groups,
                                                         downloadable=downloadable)

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
        path = self._dav_url + path
        response = await self._perform_operation_request("getSandboxAcl", auth_tuple, client,
                                                         path=path)

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
                if user is not None:
                    results["users"][user.text] = perm.text
                else:
                    group = acl.find("s:group", t.nsmap)
                    results["groups"][group.text] = perm.text
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
        path = self._dav_url + path
        response = await self._perform_operation_request("updateSandboxAcl", auth_tuple, client,
                                                         path=path, users=users, groups=groups)

        if response.status == 200:
            return True
        return False

    async def get_history(self, folder, cursor=None, auth_tuple=None, client=None):
        """
        Coroutine.

        Get the history of given top folder.

        :param folder: The top folder.
        :param cursor: The cursor of history in int. Will return the histories after cursor.
        :param auth_tuple: The auth_tuple overriding global config.
        :param client: The client overriding global config.
        :return: :class:`nswebdav.base.History` or :code:`False`.
        """
        response = await self._perform_operation_request("delta", auth_tuple, client,
                                                         folder=folder, cursor=cursor)
        if response.status == 200:
            return History(await response.read())
        return False

    async def get_latest_cursor(self, folder, auth_tuple=None, client=None):
        """
        Coroutine.

        Get the latest history cursor.

        :param folder: The top folder.
        :param auth_tuple: The auth_tuple overriding global config.
        :param client: The client overriding global config.
        :return: cursor in :code:`int`.
        """
        response = await self._perform_operation_request("latestDeltaCursor", auth_tuple, client,
                                                         folder=folder)
        if response.status == 200:
            t = etree.fromstring(await response.read())
            return int(t.find("s:cursor", t.nsmap).text, 16)
        return False

    async def cp_shared_object(self, path, url, password=None, auth_tuple=None, client=None):
        """
        Coroutine.

        Submit background copying a shared object to given path.

        :param path: The absolute path of object such as :code:`/path/to/directory/object`
        :param url: The url of shared object.
        :param password: The password of this shared object, ignore if there isn't password.
        :param auth_tuple: The auth_tuple overriding global config.
        :param client: The client overriding global config.
        :return: The uuid of this copy operation, used to query operation status later. Or :code:`False`.
        """
        response = await self._perform_operation_request("submitCopyPubObject", auth_tuple, client,
                                                         path=path, url=url, password=password)

        if response.status == 201:
            t = etree.fromstring(await response.read())
            return t.find("s:copy_uuid", t.nsmap).text
        return False

    async def poll_cp(self, copy_uuid, auth_tuple=None, client=None):
        """
        Coroutine.

        Query the state of background copy operation.

        :param copy_uuid: The uuid returned from :meth:`.cp_shared_object`.
        :param auth_tuple: The auth_tuple overriding global config.
        :param client: The client overriding global config.
        :return: "In process" or "Complete" if success else :code:`False`.
        """
        response = await self. _perform_operation_request("pollCopyPubObject", auth_tuple, client,
                                                          copy_uuid=copy_uuid)

        if response.status == 201:
            return "In process"
        elif response.status == 200:
            return "Complete"
        return False

    async def search(self, keywords, path, auth_tuple=None, client=None):
        """
        Coroutine.

        Use keywords to search files.

        :param keywords: A list of keywords in str. Each keyword should be at least two length.
        :param path: The absolute path to search. It can be an empty string to search every place.
        :param auth_tuple: The auth_tuple overriding global config.
        :param client: The client overriding global config.
        :return: :class:`nswebdav.base.ItemList` or :code:`False`.
        """
        if path:
            path = self._dav_url + path
        response = await self._perform_operation_request("search", auth_tuple, client,
                                                         keywords=keywords, path=path)
        if response.status == 207:
            return ItemList(await response.read(), False)
        return False

    async def get_content_url(self, path, platform="desktop", link_type="download", auth_tuple=None, client=None):
        """
        Coroutine.

        Get url of given object.

        :param path: The absolute path of object such as :code:`/path/to/directory/object`
        :param platform: The platform type of returned object, "desktop" or "mobile".
        :param link_type: The link type of returned object, "download" or "preview".
        :param auth_tuple: The auth_tuple overriding global config.
        :param client: The client overriding global config.
        :return: url of object or :code:`False`.
        """
        path = self._dav_url + path
        response = await self._perform_operation_request("directContentUrl", auth_tuple, client,
                                                         path=path, platform=platform, link_type=link_type)
        if response.status == 200:
            t = etree.fromstring(await response.read())
            href = unquote(t.find("s:href", t.nsmap).text)
            return href
        return False

    async def get_shared_content_url(self, link, platform="desktop", link_type="download", relative_path=None,
                                     password=None, auth_tuple=None, client=None):
        """
        Coroutine.

        Get url of given shared object.

        :param link: The share link of object.
        :param platform: The platform type of returned page, "desktop" or "mobile".
        :param link_type: The link type of returned page, "download" or "preview".
        :param relative_path: The relative path of given object. For example, given a directory contains "A.txt"
                              and "b.txt", relative path as :code:`/A.txt` will get the url of "A.txt".
        :param password: The password of this shared object, ignore if there isn't password.
        :param auth_tuple: The auth_tuple overriding global config.
        :param client: The client overriding global config.
        :return: url of object or :code:`False`.
        """
        response = await self._perform_operation_request("directPubContentUrl", auth_tuple, client,
                                                         link=link, platform=platform, link_type=link_type,
                                                         relative_path=relative_path, password=password)
        if response.status == 200:
            t = etree.fromstring(await response.read())
            href = unquote(t.find("s:href", t.nsmap).text)
            return href
        return False

    async def get_user_info(self, auth_tuple=None, client=None):
        """
        Coroutine.

        Get user's information.

        :param auth_tuple: The auth_tuple overriding global config.
        :param client: The client overriding global config.
        :return: :class:`nswebdav.base.User` or :code:`False`.
        """
        auth_tuple = self._get_auth_tuple(auth_tuple)
        client = self._get_client(client)

        root_url = urljoin(self._base_url, self._operation_url)
        url = root_url + "/getUserInfo"
        response = await client.request("GET", url, auth=auth_tuple)

        if response.status == 200:
            return User(await response.read())
        return False
