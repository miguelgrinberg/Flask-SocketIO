"""
Flask-SocketIO
--------------

Socket.IO integration for Flask applications.
"""
from setuptools import setup


setup(
    name='Flask-SocketIO',
    version='2.3',
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
    install_requires=[
        'Flask>=0.9',
        'python-socketio>=0.9.0',
        'python-engineio>=0.8.2'
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
