from contextlib import closing
from distutils.spawn import find_executable
from os.path import abspath
from os.path import join
from path import Path
import argparse
import os
import re
import requests
import socket
import sys


class NoRunningInstanceFound(Exception):
    pass


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
    renice()

    args = parse_args()
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


# XXX: These helper functions have been copied over from ftw.upgrade
#
# Unfortunately there's no trivial way to get port of a potentially
# running Zope instance without resorting to bin/instance [zopectl_command]
# style commands.
#
# And those pose an operational risk when invoked by a scheduled job, because
# they'll indefinitely keep trying to connect to ZEO instead of terminating
# when ZEO is not running. This leads to more and more processes accumulating,
# and the system eventually running out of file descriptors, memory or other
# resources.


def get_buildout_path():
    # Path to bin/dump-content-stats script
    script_path = sys.argv[0]
    return Path(abspath(join(script_path, '..', '..')))


def get_zope_url():
    instance = get_running_instance(get_buildout_path())
    if not instance:
        raise NoRunningInstanceFound()
    return 'http://localhost:{0}/'.format(instance['port'])


def get_running_instance(buildout_path):
    for zconf in find_instance_zconfs(buildout_path):
        port = get_instance_port(zconf)
        if not port:
            continue
        if is_port_open(port):
            return {'port': port,
                    'path': zconf.dirname().dirname()}
    return None


def find_instance_zconfs(buildout_path):
    return sorted(buildout_path.glob('parts/*/etc/zope.conf'))


def get_instance_port(zconf):
    match = re.search(r'address ([\d.]*:)?(\d+)', zconf.text())
    if match:
        return int(match.group(2))
    return None


def is_port_open(port):
    result = -1
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        result = sock.connect_ex(('127.0.0.1', port))
    return result == 0
