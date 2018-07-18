from setuptools import setup, find_packages
from nswebdav import __version__

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError):
    long_description = open('README.md').read()

setup(
    name='nswebdav',
    packages=find_packages(),
    version=__version__,
    license='MIT',
    description='A python implementation for nutstore(jianguoyun) webdav',
    long_description=long_description,
    author='Sraw',
    author_email='lzyl888@gmail.com',
    url='https://github.com/Sraw/nswebdav',
    download_url='https://github.com/Sraw/nswebdav/tarball/%s' % __version__,
    keywords="nutstore webdav jianguoyun",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet',
    ],
    install_requires=[
        "lxml",
        "jinja2",
    ],
    extras_require={
        "sync": ["requests"],
        "async": ["aiohttp"],
    },
    python_requires='~=3.5',
)
