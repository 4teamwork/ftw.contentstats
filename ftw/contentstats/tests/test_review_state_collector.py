from ftw.builder import Builder
from ftw.builder import create
from ftw.contentstats.interfaces import IStatsCollector
from ftw.contentstats.tests import FunctionalTestCase
from zope.component import getMultiAdapter


class TestReviewStatesCollector(FunctionalTestCase):

    def setUp(self):
        super(TestReviewStatesCollector, self).setUp()
        self.grant('Manager')

        self.collector = getMultiAdapter((self.portal, self.portal.REQUEST),
                                         IStatsCollector,
                                         name='review_states')

    def create_content(self):
        self.set_workflow_chain('Document', 'simple_publication_workflow')
        self.set_workflow_chain('Folder', 'simple_publication_workflow')
        create(Builder('folder'))
        create(Builder('page'))
        create(Builder('page')
               .in_state('published'))

    def test_review_states_counts_empty(self):
        counts = self.collector.get_raw_stats()
        self.assertEqual({}, counts)

    def test_review_states_counts_reported_correctly(self):
        self.create_content()
        counts = self.collector.get_raw_stats()
        self.assertEqual({'private': 2, 'published': 1}, counts)

    def test_display_names_reported_correctly(self):
        self.create_content()
        titles = self.collector.get_display_names()
        self.assertDictContainsSubset({
            'private': u'private',
            'published': u'published'},
            titles)
