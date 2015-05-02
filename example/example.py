import os
from optional_django import six
import js_host.conf
from js_host.function import Function

js_host.conf.settings.configure(USE_MANAGER=True)

greet = Function('greet')
double = Function('double')
read_file = Function('read_file')

if __name__ == '__main__':
    print('')

    if six.PY2:
        name = raw_input('Enter your name: ')
    else:
        name = input('Enter your name: ')

    print('Response: ' + greet.call(name=name) + '\n')

    number = input('Enter a number to double: ')

    if not six.PY2:
        number = int(number)

    print('Response: ' + double.call(number=number) + '\n')

    print('Asking the host to read the host.config.js file...\n')

    print('Response: ' + read_file.call(file=os.path.join(os.getcwd(), 'host.config.js')) + '\n')