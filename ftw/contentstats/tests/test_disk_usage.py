from datetime import datetime
from ftw.contentstats.disk_usage import DiskUsageCalculator
from ftw.contentstats.tests import assets
from ftw.testing import freeze
from textwrap import dedent
from unittest import TestCase
import json


FROZEN_NOW = datetime(2018, 12, 30, 12, 45)


class TestDiskUsageCalculator(TestCase):

    def setUp(self):
        self.deployment_path = '/path/to/deployment'

    def test_parse_du_output_total(self):
        calculator = DiskUsageCalculator(self.deployment_path)
        output_total = dedent("""\
        1024   /path/to/deployment
        """)
        disk_usage = calculator.parse_du_output(output_total)
        self.assertEqual({'': 1024}, disk_usage)

    def test_parse_du_output_subtrees(self):
        calculator = DiskUsageCalculator(self.deployment_path)
        output_subtrees = dedent("""\
        5  /path/to/deployment/bin/instance
        10 /path/to/deployment/bin
        15 /path/to/deployment/var/log
        20 /path/to/deployment/var/filestorage/Data.fs
        25 /path/to/deployment/var/filestorage/Data.fs.index
        35 /path/to/deployment/var/blobstorage/0x00
        40 /path/to/deployment/var/blobstorage/tmp
        45 /path/to/deployment/var/blobstorage
        50 /path/to/deployment
        """)
        disk_usage = calculator.parse_du_output(output_subtrees)
        self.assertEqual({'': 50,
                          'bin': 10,
                          'bin/instance': 5,
                          'var/blobstorage': 45,
                          'var/blobstorage/0x00': 35,
                          'var/blobstorage/tmp': 40,
                          'var/filestorage/Data.fs': 20,
                          'var/filestorage/Data.fs.index': 25,
                          'var/log': 15},
                         disk_usage)

    def test_parse_du_output_strips_whitespace(self):
        calculator = DiskUsageCalculator(self.deployment_path)
        output_whitespace = """

        1024   /path/to/deployment/foo
        1024   \t\t/path/to/deployment/bar
        2048      /path/to/deployment\t

        """
        disk_usage = calculator.parse_du_output(output_whitespace)
        self.assertEqual({'': 2048,
                          'bar': 1024,
                          'foo': 1024},
                         disk_usage)

    def test_calc_du_total(self):
        calculator = DiskUsageCalculator(self.deployment_path)
        calculator.du_outputs['total'] = dedent("""\
        1024   /path/to/deployment
        """)
        disk_usage = calculator.calc_du_total()
        self.assertEqual(1024, disk_usage)

    def test_calc_du_subtrees(self):
        calculator = DiskUsageCalculator(self.deployment_path)
        calculator.du_outputs['subtrees'] = dedent("""\
        5  /path/to/deployment/bin/instance
        10 /path/to/deployment/bin
        15 /path/to/deployment/var/log
        20 /path/to/deployment/var/filestorage/Data.fs
        25 /path/to/deployment/var/filestorage/Data.fs.index
        35 /path/to/deployment/var/blobstorage/0x00
        40 /path/to/deployment/var/blobstorage/tmp
        45 /path/to/deployment/var/blobstorage
        50 /path/to/deployment
        """)
        disk_usage = calculator.calc_du_subtrees()

        # Should reduce subtree depth to 2 levels, except for var/filestorage/*
        self.assertEqual({'bin': 10,
                          'bin/instance': 5,
                          'var/blobstorage': 45,
                          'var/filestorage/Data.fs': 20,
                          'var/filestorage/Data.fs.index': 25,
                          'var/log': 15},
                         disk_usage)

    def test_calc_du_stats(self):
        calculator = DiskUsageCalculator(self.deployment_path)

        calculator.du_outputs['subtrees'] = dedent("""\
        5  /path/to/deployment/bin/instance
        10 /path/to/deployment/bin
        15 /path/to/deployment/var/log
        20 /path/to/deployment/var/filestorage/Data.fs
        25 /path/to/deployment/var/filestorage/Data.fs.index
        35 /path/to/deployment/var/blobstorage/0x00
        40 /path/to/deployment/var/blobstorage/tmp
        45 /path/to/deployment/var/blobstorage
        50 /path/to/deployment
        """)

        calculator.du_outputs['total'] = dedent("""\
        1024   /path/to/deployment
        """)

        with freeze(FROZEN_NOW):
            du_stats = calculator.calc_du_stats()

        # Should reduce subtree depth to 2 levels, except for var/filestorage/*
        self.assertEqual({'deployment': '/path/to/deployment',
                          'updated': FROZEN_NOW.isoformat(),
                          'total': 1024,
                          'subtrees': {'bin': 10,
                                       'bin/instance': 5,
                                       'var/blobstorage': 45,
                                       'var/filestorage/Data.fs': 20,
                                       'var/filestorage/Data.fs.index': 25,
                                       'var/log': 15},
                          },
                         du_stats)

        # Ensure the du_stats format matches our asset file which is also
        # used to test the provider. Since this is the interchange format
        # between the bin/dump-content-stats script that dumps it and the
        # @@dump-content-stats view that reads it, we need to make sure
        # these implementations stay in sync.
        asset = json.loads(assets.load('disk-usage.json'))
        self.assertEqual(asset, du_stats)
