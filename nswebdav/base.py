from urllib.parse import urljoin, quote

from nswebdav.render import render_func


class NutstoreDavBase:
    """
    Base class for both sync subclass and async subclass

    Parameters
    ----------
    base_url : str
        The base url of nutstore website.
    dav_url : str
        The dav url of nutstore website, which is used to access files.
    operation_url: str
        The operation url of nutstore website, which is used to post operations.
    """

    def __init__(self, base_url, dav_url, operation_url):
        self._base_url = base_url
        self._operation_url = operation_url
        self._dav_url = dav_url
        self._client = None
        self._auth_tuple = None

    def config(self, client=None, auth_tuple=None, base_url=None, dav_url=None, operation_url=None):
        """
        Used to overwrite ``base_url``, ``dav_url`` or ``operation_url``.

        Or use custom ``client`` and config global ``auth_tuple``.

        Parameters
        ----------
        client : :class:`aiohttp.ClientSession` or :class:`requests.Session`
            A client used to send request.
            :class:`aiohttp.ClientSession` for async version,
            :class:`requests.Session` for sync version.
        auth_tuple : tuple
            Should be a tuple like ``(user_name, access_token)``
        base_url : str
            The base url of nutstore website.
        dav_url : str
            The dav url of nutstore website, which is used to access files.
        operation_url : str
            The operation url of nutstore website, which is used to post operations.
        """
        if client:
            self.close()
            self._client = client
        if auth_tuple:
            self._auth_tuple = auth_tuple
        if base_url:
            self._base_url = base_url
        if dav_url:
            self._dav_url = dav_url
        if operation_url:
            self._operation_url = operation_url

    def close(self):
        """
        Used to close underlying client.
        """
        raise NotImplementedError("Should be implemented in subclass.")

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
            destination = root_url + quote(to_path)

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
        return client or self._client

    def ls(self, path, auth_tuple=None, client=None):
        """
        List the items under given path.

        Parameters
        ----------
        path : str
            The absolute path of object such as ``/path/to/directory/object``
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
            The client overriding global config.

        Returns
        -------
        :obj:`list`
            A list contains :class:`.Entity` with the following values:

            ================ ============================ =========================================
            Key              Type                         Description
            ---------------- ---------------------------- -----------------------------------------
            href             str                          The relative url of this item.
            display_name     str                          The name of this item.
            is_dir           bool                         If this item is a directory.
            content_length   int                          The length of this item in bytes.
                                                          A directory always has 0 length.
            last_modified    float                        The last time this item was modified in Unix timestamp.
            owner            str                          The owner of this item.
            mime_type        str                          The mime type of this item.
            resource_perm    str                          the privilege of this item in str.
            readable         bool                         If have read privilege on this item.
            writable         bool                         If have write privilege on this item.
            full_privilege   bool                         If have full privilege on this item.
            read_acl         bool                         If have privilege to read the privilege
                                                          configuration of this item.
            write_acl        bool                         If have privilege to change the privilege
                                                          configuration of this item.
            ================ ============================ =========================================

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        raise NotImplementedError

    def mkdir(self, path, auth_tuple=None, client=None):
        """
        Create a directory to given path.

        Parameters
        ----------
        path : str
            The absolute path of object such as ``/path/to/directory/object``
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

    def upload(self, content, path, auth_tuple=None, client=None):
        """
        Upload an object to given path.

        Parameters
        ----------
        content : bytes
            The bytes of uploaded object.
        path : str
            The absolute path of object such as ``/path/to/directory/object``
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

    def download(self, path, auth_tuple=None, client=None):
        """
        Download an object from given path.

        Parameters
        ----------
        path : str
            The absolute path of object such as ``/path/to/directory/object``
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

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
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

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
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

    def rm(self, path, auth_tuple=None, client=None):
        """
        Remove a file or directory.

        Parameters
        ----------
        path : str
            The absolute path of object such as ``/path/to/directory/object``
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

    def share(self, path, users=None, groups=None, downloadable=True, auth_tuple=None, client=None):
        """
        Get the share link of given object.

        Parameters
        ----------
        path : str
            The absolute path of object such as ``/path/to/directory/object``
        users : list
            A list contains which users to share as :obj:`str`. :obj:`None` means everyone.
        groups : list
            A list contains which groups to share as :obj:`str` or :obj:`int`. :obj:`None` means every group.
        downloadable : bool
            If it can be downloaded.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

    def get_acl(self, path, auth_tuple=None, client=None):
        """
        Get the privilege configuration of given object.

        Parameters
        ----------
        path : str
            The absolute path of object such as ``/path/to/directory/object``
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
            The client overriding global config.

        Returns
        -------
        :class:`.Entity`
            Contains the following values:

            ========== ================== ==========================================================
            Key        Type               Description
            ---------- ------------------ ----------------------------------------------------------
            users      :class:`.Entity`   Contains the following values:

                                          ============================ ===== =============================
                                          Key                          Type  Description
                                          ---------------------------- ----- -----------------------------
                                          Depend on user's user name   str   The permission of this user.
                                          ============================ ===== =============================
            groups     :class:`.Entity`   Contains the following values:

                                          ========================== ====== =============================
                                          Key                        Type   Description
                                          -------------------------- ------ -----------------------------
                                          Depend on group's group id str    The permission of this group.
                                          ========================== ====== =============================
            ========== ================== ==========================================================

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        raise NotImplementedError

    def set_acl(self, path, users=None, groups=None, auth_tuple=None, client=None):
        """
        Set the privilege configuration of given object.

        Parameters
        ----------
        path : str
            The absolute path of object such as ``/path/to/directory/object``
        users : list
            A list of tuples. Each tuple contains ``(user_name, perm)``. ``perm`` should be one of :obj:`.PERM_MAP`.
        groups : list
            A list of tuples. Each tuple contains ``(group_id, perm)``. ``perm`` should be one of :obj:`.PERM_MAP`.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

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
        client : :class:`aiohttp.ClientSession`
            The client overriding global config.

        Returns
        -------
        :class:`.Entity`
            Contains the following values:

            ====================== ======================== =================================
            Key                    Type                     Description
            ---------------------- ------------------------ ---------------------------------
            reset                  bool                     If histories are continuous,
                                                            If is :obj:`False`,
                                                            all histories should be ignored and post again.
                                                            :obj:`False` may caused by
                                                            remote internal server error.
            cursor                 int                      Cursor of the last history.
            has_more               bool                     If histories are complete or there are more histories.
                                                            If :obj:`True`, you can call ``get_history``
                                                            with ``cursor`` to get the histories from ``cursor``.
            deltas                 list                     A list contains :class:`.Entity` with the following values:

                                                            ========== ====== ==================
                                                            Key        Type   Description
                                                            ---------- ------ ------------------
                                                            path       str    The path of this item.
                                                            size       int    The size of this item represented in
                                                                              bytes.
                                                            is_deleted bool   If this operation is deletion.
                                                            is_dir     bool   If this item is a directory.
                                                            modified   float  The date of this operation in Unix
                                                                              timestamp.
                                                            revision   int    Which revision of this operation.
                                                            ========== ====== ==================
            ====================== ======================== =================================

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        raise NotImplementedError

    def get_latest_cursor(self, folder, auth_tuple=None, client=None):
        """
        Get the latest history cursor.

        Parameters
        ----------
        folder : str
            The top folder.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

    def cp_shared_object(self, path, url, password=None, auth_tuple=None, client=None):
        """
        Submit background copying a shared object to given path.

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
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

    def poll_cp(self, copy_uuid, auth_tuple=None, client=None):
        """
        Query the state of background copy operation.

        Parameters
        ----------
        copy_uuid : str
            The uuid returned from :meth:`.cp_shared_object`.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

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
        client : :class:`aiohttp.ClientSession`
            The client overriding global config.

        Returns
        -------
        list
            A list contains :class:`.Entity` with the following values:

            ============= =================== ========================
            Key           Type                Description
            ------------- ------------------- ------------------------
            href          str                 The absolute path of
                                              this object.
            is_dir        bool                If this object is a directory.
            last_modified float               The last time this item was modified in Unix timestamp.
            mime_type     str                 The mime type of this object.
            owner         str                 The owner of this object.
            ============= =================== ========================

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        raise NotImplementedError

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
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

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
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

    def get_user_info(self, auth_tuple=None, client=None):
        """
        Get user's information.

        Parameters
        ----------
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
            The client overriding global config.

        Returns
        -------
        :class:`.Entity`
            Contains the following values:

            =============== ====================== =========================
            Key             Type                   Description
            --------------- ---------------------- -------------------------
            user_name       str                    The user name.
            is_admin        bool                   If this user is the admin of this team.
            state           str                    The account state of user. Could be:

                                                   - "free"
                                                   - "standard_pro_edition"
                                                   - "advanced_pro_edition"
                                                   - "free_trial_team_edition"
                                                   - "advanced_team_edition"
                                                   - "preminum_team_edition"
                                                   - "standard_team_edition"
                                                   - "frozen"
            team_id         int                    The team id of user. :obj:`None` if state equals to "frozen".
            storage_quota   int                    The total storage quota in bytes.
                                                   :obj:`None` if state equals to "frozen".
            used_storage    int                    The used storage space in bytes.
                                                   :obj:`None` if state equals to "frozen".
            expire_time     float                  The expire time in Unix timestamp.
                                                   :obj:`None` if state equals to "frozen".
            collections     list                   A list contains :class:`.Entity` with the following values:

                                                   ============= =================== ========================
                                                   Key           Type                Description
                                                   ------------- ------------------- ------------------------
                                                   href          str                 The absolute path of
                                                                                     this top folder.
                                                   used_storage  int                 The used storage space in bytes
                                                                                     of this top folder.
                                                   owner         bool                If user is the owner of
                                                                                     this top folder.
                                                   ============= =================== ========================
            =============== ====================== =========================

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        raise NotImplementedError

    def update_team_info(self, name, auth_tuple=None, client=None):
        """
        Only for admin access token.

        Update team's info.

        Currently only support updating name.

        Parameters
        ----------
        name : str
            New name
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

    def get_team_members(self, auth_tuple=None, client=None):
        """
        Only for admin access token.

        Get all members in this team.

        Parameters
        ----------
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
            The client overriding global config.

        Returns
        -------
        :obj:`list`
            A list contains :class:`.Entity` with the following values.

            ============== ================= =======================================
            Key            Type              Description
            -------------- ----------------- ---------------------------------------
            user_name      str               The user name of this member.
            admin          bool              If this member is admin.
            nickname       str               The nickname of this member
            storage_quota  int               The storage quotas in bytes.
            ldap_user      bool              If this member is managed by ldap.
                                             :obj:`None` in old version.
            disabled       bool              If this member is disabled.
                                             :obj:`None` in old version.
            ============== ================= =======================================

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        raise NotImplementedError

    def create_team_member(self, users, auth_tuple=None, client=None):
        """
        Only for admin access token.

        Create new members for given team.

        Parameters
        ----------
        users : :obj:`list`
            A list contains all users. Each user should be a :obj:`dict` which contains the following values:

            ============== ================= =======================================
            Key            Type              Description
            -------------- ----------------- ---------------------------------------
            user_name      str               The user name of this member.
            password       str               The password of this member.
            storage_quota  int               The storage quotas in bytes.
            ldap_user      bool optional     If this member is managed by ldap.
            ldap_id        str optional      The id of this member in ldap.
            ============== ================= =======================================

        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

    def update_team_member_storage_quota(self, user_name, storage_quota, auth_tuple=None, client=None):
        """
        Only for admin access token.

        Update team member's storage quota.

        Parameters
        ----------
        user_name : str
            The user's name.
        storage_quota : int or str
            The new storage quota in bytes.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

    def get_team_member_info(self, user_name, auth_tuple=None, client=None):
        """
        Only for admin access token.

        Get the info of a team member.

        Parameters
        ----------
        user_name : str
            The user's name.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
            The client overriding global config.

        Returns
        -------
        :class:`.Entity`
            Contains the following values:

            ============== ================= =======================================
            Key            Type              Description
            -------------- ----------------- ---------------------------------------
            user_name      str               The user name of this member.
            storage_quota  int               The storage quotas in bytes.
            expire_time    float             The expire time in Unix timestamp.
            sandboxes      list              A list contains :class:`.Entity` with the following values:

                                             ============= =================== ========================
                                             Key           Type                Description
                                             ------------- ------------------- ------------------------
                                             name          str                 The name of this sandbox.
                                             storage_quota int                 The storage quotas in bytes.
                                             ============= =================== ========================
            ============== ================= =======================================

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        raise NotImplementedError

    def remove_team_member(self, user_name, folder_receipt, clean_perms=False, auth_tuple=None, client=None):
        """
        Only for admin access token.

        Remove a member from team.

        Parameters
        ----------
        user_name : str
            The user's name.
        folder_receipt : str
            The user name of receiver.
        clean_perms : bool
            If delete all shared folders, if ``True``, ``folder_receipt`` will be ignored.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

    def get_group_members(self, group_id, auth_tuple=None, client=None):
        """
        Only for admin access token.

        Get the subgroups and users in a given group.

        Parameters
        ----------
        group_id : str or int
            The group id.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
            The client overriding global config.

        Returns
        -------
        :class:`.Entity`
            Contains the following values:

            ============== ================= =======================================
            Key            Type              Description
            -------------- ----------------- ---------------------------------------
            subgroups      list              A list contains :class:`.Entity` with the following values:

                                             ============= =================== ============================
                                             Key           Type                Description
                                             ------------- ------------------- ----------------------------
                                             group_id      int                 The id of this subgroup.
                                             name          str                 The name of this subgroup.
                                             ============= =================== ============================
            admins         list              A list contains :class:`.Entity` with the following values:

                                             ============= =================== ============================
                                             Key           Type                Description
                                             ------------- ------------------- ----------------------------
                                             username      str                 The user name of this user.
                                             nickname      str                 The nickname of this user.
                                             ============= =================== ============================
            users          list              A list contains :class:`.Entity` with the following values:

                                             ============= =================== ============================
                                             Key           Type                Description
                                             ------------- ------------------- ----------------------------
                                             username      str                 The user name of this user.
                                             nickname      str                 The nickname of this user.
                                             ============= =================== ============================
            ============== ================= =======================================

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        raise NotImplementedError

    def create_group(self, parent_group_id, name, admins, users=None, auth_tuple=None, client=None):
        """
        Only for admin access token.

        Create a group.

        Parameters
        ----------
        parent_group_id : str or int
            The group id of parent group.
        name : str
            The name of this group.
        admins : list
            A list contains all admins' user name.
        users : list
            A list contains all members' user name except for admins.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
            The client overriding global config.

        Returns
        -------
        int
            The group id of created group.

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, message and detail.
        """
        raise NotImplementedError

    def add_member_to_group(self, group_id, users, auth_tuple=None, client=None):
        """
        Only for admin access token.

        Add members to a given group.

        Parameters
        ----------
        group_id : str
            The group id of given group.
        users : list
            A list contains all members' user name.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

    def remove_member_from_group(self, group_id, users=None, subgroups=None, auth_tuple=None, client=None):
        """
        Only for admin access token.

        Remove members or subgroups from a given group.

        Parameters
        ----------
        group_id : str
            The group id of given group.
        users : list
            A list contains all members' user name.
        subgroups : list
            A list contains all subgroups' group id.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

    def dismiss_team(self, auth_tuple=None, client=None):
        """
        Only for admin access token.

        Dismiss current team.

        Parameters
        ----------
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

    def update_team_member_status(self, users, auth_tuple=None, client=None):
        """
        Only for admin access token.

        Update team member's status.

        Parameters
        ----------
        users : :obj:`dict`
            A dict contains user's user name as key while if disabled(bool) as value.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
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
        raise NotImplementedError

    def query_audit_logs(self, time_start, time_end, user_name=None, op_type=None, file_name=None,
                               auth_tuple=None, client=None):
        """
        Only for admin access token.

        Query audit logs.

        Parameters
        ----------
        time_start : float
            The start time in Unix timestamp.
        time_end : float
            The end time in Unix timestamp.
        user_name : str
            The user name of a given user.
        op_type : str
            The operation type. Should be one of :obj:`.OPERATION_TYPE`.
        file_name : str
            The file name.
        auth_tuple : tuple
            The auth_tuple overriding global config.
        client : :class:`aiohttp.ClientSession`
            The client overriding global config.

        Returns
        -------
        :class:`.Entity`
            Contains the following values:

            ===================== ================= =======================================
            Key                   Type              Description
            --------------------- ----------------- ---------------------------------------
            log_num               int               The number of logs.
            first_operation_time  float             The Unix timestamp of first operation in logs.
            last_operation_time   float             The Unix timestamp of last operation in logs.
            has_more              bool              If there are more logs.
            activities            list              A list contains :class:`.Entity` with the following values:

                                                    ============= =================== ============================
                                                    Key           Type                Description
                                                    ------------- ------------------- ----------------------------
                                                    operator      str                 The user name of this operation.
                                                    operation     str                 The type of this operation.
                                                    ip            str                 The ip of this operation.
                                                    ip_location   str                 The location of this ip.
                                                    terminal      str                 The terminal of this operation.
                                                    consuming     str                 How much time does this operation cost.
                                                    ============= =================== ============================
            ===================== ================= =======================================

        Raises
        ------
        :exc:`.NSWebDavHTTPError`
            Contains HTTP error code, exception and message.
        """
        raise NotImplementedError
