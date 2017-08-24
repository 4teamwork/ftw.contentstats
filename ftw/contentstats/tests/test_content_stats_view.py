from ftw.builder import Builder
from ftw.builder import create
from ftw.contentstats.stats import ContentStats
from ftw.contentstats.tests import FunctionalTestCase
from ftw.testbrowser import browsing
from zExceptions import Unauthorized
import json


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

    @browsing
    def test_view_lists_counts_in_table(self, browser):
        self.create_content()
        browser.login().open(self.portal, view='@@content-stats')
        table = browser.css('#content-stats-type-counts').first
        self.assertEqual(
            [['', 'Folder', '1'], ['', 'Page', '2']],
            table.lists())

    @browsing
    def test_editable_border_disabled(self, browser):
        browser.login().open(self.portal, view='@@content-stats')
        self.assertEqual(0, len(browser.css('#content-views')))

    @browsing
    def test_data_attribute_with_content_stats(self, browser):
        browser.login().open(self.portal, view='@@content-stats')
        self.assertItemsEqual(
            ContentStats().get_type_counts(),
            json.loads(browser.css('#content-stats-data').first.attrib['data-counts']))

    @browsing
    def test_json_endpoint(self, browser):
        self.create_content()
        browser.login().open(self.portal, view='content-stats.json')

        self.assertEquals('application/json',
                          browser.headers.get('Content-Type'))

        self.assertDictEqual(ContentStats().get_type_counts(),
                             browser.json)
