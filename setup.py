"""
Flask-SocketIO
--------------

Socket.IO integration for Flask applications.
"""
from setuptools import setup


setup(
    name='Flask-SocketIO',
    version='0.2.2',
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
        'gevent-socketio>=0.3.6'
    ],
    test_suite='test_socketio',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
