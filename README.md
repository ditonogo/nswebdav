# Introduction

For now, it is just the beginning of this project.

Limited implementation without any test case.

Any help is welcome.

# Usage

Package can only run on python3.5 or above as it uses new key words `async` and `await` for async support.

To install it:

`pip install nswebdav`

To use it:

    from nswebdav import NutstoreDav
    
    # base_url should be something like "http://www.jianguoyun.com"
    # be ware not to add "/".
    dav =  NutstoreDav(base_url)
    # optional, set global auth_tuple which will be passed to requests.request.
    # but you can still override it in every methods.
    dav.config(auth_tuple)
    
    dav.ls(path)
    
To use async version:

    from nswebdav import AsyncNutstoreDav
        
    # base_url should be something like "http://www.jianguoyun.com"
    # be ware not to add "/".
    dav =  AsyncNutstoreDav(base_url)
    # optional, set global session or auth_tuple.
    # session should be an instance of aiohttp.ClientSession.
    # auth_tuple should be a tuple like (user_name, access_token)
    # but you can still override them in every methods.
    dav.config(session, auth_tuple)
    # dav.config(auth_tuple)  # you can set only one of them.
    
    dav.ls(path)  # return a corotine, should be "await"ed.

# TODO

Write document.

Complete more functions.
