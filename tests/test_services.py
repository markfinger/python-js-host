import json
import os
import unittest
from service_host.exceptions import ConfigError, ServiceError
from service_host.service import Service
from service_host.conf import settings
from service_host.service_host import ServiceHost
from service_host.host import host

no_services_host_config_file = os.path.join(os.path.dirname(__file__), 'config_files', 'no_services.services.config.js')


class TestServices(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.echo = Service('echo')
        cls.echo_data = Service('echo_data')
        cls.async_echo = Service('async_echo')
        cls.error = Service('error')

    def test_is_instantiated_properly(self):
        service = Service(name='foo')

        self.assertEqual(service.name, 'foo')
        self.assertEqual(service.host, None)
        self.assertEqual(service.cacheable, True)

    def test_name_is_required(self):
        self.assertRaises(ConfigError, Service)

    def test_host_is_bound_lazily(self):
        service = Service(name='test')
        self.assertIsNone(service.host)
        self.assertEqual(service.get_host(), host)
        self.assertEqual(service.host, host)

    def test_get_name(self):
        self.assertEqual(self.echo.get_name(), self.echo.name)

    def test_get_config_validates_the_host_config(self):
        class Test(Service):
            name = 'test'
        service = Test()

        service.host = ServiceHost(
            settings.PATH_TO_NODE,
            settings.SOURCE_ROOT,
            no_services_host_config_file,
        )

        self.assertIsInstance(service.host.config['services'], list)
        self.assertEqual(len(service.host.config['services']), 0)

        self.assertRaises(ConfigError, service.get_config)

        service.host.config['services'].append({'name': 'test', 'cache': False})

        self.assertEqual(service.get_config(), {'name': 'test', 'cache': False})

    def test_generate_cache_key(self):
        self.assertEqual(
            self.echo.generate_cache_key('foo', None),
            '0beec7b5ea3f0fdbc95d0dd47f3c5bc275da8a33',
        )

    def test_serialize_data(self):
        self.assertEqual(
            self.echo.serialize_data({'foo': 'bar', 'woz': [1, 2, 3]}),
            json.dumps({'foo': 'bar', 'woz': [1, 2, 3]}),
        )

    def test_is_cacheable(self):
        _CACHE = settings.CACHE

        settings._unlock()
        settings.CACHE = True

        class Uncacheable(Service):
            name = 'echo'
            cacheable = False
        uncacheable = Uncacheable()

        self.assertFalse(uncacheable.is_cacheable())

        uncacheable.cacheable = True
        self.assertTrue(uncacheable.is_cacheable())

        uncacheable.config['cache'] = False
        self.assertFalse(uncacheable.is_cacheable())

        uncacheable.config['cache'] = True
        self.assertTrue(uncacheable.is_cacheable())

        settings.CACHE = False
        self.assertFalse(uncacheable.is_cacheable())

        # Revert the setting
        settings.CACHE = _CACHE
        settings._lock()

    def test_call(self):
        self.assertEqual(self.echo.call(echo='test').text, 'test')
        self.assertEqual(self.echo_data.call().text, '{}')
        self.assertEqual(
            json.loads(self.echo_data.call(foo=1, bar=[2, 3, {'woz': 4}]).text),
            {'foo': 1, 'bar': [2, 3, {'woz': 4}]}
        )
        self.assertEqual(self.async_echo.call(echo='foo').text, 'foo')

    def test_500_errors_are_raised_as_service_errors(self):
        self.assertRaises(ServiceError, self.error.call)
        self.assertRaises(ServiceError, self.echo.call)
        self.assertRaises(ServiceError, self.echo.call, _echo='test')
        self.assertRaises(ServiceError, self.echo.call, foo='test')

    '''
    call
    '''