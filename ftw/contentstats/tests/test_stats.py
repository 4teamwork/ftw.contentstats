from ftw.builder import Builder
from ftw.builder import create
from ftw.contentstats.interfaces import IStatsCollector
from ftw.contentstats.stats import ContentStats
from ftw.contentstats.tests import FunctionalTestCase
from unittest import TestCase
from zope.interface.verify import verifyClass


class TestContentStatsNoPlone(TestCase):

    def test_raise_exception_if_there_is_no_plone(self):
        with self.assertRaises(Exception):
            ContentStats()


class TestContentStats(FunctionalTestCase):

    def setUp(self):
        super(TestContentStats, self).setUp()
        self.grant('Manager')

        self.stats = ContentStats()

    def create_content(self):
        create(Builder('folder'))
        create(Builder('page'))
        create(Builder('page'))

    def test_all_registered_collectors_respects_the_contract(self):
        for name_, collector in self.stats._all_adapters():
            verifyClass(IStatsCollector, collector.__class__)

    def test_get_all_collector_names(self):
        self.assertEquals(['portal_types'],
                          self.stats.get_collector_names())

    def test_statistic_contains_portal_types_statistics(self):
        self.create_content()

        self.assertIn('portal_types', self.stats.statistics())
        self.assertDictEqual(
            {u'Folder': 1, u'Page': 2},
            self.stats.statistics()['portal_types']['data'])

        self.assertEquals(u'Portal type statistics',
                          self.stats.statistics()['portal_types']['title'])
