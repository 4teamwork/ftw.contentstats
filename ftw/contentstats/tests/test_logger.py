from contextlib import contextmanager
from datetime import timedelta
from fluent.asynchandler import FluentHandler
from freezegun import freeze_time
from ftw.builder import Builder
from ftw.builder import create
from ftw.contentstats.logger import get_log_dir_path
from ftw.contentstats.logger import log_stats_to_file
from ftw.contentstats.logger import setup_logger
from ftw.contentstats.testing import clear_log_handlers
from ftw.contentstats.testing import FTW_MONITOR_INSTALLED
from ftw.contentstats.testing import PatchedLogTZ
from ftw.contentstats.tests import assets
from ftw.contentstats.tests import FunctionalTestCase
from logging import FileHandler
from mock import patch
from operator import itemgetter
from os.path import join
import json
import os


@contextmanager
def env_var(name, value):
    assert name not in os.environ, \
        'Unexpectedly found the variable {} in the environment.'.format(name)
    os.environ[name] = value
    try:
        yield
    finally:
        os.environ.pop(name)


class TestLogging(FunctionalTestCase):

    def setUp(self):
        super(TestLogging, self).setUp()
        clear_log_handlers()
        log_dir = get_log_dir_path()
        self.disk_usage_path = join(log_dir, 'disk-usage.json')

    def tearDown(self):
        super(TestLogging, self).tearDown()
        try:
            os.unlink(self.disk_usage_path)
        except OSError:
            pass

    def create_content(self):
        self.set_workflow_chain('Document', 'simple_publication_workflow')
        self.set_workflow_chain('Folder', 'simple_publication_workflow')
        create(Builder('folder'))
        create(Builder('page'))
        create(Builder('page')
               .in_state('published'))

    def test_logs_raw_stats(self):
        self.grant('Contributor')
        self.create_content()
        self.grant('Anonymous')

        with open(self.disk_usage_path, 'w') as disk_usage_file:
            disk_usage_file.write(assets.load('disk-usage.json'))

        log_stats_to_file()
        log_entry = self.get_log_entries()[-1]

        expected_stats_names = [
            'site',
            'timestamp',
            'disk_usage',
            'portal_types',
            'review_states',
        ]

        if FTW_MONITOR_INSTALLED:
            expected_stats_names.append('perf_metrics')

        self.assertItemsEqual(expected_stats_names, log_entry.keys())

        self.assertEquals(
            {u'Folder': 1, u'Document': 2},
            log_entry['portal_types'])

        self.assertEquals(
            {u'private': 2, u'published': 1},
            log_entry['review_states'])

        self.assertEquals(
            {u'blobstorage': 45,
             u'filestorage': 20,
             u'total': 1024},
            log_entry['disk_usage'])

    def test_log_multiple_entries(self):
        # Frozen time is specified in UTC
        # tz_offset specifies what offset to UTC the local tz is supposed to
        # have. This is relevant for stdlib functions that return local times,
        # but *not* for ftw.contentstats, since we never fetch local times
        with freeze_time("2017-07-29 10:30:58.000750", tz_offset=7) as clock:
            with PatchedLogTZ('Europe/Zurich'):
                log_stats_to_file()
                clock.tick(timedelta(days=1))
                log_stats_to_file()

        log_entries = self.get_log_entries()

        self.assertEquals(2, len(log_entries))
        self.assertEquals(
            [u'2017-07-29T12:30:58.000750+02:00',
             u'2017-07-30T12:30:58.000750+02:00'],
            map(itemgetter('timestamp'), log_entries))

    def test_logs_plone_site_id(self):
        log_stats_to_file()
        log_entry = self.get_log_entries()[0]

        self.assertEquals(u'plone', log_entry['site'])

    def test_dst_rollover(self):
        # Start in winter (no DST), half an hour before switch to DST, which
        # will happen at 2017-03-26 01:00:00 UTC / 2017-03-26 02:00:00 CET
        # for Europe/Zurich
        with freeze_time("2017-03-26 00:30:00.000750", tz_offset=7) as clock, \
                PatchedLogTZ('Europe/Zurich'):
            log_stats_to_file()

            # No DST (winter) - UTC offset for Europe/Zurich should be +01:00
            log_entry = self.get_log_entries()[-1]
            self.assertEqual(u'2017-03-26T01:30:00.000750+01:00',
                             log_entry['timestamp'])

            # Forward one hour - rollover from winter to summer, it's now DST
            clock.tick(timedelta(hours=1))
            log_stats_to_file()

            # DST (summer) - UTC offset for Europe/Zurich should be +02:00,
            # and we "magically" skipped the hourd from 02:00 - 03:00
            log_entry = self.get_log_entries()[-1]
            self.assertEqual(u'2017-03-26T03:30:00.000750+02:00',
                             log_entry['timestamp'])

            # Fast forward to October, half an hour before end of DST
            clock.move_to("2017-10-29 00:30:00.000750")
            log_stats_to_file()

            # We're still just in DST (summer) - UTC offset for
            # Europe/Zurich should be +02:00
            log_entry = self.get_log_entries()[-1]
            self.assertEqual(u'2017-10-29T02:30:00.000750+02:00',
                             log_entry['timestamp'])

            # Forward one hour - rollover from summer to winter, DST ends
            clock.tick(timedelta(hours=1))
            log_stats_to_file()

            # No DST (winter) - UTC offset for Europe/Zurich should be +01:00,
            # and it's now "magically" 02:30 again, even though an hour passed
            log_entry = self.get_log_entries()[-1]
            self.assertEqual(u'2017-10-29T02:30:00.000750+01:00',
                             log_entry['timestamp'])


class TestFluentLogging(FunctionalTestCase):

    @patch('fluent.handler.FluentHandler.emit')
    def test_dispatches_to_fluentd(self, mock_emit):
        clear_log_handlers()

        with env_var('FLUENT_HOST', 'localhost'):
            log_stats_to_file()

        self.assertEqual(1, mock_emit.call_count)
        log_record = mock_emit.call_args[0][0]

        expected_stats_names = [
            'site',
            'timestamp',
            'disk_usage',
            'portal_types',
            'review_states',
        ]

        if FTW_MONITOR_INSTALLED:
            expected_stats_names.append('perf_metrics')

        self.assertItemsEqual(
            expected_stats_names,
            json.loads(log_record.msg).keys())

    @patch('ftw.contentstats.logger.get_logfile_path')
    def test_sets_up_file_handler_by_default(self, mocked_logpath):
        mocked_logpath.return_value = '/tmp/logfile'
        clear_log_handlers()

        logger = setup_logger()

        self.assertEqual(1, len(logger.handlers))
        handler = logger.handlers[0]
        self.assertIsInstance(handler, FileHandler)
        self.assertEqual('/tmp/logfile', handler.stream.name)

    @patch('ftw.contentstats.logger.get_logfile_path')
    def test_sets_up_fluent_handler_if_envvar_set(self, mocked_logpath):
        # Mock the presence of a possible log file path in order to test that
        # even if one could be determined, setup_logger() *doesn't* set up
        # a FileHandler if FLUENT_HOST is set.
        mocked_logpath.return_value = '/tmp/logfile'

        clear_log_handlers()

        with env_var('FLUENT_HOST', 'localhost'):
            logger = setup_logger()

        self.assertEqual(1, len(logger.handlers))
        handler = logger.handlers[0]
        self.assertIsInstance(handler, FluentHandler)

    def test_sets_up_tag_including_ns_for_fluent_handler(self):
        clear_log_handlers()

        with env_var('FLUENT_HOST', 'localhost'):
            with env_var('KUBERNETES_NAMESPACE', 'demo-example-org'):
                logger = setup_logger()

        self.assertEqual(1, len(logger.handlers))
        handler = logger.handlers[0]
        self.assertEqual('demo-example-org-contentstats-json.log', handler.tag)

    def test_sets_up_fallback_tag_for_fluent_handler(self):
        clear_log_handlers()

        with env_var('FLUENT_HOST', 'localhost'):
            logger = setup_logger()

        self.assertEqual(1, len(logger.handlers))
        handler = logger.handlers[0]
        self.assertEqual('contentstats-json.log', handler.tag)
