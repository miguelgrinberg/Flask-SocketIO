"""
Flask-SocketIO
--------------

Socket.IO integration for Flask applications.
"""
import re
from setuptools import setup

with open('flask_socketio/__init__.py', 'r') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        f.read(), re.MULTILINE).group(1)

setup(
    name='Flask-SocketIO',
    version=version,
    url='http://github.com/miguelgrinberg/Flask-SocketIO/',
    license='MIT',
    author='Miguel Grinberg',
    author_email='miguelgrinberg50@gmail.com',
    description='Socket.IO integration for Flask applications',
    long_description=__doc__,
    packages=['flask_socketio'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'flask.commands': [
            'run=flask_socketio.cli:run'
        ],
    },
    install_requires=[
        'Flask>=0.9',
        'python-socketio>=2.1.0'
    ],
    tests_require=[
        'coverage'
    ],
    test_suite='test_socketio',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
