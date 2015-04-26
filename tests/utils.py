import subprocess
import json
import atexit
from js_host.js_host import JSHost
from js_host.conf import settings, Verbosity


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

    config = json.loads(output)

    if port_override is not None:
        if port_override != 0:
            assert config['port'] == port_override
        host.config['port'] = config['port']

    expected = host.get_comparable_config(host.config)
    actual = host.get_comparable_config(config)
    if actual != expected:
        raise Exception(
            'Unexpected output {}. Expected {}'.format(actual, expected)
        )

    if settings.VERBOSITY == Verbosity.ALL:
        print('Started {}'.format(host.get_name()))

    atexit.register(stop_host_process, host=host, process=process)

    return process


def stop_host_process(host, process):
    # Sanity checks
    assert isinstance(host, JSHost)
    assert process is not None

    if host.is_running():
        process.kill()
        if settings.VERBOSITY == Verbosity.ALL:
            print('Stopped {}'.format(host.get_name()))