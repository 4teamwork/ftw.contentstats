from ftw.contentstats.interfaces import IStatsProvider
from ftw.contentstats.providers.perf_metrics import get_buildout_dir
from ftw.contentstats.providers.perf_metrics import get_instance_names
from ftw.contentstats.providers.perf_metrics import get_instance_number
from ftw.contentstats.providers.perf_metrics import get_port_base
from ftw.contentstats.testing import FTW_MONITOR_INSTALLED
from mock import Mock
from mock import patch
from plone.testing import Layer
from unittest import skipUnless
from unittest import TestCase
from ZODB.interfaces import IDatabase
from zope.component import getMultiAdapter
from zope.component import provideUtility


if FTW_MONITOR_INSTALLED:
    from ftw.monitor.testing import MONITOR_ZSERVER_TESTING
    from ftw.monitor.testing import MonitorTestCase
else:
    MonitorTestCase = TestCase
    MONITOR_ZSERVER_TESTING = Layer(name='stub')


@skipUnless(FTW_MONITOR_INSTALLED, 'Requires ftw.monitor to run')
class TestPerfMetricsProvider(MonitorTestCase):

    layer = MONITOR_ZSERVER_TESTING

    @patch('ftw.contentstats.providers.perf_metrics.get_monitor_ports')
    def test_reports_loads_and_stores(self, mocked_get_monitor_ports):
        mocked_get_monitor_ports.return_value = {
            'instance99': MonitorTestCase.MONITOR_PORT}

        # Plone's testing DB is named 'unnamed' in tests. Also register it
        # as 'main' in order for ftw.monitor to be able to pick it up
        db = self.layer['portal']._p_jar.db()
        provideUtility(db, IDatabase, name='main')

        provider = getMultiAdapter(
            (self.layer['portal'], self.portal.REQUEST),
            IStatsProvider, name='perf_metrics')

        perf_metrics = provider.get_raw_stats()

        actual_categories = perf_metrics['instance99'].keys()
        for expected_category in [u'instance', u'cache', u'db', u'memory']:
            self.assertIn(expected_category, actual_categories)


class TestPerfMetricsHelperFunctions(TestCase):

    def test_get_port_base(self):
        self.assertEqual(14700, get_port_base(14702))

    def test_get_instance_number(self):
        self.assertIsNone(get_instance_number('instance'))
        self.assertEqual(1, get_instance_number('instance1'))
        self.assertEqual(1, get_instance_number('instance01'))
        self.assertEqual(42, get_instance_number('instance42'))

    def test_get_instance_names(self):
        instance_scripts = ['bin/instance1', '/path/to/bin/instance2']
        self.assertEqual(['instance1', 'instance2'],
                         get_instance_names(instance_scripts))

    def test_get_buildout_dir(self):
        zconfig = Mock(instancehome='/apps/01-plone/parts/instance1')
        self.assertEqual('/apps/01-plone', get_buildout_dir(zconfig))
