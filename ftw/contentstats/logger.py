from App.config import getConfiguration
from datetime import datetime
from fluent.asynchandler import FluentHandler
from fluent.handler import FluentRecordFormatter
from ftw.contentstats.stats import ContentStats
from logging import FileHandler
from logging import getLogger
from os.path import dirname
from os.path import join
from tzlocal import get_localzone
from zope.component.hooks import getSite
import json
import logging
import os
import pytz


logger = getLogger('ftw.contentstats')
root_logger = logging.root

LOG_TZ = get_localzone()


def setup_logger():
    """Set up logger that writes to a JSON logfile or a Fluentd instance.

    May be invoked multiple times, and must therefore be idempotent.
    """
    if not logger.handlers:
        fluent_host = os.environ.get('FLUENT_HOST')
        fluent_port = int(os.environ.get('FLUENT_PORT', 24224))

        if fluent_host:
            setup_fluent_handler(fluent_host, fluent_port)
        else:
            setup_jsonfile_handler()

        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger


def setup_fluent_handler(fluent_host, fluent_port):
    """Set up handler that writes to a Fluentd / Fluent Bit instance.
    """
    tag = 'contentstats-json.log'
    ns = os.environ.get('KUBERNETES_NAMESPACE')
    if ns:
        tag = '-'.join((ns, tag))

    handler = FluentHandler(tag, fluent_host, fluent_port)
    handler.setFormatter(FluentRecordFormatter())
    logger.addHandler(handler)
    return logger


def setup_jsonfile_handler():
    """Set up handler that writes to the JSON based logfile.
    """
    path = get_logfile_path()
    if path is not None:
        handler = FileHandler(path)
        logger.addHandler(handler)
    return logger


def get_log_dir_path():
    """Determine the path of the deployment's var/log/ directory.

    This will be derived from Zope2's EventLog location, in order to not
    have to figure out the path to var/log/ ourselves from buildout.
    """
    zconf = getConfiguration()
    eventlog = getattr(zconf, 'eventlog', None)
    if eventlog is None:
        root_logger.error('')
        root_logger.error(
            "ftw.contentstats: Couldn't find eventlog configuration in order "
            "to determine logfile location!")
        root_logger.error(
            "ftw.contentstats: No content stats logfile will be written!")
        root_logger.error('')
        return None

    handler_factories = eventlog.handler_factories
    eventlog_path = handler_factories[0].section.path
    log_dir = dirname(eventlog_path)
    return log_dir


def get_logfile_path():
    """Determine the path for our JSON log.
    """
    log_dir = get_log_dir_path()
    path = join(log_dir, 'contentstats-json.log')
    return path


def log_stats_to_file():
    logger = setup_logger()

    stats = ContentStats().get_raw_stats()

    ts = datetime.utcnow().replace(tzinfo=pytz.utc)
    stats['timestamp'] = ts.astimezone(LOG_TZ).isoformat()
    stats['site'] = get_site_id()

    logger.info(json.dumps(stats, sort_keys=True))


def get_site_id():
    site = getSite()
    if site:
        return site.id
    return ''
