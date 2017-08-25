from ftw.builder import Builder
from ftw.builder import create
from ftw.contentstats.stats import ContentStats
from ftw.contentstats.tests import FunctionalTestCase
from unittest import TestCase


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

    def test_type_counts_empty(self):
        counts = self.stats.get_type_counts()
        self.assertEqual([], counts)

    def test_type_counts_reported_correctly(self):
        self.create_content()
        counts = self.stats.get_type_counts()
        self.assertEqual([(u'Folder', 1), (u'Page', 2)], counts)

    def test_type_titles_reported_correctly(self):
        titles = self.stats.get_type_title_mapping
        self.assertDictContainsSubset({
            'Discussion Item': u'Comment',
            'Document': u'Page',
            'News Item': u'News Item'},
            titles)
