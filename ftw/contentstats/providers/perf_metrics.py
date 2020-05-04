from App.config import getConfiguration
from ftw.contentstats.interfaces import IStatsProvider
from ftw.contentstats.logger import root_logger as logger
from glob import glob
from os.path import basename
from os.path import join as pjoin
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
from ZServer.medusa.http_server import http_server
import json
import re
import socket


INSTANCE_NAME_PATTERN = re.compile(r'instance(\d+)')


@implementer(IStatsProvider)
@adapter(IPloneSiteRoot, Interface)
class PerformanceMetricsProvider(object):
    """Gathers performance metrics from ftw.monitor (if installed).
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def title(self):
        return u'Performance metrics'

    def get_raw_stats(self):
        """Return a dict with performance metrics.
        """
        stats = {}

        try:
            monitor_ports = get_monitor_ports(self.request)
        except Exception as exc:
            logger.warn('Failed to determine monitor ports: %r' % exc)
            return {}

        monitor_ports = get_monitor_ports(self.request)
        logger.info('Selected monitor ports for dumping perf_metrics: %r' % monitor_ports)
        for instance_name, monitor_port in monitor_ports.items():
            try:
                reply = netcat('127.0.0.1', monitor_port,
                               'perf_metrics\n').strip()
                instance_metrics = json.loads(reply)
                stats[instance_name] = instance_metrics
            except Exception as exc:
                logger.warn('Failed to gather perf_metrics from %s: %r' % (instance_name, exc))

        return stats

    def get_display_names(self):
        return None


def get_monitor_ports(request):
    """Get a list of open ftw.monitor ports for instances of this deployment.

    This will:
    - Determine which bin/instance* scripts belong to this deployment
    - Determine the instance numbers from them
    - Determine the port base via the ZServer port of the current instance
    - Build the map of monitor ports by instance by doing port arithmetic:
      monitor_port = port base + instance number + 80
      (According to 4tw port schema and ftw.monitor port strategy)
    """
    config = getConfiguration()
    instance_scripts = get_instance_scripts(config)
    instance_names = get_instance_names(instance_scripts)

    zserver_port = get_zserver_port(config)
    if zserver_port == 8080:
        # Local development
        return {'instance': 8160}

    port_base = get_port_base(zserver_port)

    monitor_ports_by_instance = {}
    for name in instance_names:
        if name in ('instance0', 'instance'):
            # Ignore maintenance or development instances
            continue

        number = get_instance_number(name)
        if number:
            monitor_port = port_base + number + 80
            monitor_ports_by_instance[name] = monitor_port

    return monitor_ports_by_instance


def get_buildout_dir(config):
    buildout_dir = config.instancehome.partition('/parts/')[0]
    return buildout_dir


def get_instance_scripts(config):
    buildout_dir = get_buildout_dir(config)
    bin_dir = pjoin(buildout_dir, 'bin')
    instance_scripts = glob(pjoin(bin_dir, 'instance*'))
    return instance_scripts


def get_instance_names(instance_scripts):
    return [basename(path) for path in instance_scripts]


def get_instance_number(instance_name):
    match = INSTANCE_NAME_PATTERN.match(instance_name)
    if match:
        number = int(match.group(1))
        return number


def get_zserver_port(config):
    zservers = [
        server for server in config.servers
        if isinstance(server, http_server)
    ]

    zserver_ports = [zs.port for zs in zservers]

    assert len(zserver_ports) == 1
    zserver_port = zserver_ports[0]
    return zserver_port


def get_port_base(zserver_port):
    return int(str(zserver_port)[:-2] + '00')


def netcat(hostname, port, content):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((hostname, port))
    s.sendall(content)

    result = ''
    while 1:
        data = s.recv(1024)
        if data == '':
            break
        result += data
    s.close()
    return result
