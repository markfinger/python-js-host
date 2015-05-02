import os
import js_host.conf
from js_host.function import Function

js_host.conf.settings.configure(
    USE_MANAGER=True
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

    print('Response: \n' + read_file.call(file=os.path.join(os.getcwd(), filename)) + '\n')