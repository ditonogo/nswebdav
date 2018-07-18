#: A dict contains permission's number as string and its corresponding meanings.
PERM_MAP = {
    "1": "download and preview",
    "2": "upload",
    "3": "upload, download, preview, remove and move",
    "4": "upload, download, preview, remove, move and change acls of others",
    "5": "preview"
}

#: A set contains all available operation types.
OPERATION_TYPE = {
    "SESSION_START",
    "DOWNLOAD",
    "UPLOAD",
    "SHARE",
    "MOVE",
    "DELETE",
    "RESTORE",
    "PREVIEW",
    "PURGE",
    "PWD_ATTACK",
    "VIRUS_INFECTED"
}
