import os
from js_host.conf import settings, Verbosity
from js_host.function import Function

DEBUG = True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

settings.configure(
    CACHE=not DEBUG,
    USE_MANAGER=DEBUG,
    SOURCE_ROOT=BASE_DIR,
    VERBOSITY=Verbosity.PROCESS_STOP,
)

greet = Function('greet')
double = Function('double')
read_file = Function('read_file')

if __name__ == '__main__':
    print('')

    name = raw_input('Enter your name: ')

    print('Response: ' + greet.call(name=name) + '\n')

    number = input('Enter a number to double: ')

    print('Response: ' + double.call(number=number) + '\n')

    filename = raw_input('Enter a file to read (defaults to host.config.js): ')
    filename = filename or 'host.config.js'

    print('Response: \n' + read_file.call(file=os.path.join(BASE_DIR, filename)) + '\n')