from setuptools import setup, find_packages

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError):
    long_description = open('README.md').read()

setup(
    name='nswebdav',
    packages=find_packages(),
    version='0.0.5',
    license='MIT',
    description='A python implementation for nutstore(jianguoyun) webdav',
    long_description=long_description,
    author='Sraw',
    author_email='lzyl888@gmail.com',
    url='https://github.com/Sraw/nswebdav',
    download_url='https://github.com/Sraw/nswebdav/tarball/0.0.5',
    keywords="nutstore webdav jianguoyun",
    classifiers=[
        'Development Status :: 3 - Alpha',
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
    python_requires='~=3.5',
)
