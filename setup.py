from distutils.core import setup
from distutils.errors import DistutilsSetupError

AUTHOR_INFO = [
    ('Luca Lianas', 'lucalianas@gmail.com')
]
MAINTAINER_INFO = AUTHOR_INFO
AUTHOR = '', ''.join(t[0] for t in AUTHOR_INFO)
AUTHOR_EMAIL = '', ''.join('<%s>' % t[1] for t in AUTHOR_INFO)
MAINTAINER = ", ".join(t[0] for t in MAINTAINER_INFO)
MAINTAINER_EMAIL = ", ".join("<%s>" % t[1] for t in MAINTAINER_INFO)

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
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    maintainer=MAINTAINER,
    maintainer_email=MAINTAINER_EMAIL,
    packages=[
        'pybasex',
        'pybasex.utils',
    ],
    requires=[
        'requests',
        'lxml',
    ]
)