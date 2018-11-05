from distutils.spawn import find_executable
from ftw.contentstats.disk_usage import DiskUsageCalculator
from ftw.contentstats.utils import get_buildout_path
from ftw.contentstats.utils import get_zope_url
import argparse
import os
import requests
import sys


def parse_args():
    parser = argparse.ArgumentParser(
        description="""
            Dump content stats to logfile.

            Will dump content stats to logfile by making a request to
            the @@dump-content-stats view.

            Invoke this command on the same machine that a Plone site is
            running in order to have content stats dumped to the JSON logfile.
            """)
    parser.add_argument(
        '--site-id', '-s',
        help='Path to the Plone site.',
        required=True)

    args = parser.parse_args()
    return args


def renice():
    """Set CPU and I/O scheduling priorities so that this process
    (the bin/dump-content-stats script, not the Plone instances) run with
    lower priority and give way to other processes if required.
    """
    os.nice(10)
    ionice_path = find_executable('ionice')

    if ionice_path is None:
        print "Unable to find 'ionice' executable, skipping ionicing..."
        return

    # class 2: Best-effort, prio 7: lowest (in that class)
    ionice_cmd = '%s -c2 -n7 -p %s' % (ionice_path, os.getpid())
    os.system(ionice_cmd)


def dump_stats_cmd():
    """Will dump content stats to logfile via the @@dump-content-stats view.
    """
    args = parse_args()

    # Lower CPU and I/O scheduling priority
    renice()

    # Calculate disk usage stats and dump them to var/log/disk-usage.json
    deployment_path = get_buildout_path()
    DiskUsageCalculator(deployment_path).calc_and_dump()

    zope_url = get_zope_url()
    plone_url = ''.join((zope_url, args.site_id))
    dump_stats_url = '/'.join((plone_url, '@@dump-content-stats'))

    with requests.Session() as session:
        response = session.post(dump_stats_url)
        if response.status_code == 204:
            print "Stats dumped"
            sys.exit(0)

        else:
            print "Failed to dump stats:"
            print "Got response %r for URL %r" % (response, dump_stats_url)
            print
            print response.content
            print repr(response)
            sys.exit(1)
