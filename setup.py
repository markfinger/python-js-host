from setuptools import setup
import service_host

setup(
    name='service-host',
    version=service_host.VERSION,
    packages=['service_host'],
    install_requires=[
        'requests>=2.5.0',
        'optional-django==0.2.1',
    ],
    description='Python binding to service-host',
    long_description='Documentation at https://github.com/markfinger/python-service-host',
    author='Mark Finger',
    author_email='markfinger@gmail.com',
    url='https://github.com/markfinger/service-host',
)
