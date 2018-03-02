.. nswebdav documentation master file, created by
   sphinx-quickstart on Fri Mar  2 09:48:20 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Documentation for nswebdav
==========================

This is a python implementation for nutstore(jianguoyun) webdav.

It implements easy-to-use high-level interface and support both sync version and async version.

The sync version needs :code:`requests` and async version needs :code:`aiohttp`.
You need to install either of them manually.

To install it:

:code:`pip install nswebdav`

To use sync version, you need :code:`pip install requests` first:

.. code-block:: python

   from nswebdav.sync import NutstoreDav

   # base_url should be something like "http://www.jianguoyun.com"
   # be ware not to add "/".
   dav =  NutstoreDav(base_url)

   # optional, set global auth_tuple which will be passed to requests.request.
   # but you can still override it in every methods.
   dav.config(auth_tuple)

   dav.ls(path)

To use async version, you need :code:`pip install aiohttp` first:

.. code-block:: python

   from nswebdav.async import AsyncNutstoreDav

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

.. toctree::
   :maxdepth: 2
   :caption: APIs:

   source/nswebdav


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
