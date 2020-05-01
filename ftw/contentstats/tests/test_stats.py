from ftw.builder import Builder
from ftw.builder import create
from ftw.contentstats.interfaces import IStatsProvider
from ftw.contentstats.stats import ContentStats
from ftw.contentstats.testing import FTW_MONITOR_INSTALLED
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

        self.stats_util = ContentStats()

    def create_content(self):
        self.set_workflow_chain('Document', 'simple_publication_workflow')
        self.set_workflow_chain('Folder', 'simple_publication_workflow')
        create(Builder('folder'))
        create(Builder('page'))
        create(Builder('page')
               .in_state('published'))

    def test_all_registered_providers_respect_the_contract(self):
        for name_, provider in self.stats_util._get_providers():
            verifyClass(IStatsProvider, provider.__class__)

    def test_get_all_provider_names(self):
        expected_provider_names = [
            'portal_types',
            'review_states',
            'disk_usage',
        ]
        if FTW_MONITOR_INSTALLED:
            expected_provider_names.append('perf_metrics')

        self.assertItemsEqual(expected_provider_names,
                              self.stats_util.get_provider_names())

    def test_stats_contain_portal_types_stats(self):
        self.create_content()
        stats = self.stats_util.get_human_readable_stats()

        self.assertIn('portal_types', stats)
        self.assertDictEqual(
            {u'Folder': 1, u'Page': 2},
            stats['portal_types']['data'])

        self.assertEquals(u'Portal type statistics',
                          stats['portal_types']['title'])

    def test_stats_contain_review_state_stats(self):
        self.create_content()

        stats = self.stats_util.get_human_readable_stats()
        self.assertIn('review_states', stats)
        self.assertDictEqual(
            {'private': 2, 'published': 1},
            stats['review_states']['data'])

        self.assertEquals(u'Review state statistics',
                          stats['review_states']['title'])

    def test_stats_contain_disk_usage_stats(self):
        stats = self.stats_util.get_human_readable_stats()
        self.assertIn('disk_usage', stats)

        self.assertEquals(u'Disk usage statistics',
                          stats['disk_usage']['title'])
