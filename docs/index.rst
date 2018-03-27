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
You need to install either of them manually.

To install it:

``pip install nswebdav``

To use sync version, you need ``pip install requests`` first:

.. code-block:: python

   from nswebdav.sync import NutstoreDav

   # Will connect to https://dav.jianguoyun.com by default,
   # but you can overwrite it by passing arg base_url.
   # base_url should be something like "http://www.jianguoyun.com"
   # be ware not to add "/".
   dav = NutstoreDav()

   dav.ls("/")

To use async version, you need ``pip install aiohttp`` first:

.. code-block:: python

   from nswebdav.async import AsyncNutstoreDav
   import asyncio

   # Will connect to https://dav.jianguoyun.com by default,
   # but you can overwrite it by passing arg base_url.
   # base_url should be something like "http://www.jianguoyun.com"
   # be ware not to add "/".
   dav = AsyncNutstoreDav()

   asyncio.get_event_loop.run_until_complete(dav.ls("/"))

.. toctree::
   :maxdepth: 2
   :caption: APIs:

   source/nswebdav


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
