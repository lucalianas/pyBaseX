try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from distutils.errors import DistutilsSetupError

DESCRIPTION = 'pyBaseX: a Python adapter for BaseX REST interface'
LONG_DESCRIPTION = """
pyBaseX: a Python adapter for BaseX REST interface
--------------------------------------------------

pyBaseX is a Python package that provides functionality to interact with BaseX via REST interface.

The main features include:
 * CRUD methods for databases and documents
 * XPATH queries execution
"""

AUTHOR_INFO = [
    ('Luca Lianas', 'lucalianas@gmail.com')
]
MAINTAINER_INFO = AUTHOR_INFO
AUTHOR = '', ''.join(t[0] for t in AUTHOR_INFO)
AUTHOR_EMAIL = '', ''.join('<%s>' % t[1] for t in AUTHOR_INFO)
MAINTAINER = ", ".join(t[0] for t in MAINTAINER_INFO)
MAINTAINER_EMAIL = ", ".join("<%s>" % t[1] for t in MAINTAINER_INFO)
URL = 'https://github.com/lucalianas/pyBaseX'
DOWNLOAD_URL = 'https://github.com/lucalianas/pyBaseX/releases'

try:
    with open("NAME") as f:
        NAME = f.read().strip()
    with open("VERSION") as f:
        VERSION = f.read().strip()
except IOError:
    raise DistutilsSetupError("failed to read name/version info")

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    download_url=DOWNLOAD_URL,
    license='MIT License',
    platforms=['any'],
    keywords=['BaseX', 'REST', 'HTTP', 'XPATH', 'XML', 'database', 'python'],
    maintainer=MAINTAINER,
    maintainer_email=MAINTAINER_EMAIL,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Intended Audience :: Developers',
    ],
    packages=[
        'pybasex',
        'pybasex.utils',
    ],
    requires=[
        'setuptools',
        'requests',
        'lxml',
    ],
    install_requires=[
        'setuptools',
        'requests',
        'lxml',
    ]
)
