from ftw.builder import Builder
from ftw.builder import create
from ftw.contentstats.tests import FunctionalTestCase
from ftw.testbrowser import browsing
from zExceptions import Unauthorized


class TestContentStatsView(FunctionalTestCase):

    def setUp(self):
        super(TestContentStatsView, self).setUp()
        self.grant('Manager')

    def create_content(self):
        create(Builder('folder'))
        create(Builder('page'))
        create(Builder('page'))

    def test_content_stats_view_only_accessible_for_manager(self):
        self.grant('Contributor', 'Editor', 'Reviewer', 'Publisher')
        with self.assertRaises(Unauthorized):
            self.portal.restrictedTraverse('@@content-stats')

    def test_type_counts_empty(self):
        view = self.portal.restrictedTraverse('@@content-stats')
        counts = view.get_type_counts()
        self.assertEqual([], counts)

    def test_type_counts_reported_correctly(self):
        self.create_content()
        view = self.portal.restrictedTraverse('@@content-stats')
        counts = view.get_type_counts()
        self.assertEqual([('Document', 2), ('Folder', 1)], counts)

    def test_type_titles_reported_correctly(self):
        view = self.portal.restrictedTraverse('@@content-stats')
        titles = view.get_type_titles()
        self.assertDictContainsSubset({
            'Discussion Item': u'Comment',
            'Document': u'Page',
            'News Item': u'News Item'},
            titles)

    @browsing
    def test_view_lists_counts_in_table(self, browser):
        self.create_content()
        browser.login().open(self.portal, view='@@content-stats')
        table = browser.css('#content-stats-type-counts').first
        self.assertEqual(
            [['', 'Page', '2'], ['', 'Folder', '1']],
            table.lists())

    @browsing
    def test_editable_border_disabled(self, browser):
        browser.login().open(self.portal, view='@@content-stats')
        self.assertEqual(0, len(browser.css('#content-views')))
