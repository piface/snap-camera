#!/usr/bin/python3
import sys
from distutils.core import setup


VERSION_FILE = "snapcamera/version.py"


def get_version():
    version_vars = {}
    with open(VERSION_FILE) as f:
        code = compile(f.read(), VERSION_FILE, 'exec')
        exec(code, None, version_vars)
    return version_vars['__version__']


setup(
    name='snap-camera',
    version=get_version(),
    description='A camera that uses PiFace Control and Display and Raspicam.',
    author='Thomas Preston',
    author_email='thomas.preston@openlx.org.uk',
    license='GPLv3+',
    url='http://www.piface.org.uk/',
    packages=['snapcamera'],
    classifiers=[
        "License :: OSI Approved :: GNU Affero General Public License v3 or "
        "later (AGPLv3+)",
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
    ],
    keywords='piface cad control and display snap camera raspberrypi openlx',
)
