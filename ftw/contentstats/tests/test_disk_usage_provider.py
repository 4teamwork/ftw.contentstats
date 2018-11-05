from ftw.contentstats.interfaces import IStatsProvider
from ftw.contentstats.logger import get_log_dir_path
from ftw.contentstats.tests import assets
from ftw.contentstats.tests import FunctionalTestCase
from os.path import join
from zope.component import getMultiAdapter
import os


class TestDiskUsageProvider(FunctionalTestCase):

    def setUp(self):
        super(TestDiskUsageProvider, self).setUp()
        self.grant('Manager')

        self.provider = getMultiAdapter((self.portal, self.portal.REQUEST),
                                        IStatsProvider,
                                        name='disk_usage')

        log_dir = get_log_dir_path()
        self.disk_usage_path = join(log_dir, 'disk-usage.json')

    def tearDown(self):
        super(TestDiskUsageProvider, self).tearDown()
        try:
            os.unlink(self.disk_usage_path)
        except OSError:
            pass

    def test_disk_usage_empty_if_file_not_present(self):
        disk_usage = self.provider.get_raw_stats()
        self.assertEqual({}, disk_usage)

    def test_disk_usage_getting_read_from_json_file(self):
        with open(self.disk_usage_path, 'w') as disk_usage_file:
            disk_usage_file.write(assets.load('disk-usage.json'))

        disk_usage = self.provider.get_raw_stats()
        self.assertEqual({'blobstorage': 45,
                          'filestorage': 20,
                          'total': 1024},
                         disk_usage)
