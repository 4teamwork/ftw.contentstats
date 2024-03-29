from ftw.contentstats.interfaces import IStatsProvider
from ftw.contentstats.logger import get_log_dir_path
from logging import getLogger
from os.path import join
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
import json


log = getLogger()


@implementer(IStatsProvider)
@adapter(IPloneSiteRoot, Interface)
class DiskUsageProvider(object):
    """Reads disk usage statistics from a file in var/log/disk-usage.json.

    This file gets created/updated by the bin/dump-content-stats script.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def title(self):
        """Human readable title
        """
        return u'Disk usage statistics'

    def get_raw_stats(self):
        """Returns a dict with disk usage stats.
        """
        log_dir = get_log_dir_path()
        path = join(log_dir, 'disk-usage.json')
        try:
            with open(path) as disk_usage_file:
                disk_usage = json.load(disk_usage_file)
        except IOError:
            log.warn('Unable to read disk usage stats from %r' % path)
            return {}

        stats = {}
        stats['total'] = disk_usage['total']
        stats['filestorage'] = disk_usage['filestorage']
        stats['blobstorage'] = disk_usage['blobstorage']
        return stats

    def get_display_names(self):
        return None
