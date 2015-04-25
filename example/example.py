import os
from service_host.conf import settings, Verbosity
from service_host.service import Service

DEBUG = True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

settings.configure(
    CACHE=not DEBUG,
    USE_MANAGER=DEBUG,
    SOURCE_ROOT=BASE_DIR,
)

hello_world = Service('hello_world')
double = Service('double')
read_file = Service('read_file')

if __name__ == '__main__':
    print('')

    name = raw_input('Enter your name: ')

    print('Response: ' + hello_world.call(name=name) + '\n')

    number = input('Enter a number to double: ')

    print('Response: ' + double.call(number=number) + '\n')

    filename = raw_input('Enter a file to read (defaults to services.config.js): ')
    filename = filename or 'services.config.js'

    print('Response: ' + read_file.call(file=os.path.join(BASE_DIR, filename)) + '\n')