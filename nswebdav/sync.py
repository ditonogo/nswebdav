from urllib.parse import urljoin, unquote

import requests
from lxml import etree

from nswebdav.base import NutstoreDavBase, ItemList, History, User
from nswebdav.exceptions import NSWebDavHTTPError


class NutstoreDav(NutstoreDavBase):
    """
    An implementation which supports sync usage.

    By default, ``auth_tuple`` is :obj:`None`, you need to config it by calling :meth:`.config`
    or by passing a tuple in every methods.

    There is a default client :class:`requests.Session`, but you can still overwrite it by calling :meth:`.config`
    or passing a custom one in every methods.
    """
    def __init__(self, base_url="https://dav.jianguoyun.com", dav_url="/dav", operation_url="/nsdav"):
        super().__init__(base_url, dav_url, operation_url)
        self._client = requests.Session()

    def _get_auth_tuple(self, auth_tuple=None):
        return auth_tuple or self._auth_tuple

    def ls(self, path, auth_tuple=None, client=None):
        """
        List the items under given path.

        Parameters
        ----------
        path : str
            The absolute path of object such as ``/path/to/directory/object``
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`requests.Session`
            The client overriding global config.

        Returns
        -------
        :class:`.ItemList`
            A list-like object contains items.

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        response = self._perform_dav_request("PROPFIND", auth_tuple, client, path=path)

        if response.status_code == 207:
            return ItemList(response.content)
        raise NSWebDavHTTPError(response.status_code, response.content)

    def mkdir(self, path, auth_tuple=None, client=None):
        """
        Create a directory to given path.

        Parameters
        ----------
        path : str
            The absolute path of directory such as ``/path/to/directory``
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`requests.Session`
            The client overriding global config.

        Returns
        -------
        bool
            Return :obj:`True` or raise exception.

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        response = self._perform_dav_request("MKCOL", auth_tuple, client, path=path)

        if response.status_code == 201:
            return True
        raise NSWebDavHTTPError(response.status_code, response.content)

    def upload(self, content, path, auth_tuple=None, client=None):
        """
        Upload an object to given path.

        Parameters
        ----------
        content : bytes
            The bytes of uploaded object.
        path : str
            The absolute path of directory such as ``/path/to/directory``
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`requests.Session`
            The client overriding global config.

        Returns
        -------
        str
            "Upload" or "Overwrite".

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        response = self._perform_dav_request("PUT", auth_tuple, client, path=path, data=content)

        if response.status_code == 201:
            return "Upload"
        elif response.status_code == 204:
            return "Overwrite"
        raise NSWebDavHTTPError(response.status_code, response.content)

    def download(self, path, auth_tuple=None, client=None):
        """
        Download an object from given path.

        Parameters
        ----------
        path : str
            The absolute path of directory such as ``/path/to/directory``
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`requests.Session`
            The client overriding global config.

        Returns
        -------
        bytes
            The bytes of object.

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        response = self._perform_dav_request("GET", auth_tuple, client, path=path)

        if response.status_code == 200:
            return response.content
        raise NSWebDavHTTPError(response.status_code, response.content)

    def mv(self, from_path, to_path, auth_tuple=None, client=None):
        """
        Move or rename a file or directory.

        Parameters
        ----------
        from_path : str
            The original path of object.
        to_path : str
            The destination path of object.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`requests.Session`
            The client overriding global config.

        Returns
        -------
        bool
            Return :obj:`True` or raise exception.

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        response = self._perform_dav_request("MOVE", auth_tuple, client, from_path=from_path, to_path=to_path)

        if response.status_code == 201:
            return True
        raise NSWebDavHTTPError(response.status_code, response.content)

    def cp(self, from_path, to_path, auth_tuple=None, client=None):
        """
        Copy a file or directory.

        Parameters
        ----------
        from_path : str
            The original path of object.
        to_path : str
            The destination path of object.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`requests.Session`
            The client overriding global config.

        Returns
        -------
        bool
            Return :obj:`True` or raise exception.

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        response = self._perform_dav_request("COPY", auth_tuple, client, from_path=from_path, to_path=to_path)

        if response.status_code == 201:
            return True
        raise NSWebDavHTTPError(response.status_code, response.content)

    def rm(self, path, auth_tuple=None, client=None):
        """
        Remove a file or directory.

        Parameters
        ----------
        path : str
            The absolute path of directory such as ``/path/to/directory``
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`requests.Session`
            The client overriding global config.

        Returns
        -------
        bool
            Return :obj:`True` or raise exception.

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        response = self._perform_dav_request("DELETE", auth_tuple, client, path=path)

        if response.status_code == 204:
            return True
        raise NSWebDavHTTPError(response.status_code, response.content)

    def share(self, path, users=None, groups=None, downloadable=True, auth_tuple=None, client=None):
        """
        Get the share link of given object.

        Parameters
        ----------
        path : str
            The absolute path of directory such as ``/path/to/directory``
        users : list
            A list contains which users to share as :obj:`str`. :obj:`None` means everyone.
        groups : list
            A list contains which groups to share as :obj:`str` or :obj:`int`. :obj:`None` means every group.
        downloadable : bool
            If it can be downloaded.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`requests.Session`
            The client overriding global config.

        Returns
        -------
        str
            Share link.

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        path = self._dav_url + path
        response = self._perform_operation_request("pubObject", auth_tuple, client,
                                                   path=path, users=users, groups=groups,
                                                   downloadable=downloadable)

        if response.status_code == 200:
            t = etree.fromstring(response.content)
            share_link = t.find("s:sharelink", t.nsmap).text.strip()
            return share_link
        raise NSWebDavHTTPError(response.status_code, response.content)

    def get_acl(self, path, auth_tuple=None, client=None):
        """
        Get the privilege configuration of given object.

        Parameters
        ----------
        path : str
            The absolute path of directory such as ``/path/to/directory``
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`requests.Session`
            The client overriding global config.

        Returns
        -------
        dict
            Contains two :obj:`dict` "users" and "groups".

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        path = self._dav_url + path
        response = self._perform_operation_request("getSandboxAcl", auth_tuple, client,
                                                   path=path)

        if response.status_code == 200:
            t = etree.fromstring(response.content)
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
        raise NSWebDavHTTPError(response.status_code, response.content)

    def set_acl(self, path, users=None, groups=None, auth_tuple=None, client=None):
        """
        Set the privilege configuration of given object.

        Parameters
        ----------
        path : str
            The absolute path of directory such as ``/path/to/directory``
        users : list
            A list of tuples. Each tuple contains :code:`(user_name, perm)`.
        groups : list
            A list of tuples. Each tuple contains :code:`(group_id, perm)`.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`requests.Session`
            The client overriding global config.

        Returns
        -------
        bool
            Return :obj:`True` or raise exception.

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        path = self._dav_url + path
        response = self._perform_operation_request("updateSandboxAcl", auth_tuple, client,
                                                   path=path, users=users, groups=groups)

        if response.status_code == 200:
            return True
        raise NSWebDavHTTPError(response.status_code, response.content)

    def get_history(self, folder, cursor=None, auth_tuple=None, client=None):
        """
        Get the history of given top folder.

        Parameters
        ----------
        folder : str
            The top folder.
        cursor : int
            The cursor of history in :obj:`int`. Will return the histories after cursor.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`requests.Session`
            The client overriding global config.

        Returns
        -------
        :class:`.History`
            A list-like object contains history item.

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        response = self._perform_operation_request("delta", auth_tuple, client,
                                                   folder=folder, cursor=cursor)
        if response.status_code == 200:
            return History(response.content)
        raise NSWebDavHTTPError(response.status_code, response.content)

    def get_latest_cursor(self, folder, auth_tuple=None, client=None):
        """
        Get the latest history cursor.

        Parameters
        ----------
        folder : str
            The top folder.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`requests.Session`
            The client overriding global config.

        Returns
        -------
        int
            Latest cursor.

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        response = self._perform_operation_request("latestDeltaCursor", auth_tuple, client,
                                                   folder=folder)
        if response.status_code == 200:
            t = etree.fromstring(response.content)
            return int(t.find("s:cursor", t.nsmap).text, 16)
        raise NSWebDavHTTPError(response.status_code, response.content)

    def cp_shared_object(self, path, url, password=None, auth_tuple=None, client=None):
        """
        Submit copying a shared object to given path.

        Parameters
        ----------
        path : str
            The absolute path of object such as :code:`/path/to/directory/object`.
        url : str
            The url of shared object.
        password : str
            The password of this shared object, ignore if there isn't password.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`requests.Session`
            The client overriding global config.

        Returns
        -------
        str
            The uuid of this copy operation, used to query operation status later.

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        response = self._perform_operation_request("submitCopyPubObject", auth_tuple, client,
                                                   path=path, url=url, password=password)

        if response.status_code == 201:
            t = etree.fromstring(response.content)
            return t.find("s:copy_uuid", t.nsmap).text
        raise NSWebDavHTTPError(response.status_code, response.content)

    def poll_cp(self, copy_uuid, auth_tuple=None, client=None):
        """
        Query the state of background copy operation.

        Parameters
        ----------
        copy_uuid : str
            The uuid returned from :meth:`.cp_shared_object`.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`requests.Session`
            The client overriding global config.

        Returns
        -------
        str
            "In process" or "Complete".

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        response = self._perform_operation_request("pollCopyPubObject", auth_tuple, client,
                                                   copy_uuid=copy_uuid)

        if response.status_code == 201:
            return "In process"
        elif response.status_code == 200:
            return "Complete"
        raise NSWebDavHTTPError(response.status_code, response.content)

    def search(self, keywords, path, auth_tuple=None, client=None):
        """
        Use keywords to search files.

        Parameters
        ----------
        keywords : list
            A list of keywords in str. Each keyword should be at least two length.
        path : str
            The absolute path to search. It can be an empty string to search every place.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`requests.Session`
            The client overriding global config.

        Returns
        -------
        :class:`.ItemList`
            A list-like object contains items.

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        if path:
            path = self._dav_url + path
        response = self._perform_operation_request("search", auth_tuple, client,
                                                   keywords=keywords, path=path)
        if response.status_code == 207:
            return ItemList(response.content, False)
        raise NSWebDavHTTPError(response.status_code, response.content)

    def get_content_url(self, path, platform="desktop", link_type="download", auth_tuple=None, client=None):
        """
        Get url of given object.

        Parameters
        ----------
        path : str
            The absolute path of object such as :code:`/path/to/directory/object`.
        platform : str
            The platform type of returned object, "desktop" or "mobile".
        link_type : str
            The link type of returned object, "download" or "preview".
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`requests.Session`
            The client overriding global config.

        Returns
        -------
        str
            url of object.

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        path = self._dav_url + path
        response = self._perform_operation_request("directContentUrl", auth_tuple, client,
                                                   path=path, platform=platform, link_type=link_type)
        if response.status_code == 200:
            t = etree.fromstring(response.content)
            href = unquote(t.find("s:href", t.nsmap).text)
            return href
        raise NSWebDavHTTPError(response.status_code, response.content)

    def get_shared_content_url(self, link, platform="desktop", link_type="download", relative_path=None,
                               password=None, auth_tuple=None, client=None):
        """
        Get url of given shared object.

        Parameters
        ----------
        link : str
            The share link of object.
        platform : str
            The platform type of returned object, "desktop" or "mobile".
        link_type : str
            The link type of returned object, "download" or "preview".
        relative_path : str
            The relative path of given object. For example, given a directory contains "A.txt" and "b.txt",
            relative path as ``/A.txt`` will get the url of "A.txt".
        password : str
            The password of this shared object, ignore if there isn't password.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`requests.Session`
            The client overriding global config.

        Returns
        -------
        str
            url of object.

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        response = self._perform_operation_request("directPubContentUrl", auth_tuple, client,
                                                   link=link, platform=platform, link_type=link_type,
                                                   relative_path=relative_path, password=password)
        if response.status_code == 200:
            t = etree.fromstring(response.content)
            href = unquote(t.find("s:href", t.nsmap).text)
            return href
        raise NSWebDavHTTPError(response.status_code, response.content)

    def get_user_info(self, auth_tuple=None, client=None):
        """
        Get user's information.

        Parameters
        ----------
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`requests.Session`
            The client overriding global config.

        Returns
        -------
        :class:`.User`
            An object contains user's information.

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        auth_tuple = self._get_auth_tuple(auth_tuple)
        client = self._get_client(client)

        root_url = urljoin(self._base_url, self._operation_url)
        url = root_url + "/getUserInfo"
        response = client.request("GET", url, auth=auth_tuple)

        if response.status_code == 200:
            return User(response.content)
        raise NSWebDavHTTPError(response.status_code, response.content)
