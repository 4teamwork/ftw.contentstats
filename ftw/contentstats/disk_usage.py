"""Contains functions to calculate disk usage stats of a deployment.

These are intended to be run from the bin/dump-content-stats script (outside
a Plone process), and write the resulting stats to var/log/disk-usage.json
in order to be picked up by the @@dump-content-stats view later.
"""

from datetime import datetime
from distutils.spawn import find_executable
from subprocess import check_output
import json
import os
import shlex
import sys


class DiskUsageCalculator(object):

    du_stats_path = 'var/log/disk-usage.json'

    def __init__(self, deployment_path):
        self.deployment_path = deployment_path
        self.du_executable = None

        # This facilitates testing without actually running `du`
        self.du_outputs = {}

    def calc_and_dump(self):
        """Calculate disk usage stats and dump them.

        Results will be written to a JSON file in var/log/ for pickup by the
        @@dump-content-stats view (we don't want to run I/O heavy and potentially
        long running jobs like this from inside a Zope instance).
        """
        self.du_executable = get_du_executable()
        if self.du_executable is None:
            print "No suitable `du` executable found, skipping disk usage"
            return

        du_stats = self.calc_du_stats()
        self.dump(du_stats)

    def calc_du_stats(self):
        """Determine disk usage (using `du`) for Data.fs and blobstorage.

        Returns a dictionary with separate keys for total deployment size and
        individual subtrees.
        """
        # Calculate an accurate total first
        disk_usage_total = self.calc_du_total()

        # Calculate size of individual subdirectories / files
        disk_usage_subtrees = self.calc_du_subtrees()

        du_stats = {}
        du_stats['deployment'] = self.deployment_path
        du_stats['updated'] = datetime.now().isoformat()
        du_stats['total'] = disk_usage_total
        du_stats['subtrees'] = disk_usage_subtrees
        return du_stats

    def calc_du_total(self):
        """Calculate an accurate total for the deployment directory.

        Sum up the size of the entire deployment directory, counting hardlinked
        files only once, and using actual FS block usage (not apparent size).
        This correctly reports the real disk usage of the deployment, accounting
        for hardlinks, sparse files and files smaller than the FS block size.

        Returns the total size in bytes as an integer.
        """
        if 'total' not in self.du_outputs:
            du_total_cmd = '%s -s -B1 %s' % (self.du_executable, self.deployment_path)
            self.du_outputs['total'] = self.run(du_total_cmd)

        disk_usage_total = self.parse_du_output(self.du_outputs['total'])

        # We have exactly one result line, the deployment directory itself
        assert disk_usage_total.keys() == ['']
        return disk_usage_total['']

    def calc_du_subtrees(self):
        """Calculate size of individual subdirectories / files in deployment dir.

        This is needed to report database size (Data.fs, blobstorage) without
        accounting for hardlinks. We actually want to count hardlinks twice,
        because otherwise we would be dependent on `du` counting blobstorage
        and blobstorage.old in exactly the right order.

        This listing might eventually also be used by agent.smith to replace
        the `du/big` command.
        """
        if 'subtrees' not in self.du_outputs:
            du_subtrees_cmd = '%s -x -a -B1 --count-links --apparent-size --max-depth=3 %s' % (
                self.du_executable, self.deployment_path)
            self.du_outputs['subtrees'] = self.run(du_subtrees_cmd)

        disk_usage_subtrees = self.parse_du_output(self.du_outputs['subtrees'])

        # Remove total, because it's inaccurate in this run
        disk_usage_subtrees.pop('')

        # Reduce subtree depth to 2, except for var/filestorage/*
        # (We need the size of Data.fs, which is 3 levels deep)
        for key in disk_usage_subtrees.keys():
            path = key.lstrip('/')
            if path.count(os.sep) > 1 and 'filestorage' not in path:
                disk_usage_subtrees.pop(key)
        return disk_usage_subtrees

    def parse_du_output(self, output):
        """Parse output of a 'du ...' command.

        Returns a dict (path -> size_in_bytes) with paths relative to the deployment
        directory.
        """
        disk_usage = {}
        lines = map(str.strip, output.strip().splitlines())
        for line in lines:
            size_in_bytes, path = map(str.strip, line.split())
            size_in_bytes = int(size_in_bytes)
            assert path.startswith(self.deployment_path)
            path = path.replace(self.deployment_path, '', 1).lstrip('/')
            disk_usage[path] = size_in_bytes

        return disk_usage

    def run(self, cmd):
        return check_output(shlex.split(cmd))

    def dump(self, du_stats):
        """Dump disk usage to file for pickup by @@dump-content-stats view
        (or, eventually, agent.smith)
        """
        du_stats_path = os.path.join(self.deployment_path, self.du_stats_path)
        with open(du_stats_path, 'w') as du_stats_file:
            json.dump(du_stats, du_stats_file)


def get_du_executable():
    """Get path to `du` (Linux) or `gdu` (Mac OS).

    The flags we need for `du` are not supported by the default *BSD-style
    `du` that is shipped with Mac OS. However, the GNU-style `du` can be
    installed on Mac OS (as `gdu`), so we attempt to look for it's presence.
    This way, the disk usage aspect can still be tested locally on Mac OS.
    """
    if sys.platform == 'darwin':
        du_executable = find_executable('gdu')
        if du_executable is None:
            print "WARNING: Unable to locate `gdu` executable."
            print
            print "Disk usage stats will not be computed."
            print
            print "If you want to test disk usage stats on Mac OS, you need"
            print "to install GNU coreutils to get the GNU-style du command"
            print "(installed as `gdu`):"
            print
            print "  brew install coreutils"
            print

        return du_executable

    else:
        du_executable = find_executable('du')
        return du_executable
