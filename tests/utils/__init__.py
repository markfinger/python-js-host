import os
import subprocess
import json
import atexit
from js_host.js_host import JSHost
from js_host.conf import settings
from js_host.verbosity import VERBOSE


def start_proxy():
    cmd = (settings.PATH_TO_NODE, os.path.join(os.path.dirname(__file__), 'proxy.js'),)

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    output = process.stdout.readline()

    output = output.decode('utf-8')

    if output.strip() != 'proxy listening on port 8000':
        raise Exception('Unexpected output from `{}`: {}'.format(' '.join(cmd), output))

    atexit.register(stop_proxy, process=process)

    return process


def stop_proxy(process):
    process.kill()


def start_host_process(host, port_override=None):
    assert isinstance(host, JSHost)

    cmd = (
        host.path_to_node,
        host.get_path_to_bin(),
        host.config_file,
        '--json'
    )

    if port_override is not None:
        cmd += ('--port', str(port_override))

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    output = process.stdout.readline()

    output = output.decode('utf-8')

    if not output.startswith('{'):
        raise Exception('Unexpected output from `{}`: {}'.format(' '.join(cmd), output))

    status = json.loads(output)

    if port_override is not None:
        if port_override != 0:
            assert status['config']['port'] == port_override
        host.get_config()['port'] = status['config']['port']

    expected = host.get_status()
    if status != expected:
        raise Exception(
            'Unexpected output {}. Expected {}'.format(status, expected)
        )

    if settings.VERBOSITY >= VERBOSE:
        print('Started {}'.format(host.get_name()))

    atexit.register(stop_host_process, host=host, process=process)

    return process


def stop_host_process(host, process):
    # Sanity checks
    assert isinstance(host, JSHost)
    assert process is not None

    if host.is_running():
        process.kill()
        if settings.VERBOSITY == VERBOSE:
            print('Stopped {}'.format(host.get_name()))