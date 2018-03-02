from lxml import etree
from urllib.parse import urljoin

import requests

from nswebdav.base import NutstoreDavBase, ItemList, render_pubObject, render_getSandboxAcl


class NutstoreDav(NutstoreDavBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._auth_tuple = None

    def config(self, auth_tuple=None):
        """
        Config global :code:`auth_tuple`.

        :param auth_tuple: Should be a tuple like :code:`(user_name, access_token)`
        """
        if auth_tuple:
            self._auth_tuple = auth_tuple

    def _get_auth_tuple(self, auth_tuple):
        return auth_tuple or self._auth_tuple

    def ls(self, path, auth_tuple=None):
        """
        List the items under given path.

        :param path: The absolute path of object such as :code:`/path/to/directory/object`
        :param auth_tuple: The auth_tuple overriding global config.
        :return: :class:`nswebdav.base.ItemList` or :code:`False`.
        """
        auth_tuple = self._get_auth_tuple(auth_tuple)

        root_url = urljoin(self._base_url, self._dav_url)
        url = root_url + path

        response = requests.request("PROPFIND", url, auth=auth_tuple)

        if response.status_code == 207:
            return ItemList(response.content)
        return False

    def mkdir(self, path, auth_tuple=None):
        """
        Create a directory to given path.

        :param path: The absolute path of directory such as :code:`/path/to/directory`
        :param auth_tuple: The auth_tuple overriding global config.
        :return: :code:`True` or :code:`False`.
        """
        auth_tuple = self._get_auth_tuple(auth_tuple)

        root_url = urljoin(self._base_url, self._dav_url)
        url = root_url + path

        response = requests.request("MKCOL", url, auth=auth_tuple)

        if response.status_code == 201:
            return True
        return False

    def upload(self, content, path, auth_tuple=None):
        """
        Upload an object to given path.

        :param content: The bytes of uploaded object.
        :param path: The absolute path of uploaded object such as :code:`/path/to/directory/object`
        :param auth_tuple: The auth_tuple overriding global config.
        :return: "Upload" or "Overwrite" if success else :code:`False`.
        """
        auth_tuple = self._get_auth_tuple(auth_tuple)

        root_url = urljoin(self._base_url, self._dav_url)
        url = root_url + path

        response = requests.request("PUT", url, data=content, auth=auth_tuple)

        if response.status_code == 201:
            return "Upload"
        elif response.status_code == 204:
            return "Overwrite"
        return False

    def download(self, path, auth_tuple=None):
        """
        Download an object from given path.

        :param path: The absolute path of object such as :code:`/path/to/directory/object`
        :param auth_tuple: The auth_tuple overriding global config.
        :return: The bytes of object or :code:`None`.
        """
        auth_tuple = self._get_auth_tuple(auth_tuple)

        root_url = urljoin(self._base_url, self._dav_url)
        url = root_url + path

        response = requests.request("GET", url, auth=auth_tuple)

        if response.status_code == 200:
            return response.content
        return None

    def mv(self, from_path, to_path, auth_tuple=None):
        """
        Move or rename a file or directory.

        :param from_path: The original path of object.
        :param to_path: The destination path of object.
        :param auth_tuple: The auth_tuple overriding global config.
        :return: :code:`True` or :code:`False`.
        """
        auth_tuple = self._get_auth_tuple(auth_tuple)

        root_url = urljoin(self._base_url, self._dav_url)
        from_url = root_url + from_path
        to_url = root_url + to_path

        headers = {
            "Destination": to_url
        }

        response = requests.request("MOVE", from_url, headers=headers, auth=auth_tuple)

        if response.status_code == 201:
            return True
        return False

    def cp(self, from_path, to_path, auth_tuple=None):
        """
        Copy a file or directory.

        :param from_path: The original path of object.
        :param to_path: The destination path of object.
        :param auth_tuple: The auth_tuple overriding global config.
        :return: :code:`True` or :code:`False`.
        """
        auth_tuple = self._get_auth_tuple(auth_tuple)

        root_url = urljoin(self._base_url, self._dav_url)
        from_url = root_url + from_path
        to_url = root_url + to_path

        headers = {
            "Destination": to_url
        }

        response = requests.request("COPY", from_url, headers=headers, auth=auth_tuple)

        if response.status_code == 201:
            return True
        return False

    def rm(self, path, auth_tuple=None):
        """
        Remove a file or directory.

        :param path: The absolute path of object such as :code:`/path/to/directory/object`
        :param auth_tuple: The auth_tuple overriding global config.
        :return: :code:`True` or :code:`False`.
        """
        auth_tuple = self._get_auth_tuple(auth_tuple)

        root_url = urljoin(self._base_url, self._dav_url)
        url = root_url + path

        response = requests.request("DELETE", url, auth=auth_tuple)

        if response.status_code == 204:
            return True
        return False

    def share(self, path, users=None, groups=None, downloadable=True, auth_tuple=None):
        """
        Get the share link of given object.

        :param path: The absolute path of object such as :code:`/path/to/directory/object`
        :param users: A list contains which users to share as :code:`str`. :code:`None` means everyone.
        :param groups: A list contains which groups to share as :code:`str` or :code:`int`. :code:`None`
                       means every group.
        :param downloadable: If it can be downloaded.
        :param auth_tuple: The auth_tuple overriding global config.
        :return: share link as :code:`str` or :code:`False`.
        """
        auth_tuple = self._get_auth_tuple(auth_tuple)

        root_url = urljoin(self._base_url, self._operation_url)
        url = root_url + "/pubObject"

        path = self._dav_url + path

        xml = render_pubObject(path, users, groups, downloadable)

        response = requests.request("POST", url, data=xml, auth_tuple=auth_tuple)

        if response.status_code == 200:
            t = etree.fromstring(response.content)
            share_link = t.find("s:sharelink", t.nsmap).text.strip()
            return share_link
        return False

    def get_acl(self, path, auth_tuple=None):
        """
        Get the privilege configuration of given object.

        :param path: The absolute path of object such as :code:`/path/to/directory/object`
        :param auth_tuple: The auth_tuple overriding global config.
        :return: A :code:`dict` contains two :code:`dict` "users" and "groups".
        """
        auth_tuple = self._get_auth_tuple(auth_tuple)

        root_url = urljoin(self._base_url, self._operation_url)
        url = root_url + "/getSandboxAcl"

        path = self._dav_url + path

        xml = render_getSandboxAcl(path)

        response = requests.request("POST", url, data=xml, auth_tuple=auth_tuple)

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
                if user:
                    results["users"][user] = perm
                else:
                    group = acl.find("s:group", t.nsmap)
                    results["groups"][group] = perm
            return results
        return False
