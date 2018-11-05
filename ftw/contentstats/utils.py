from contextlib import closing
from os.path import abspath
from os.path import join
from path import Path
import re
import socket
import sys


# XXX: These helper functions have been copied over from ftw.upgrade
#
# Unfortunately there's no trivial way to get the port of a potentially
# running Zope instance without resorting to bin/instance [zopectl_command]
# style commands.
#
# And those pose an operational risk when invoked by a scheduled job, because
# they'll indefinitely keep trying to connect to ZEO instead of terminating
# when ZEO is not running. This leads to more and more processes accumulating,
# and the system eventually running out of file descriptors, memory or other
# resources.


class NoRunningInstanceFound(Exception):
    pass


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
