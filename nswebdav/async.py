from lxml import etree
from urllib.parse import urljoin

import aiohttp

from nswebdav.base import NutstoreDavBase, ItemList, render_pubObject, render_getSandboxAcl


class AsyncNutstoreDav(NutstoreDavBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = None
        self._auth_tuple = None

    def config(self, session=None, auth_tuple=None):
        if session:
            self._session = session
        if auth_tuple:
            self._auth_tuple = auth_tuple

    def _get_auth_tuple(self, auth_tuple):
        return aiohttp.BasicAuth(*auth_tuple) if auth_tuple else self._auth_tuple

    def _get_session(self, session):
        return session or self._session

    async def ls(self, path, auth_tuple=None, session=None):
        auth_tuple = self._get_auth_tuple(auth_tuple)
        session = self._get_session(session)

        root_url = urljoin(self._base_url, self._dav_url)
        url = root_url + path

        response = await session.request("PROPFIND", url, auth=auth_tuple)

        if response.status == 207:
            return ItemList(await response.read())
        return False

    async def mkdir(self, path, auth_tuple=None, session=None):
        auth_tuple = self._get_auth_tuple(auth_tuple)
        session = self._get_session(session)

        root_url = urljoin(self._base_url, self._dav_url)
        url = root_url + path

        response = await session.request("MKCOL", url, auth=auth_tuple)

        if response.status == 201:
            return True
        return False

    async def upload(self, content, path, auth_tuple=None, session=None):
        auth_tuple = self._get_auth_tuple(auth_tuple)
        session = self._get_session(session)

        root_url = urljoin(self._base_url, self._dav_url)
        url = root_url + path

        response = await session.request("PUT", url, data=content, auth=auth_tuple)

        if response.status == 201:
            return "Upload"
        elif response.status == 204:
            return "Overwrite"
        return False

    async def download(self, path, auth_tuple=None, session=None):
        auth_tuple = self._get_auth_tuple(auth_tuple)
        session = self._get_session(session)

        root_url = urljoin(self._base_url, self._dav_url)
        url = root_url + path

        response = await session.request("GET", url, auth=auth_tuple)

        if response.status == 200:
            return await response.read()
        return None

    async def mv(self, from_path, to_path, auth_tuple=None, session=None):
        auth_tuple = self._get_auth_tuple(auth_tuple)
        session = self._get_session(session)

        root_url = urljoin(self._base_url, self._dav_url)
        from_url = root_url + from_path
        to_url = root_url + to_path

        headers = {
            "Destination": to_url
        }

        response = await session.request("MOVE", from_url, headers=headers, auth=auth_tuple)

        if response.status == 201:
            return True
        return False

    async def cp(self, from_path, to_path, auth_tuple=None, session=None):
        auth_tuple = self._get_auth_tuple(auth_tuple)
        session = self._get_session(session)

        root_url = urljoin(self._base_url, self._dav_url)
        from_url = root_url + from_path
        to_url = root_url + to_path

        headers = {
            "Destination": to_url
        }

        response = await session.request("COPY", from_url, headers=headers, auth=auth_tuple)

        if response.status == 201:
            return True
        return False

    async def rm(self, path, auth_tuple=None, session=None):
        auth_tuple = self._get_auth_tuple(auth_tuple)
        session = self._get_session(session)

        root_url = urljoin(self._base_url, self._dav_url)
        url = root_url + path

        response = await session.request("DELETE", url, auth=auth_tuple)

        if response.status == 204:
            return True
        return False

    async def share(self, path, users=None, groups=None, downloadable=True, auth_tuple=None, session=None):
        auth_tuple = self._get_auth_tuple(auth_tuple)
        session = self._get_session(session)

        root_url = urljoin(self._base_url, self._operation_url)
        url = root_url + "/pubObject"

        path = self._dav_url + path

        xml = render_pubObject(path, users, groups, downloadable)

        response = await session.request("POST", url, data=xml, auth_tuple=auth_tuple)

        if response.status == 200:
            t = etree.fromstring(await response.read())
            share_link = t.find("s:sharelink", t.nsmap).text.strip()
            return share_link
        return False

    async def get_acl(self, path, auth_tuple=None, session=None):
        auth_tuple = self._get_auth_tuple(auth_tuple)
        session = self._get_session(session)

        root_url = urljoin(self._base_url, self._operation_url)
        url = root_url + "/getSandboxAcl"

        path = self._dav_url + path

        xml = render_getSandboxAcl(path)

        response = await session.request("POST", url, data=xml, auth_tuple=auth_tuple)

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
