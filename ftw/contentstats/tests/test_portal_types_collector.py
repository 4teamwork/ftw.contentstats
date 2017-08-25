from ftw.builder import Builder
from ftw.builder import create
from ftw.contentstats.interfaces import IStatsCollector
from ftw.contentstats.tests import FunctionalTestCase
from zope.component import getMultiAdapter


class TestPortalTypesCollector(FunctionalTestCase):

    def setUp(self):
        super(TestPortalTypesCollector, self).setUp()
        self.grant('Manager')

        self.collector = getMultiAdapter((self.portal, self.portal.REQUEST),
                                         IStatsCollector,
                                         name='portal_types')

    def create_content(self):
        create(Builder('folder'))
        create(Builder('page'))
        create(Builder('page'))

    def test_type_counts_empty(self):
        counts = self.collector.get_statistic()
        self.assertEqual({}, counts)

    def test_type_counts_reported_correctly(self):
        self.create_content()
        counts = self.collector.get_statistic()
        self.assertEqual({u'Folder': 1, u'Page': 2}, counts)

    def test_type_titles_reported_correctly(self):
        titles = self.collector.get_type_title_mapping
        self.assertDictContainsSubset({
            'Discussion Item': u'Comment',
            'Document': u'Page',
            'News Item': u'News Item'},
            titles)
