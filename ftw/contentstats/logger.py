from App.config import getConfiguration
from datetime import datetime
from ftw.contentstats.stats import ContentStats
from logging import FileHandler
from logging import getLogger
from os.path import dirname
from os.path import join
from tzlocal import get_localzone
from zope.component.hooks import getSite
import json
import logging
import pytz


logger = getLogger('ftw.contentstats')

LOG_TZ = get_localzone()


def setup_logger():
    """Set up logger that writes to the JSON based logfile.

    May be invoked multiple times, and must therefore be idempotent.
    """
    if not logger.handlers:
        path = get_logfile_path()
        handler = FileHandler(path)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def get_logfile_path():
    """Determine the path for our JSON log.

    This will be derived from Zope2's EventLog location, in order to not
    have to figure out the path to var/log/ and the instance name ourselves.
    """
    zconf = getConfiguration()
    handler_factories = zconf.eventlog.handler_factories
    eventlog_path = handler_factories[0].section.path
    log_dir = dirname(eventlog_path)
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
