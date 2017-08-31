from ftw.builder import Builder
from ftw.builder import create
from ftw.contentstats.interfaces import IStatsCollector
from ftw.contentstats.stats import ContentStats
from ftw.contentstats.tests import FunctionalTestCase
from plone import api
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
        self.set_workflow_chain('Document', 'simple_publication_workflow')
        self.set_workflow_chain('Folder', 'simple_publication_workflow')
        create(Builder('folder'))
        create(Builder('page'))
        create(Builder('page')
               .in_state('published'))

    def set_workflow_chain(self, for_type, to_workflow):
        wftool = api.portal.get_tool('portal_workflow')
        wftool.setChainForPortalTypes((for_type,),
                                      (to_workflow,))

    def test_all_registered_collectors_respects_the_contract(self):
        for name_, collector in self.stats._all_adapters():
            verifyClass(IStatsCollector, collector.__class__)

    def test_get_all_collector_names(self):
        self.assertEquals(['portal_types', 'review_states'],
                          self.stats.get_collector_names())

    def test_statistic_contains_portal_types_statistics(self):
        self.create_content()

        self.assertIn('portal_types', self.stats.statistics())
        self.assertDictEqual(
            {u'Folder': 1, u'Page': 2},
            self.stats.statistics()['portal_types']['data'])

        self.assertEquals(u'Portal type statistics',
                          self.stats.statistics()['portal_types']['title'])

    def test_statistic_contains_review_state_statistics(self):
        self.create_content()

        self.assertIn('review_states', self.stats.statistics())
        self.assertDictEqual(
            {'private': 2, 'published': 1},
            self.stats.statistics()['review_states']['data'])

        self.assertEquals(u'Review state statistics',
                          self.stats.statistics()['review_states']['title'])
