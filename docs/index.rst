.. nswebdav documentation master file, created by
   sphinx-quickstart on Fri Mar  2 09:48:20 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Documentation for nswebdav
==========================

This is a python implementation for `nutstore(jianguoyun) <https://www.jianguoyun.com>`_ webdav.

It implements easy-to-use high-level interface and support both sync version and async version.

The sync version needs `requests <http://docs.python-requests.org/en/master>`_
while async version needs `aiohttp <https://aiohttp.readthedocs.io/en/stable>`_.
You need to install either of them manually if you install by ``pip install nswebdav``.

But you can directly install the version you want:

``pip install nswebdav[sync]`` for sync version

``pip install nswebdav[async]`` for async version

Sync version:

.. code-block:: python

   from nswebdav.sync import NutstoreDav

   # Will connect to https://dav.jianguoyun.com by default,
   # but you can overwrite it by passing arg base_url.
   # base_url should be something like "http://www.jianguoyun.com"
   # be ware not to add "/".
   dav = NutstoreDav()
   dav.config(auth_tuple=(user_name, access_token))

   dav.ls("/")

Async version:

.. code-block:: python

   from nswebdav.async import AsyncNutstoreDav
   import asyncio

   # Will connect to https://dav.jianguoyun.com by default,
   # but you can overwrite it by passing arg base_url.
   # base_url should be something like "http://www.jianguoyun.com"
   # be ware not to add "/".
   dav = AsyncNutstoreDav()
   dav.config(auth_tuple=(user_name, access_token))

   asyncio.get_event_loop().run_until_complete(dav.ls("/"))

To develop, clone this project from github and use ``pipenv install --dev``.

.. toctree::
   :maxdepth: 2
   :caption: API:

   source/nswebdav


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
