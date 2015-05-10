from setuptools import setup, find_packages
import js_host

setup(
    name='js-host',
    version=js_host.__version__,
    packages=find_packages(exclude=('examples', 'tests')),
    install_requires=[
        'requests>=2.5.0',
        'optional-django==0.3.0',
    ],
    description='Python bindings to a performant JavaScript environment',
    long_description='Documentation at https://github.com/markfinger/python-js-host',
    author='Mark Finger',
    author_email='markfinger@gmail.com',
    url='https://github.com/markfinger/python-js-host',
)
