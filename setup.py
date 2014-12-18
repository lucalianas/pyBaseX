from distutils.core import setup
from distutils.errors import DistutilsSetupError

import pybasex

AUTHOR_INFO = [
    ('Luca Lianas', 'lucalianas@gmail.com')
]
MAINTAINER_INFO = AUTHOR_INFO
AUTHOR = '', ''.join(t[0] for t in AUTHOR_INFO)
AUTHOR_EMAIL = '', ''.join('<%s>' % t[1] for t in AUTHOR_INFO)
MAINTAINER = ", ".join(t[0] for t in MAINTAINER_INFO)
MAINTAINER_EMAIL = ", ".join("<%s>" % t[1] for t in MAINTAINER_INFO)
URL = 'https://github.com/lucalianas/pyBaseX'

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
    description=pybasex.__doc__.strip().splitlines()[0],
    long_description=pybasex.__doc__.strip(),
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    license='MIT License',
    keyword=['BaseX', 'REST', 'HTTP', 'XPATH', 'XML', 'database', 'python'],
    maintainer=MAINTAINER,
    maintainer_email=MAINTAINER_EMAIL,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    packages=[
        'pybasex',
        'pybasex.utils',
    ],
    requires=[
        'requests',
        'lxml',
    ]
)