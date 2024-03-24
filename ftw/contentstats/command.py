from ftw.contentstats.disk_usage import DiskUsageCalculator
from ftw.contentstats.logger import log_stats_to_file
from zope.component.hooks import setSite
import App.config
import argparse
import os.path
import sys


def get_deployment_path():
    cfg = App.config._config
    return os.path.normpath(os.path.join(cfg.clienthome, '..', '..'))


def dump_content_stats(app, args):
    parser = argparse.ArgumentParser(description="Dump content stats.")
    parser.add_argument(
        '--site-path', '-s',
        help='Path to the Plone site.',
        default=None,
    )
    parser.add_argument(
        '--python-du',
        help='Use Python implementation for disk usage calculation.',
        action='store_true',
    )
    parser.add_argument(
        '--data-path', '-d',
        help='Path to data directory for which to calculate disk usage.',
        default=None,
    )

    if sys.argv[0] != 'dump_content_stats':
        args = args[2:]
    options = parser.parse_args(args)

    deployment_path = get_deployment_path()
    DiskUsageCalculator(
        deployment_path,
        use_du_util=not options.python_du,
        data_path=options.data_path,
    ).calc_and_dump()

    site = setup_site(app, options)
    if site is None:
        sys.exit(1)

    log_stats_to_file()


def get_site(app, options):
    if options.site_path:
        return app.unrestrictedTraverse(options.site_path)
    else:
        sites = []
        for item in app.values():
            if item.meta_type == 'Plone Site':
                sites.append(item)

        if len(sites) == 1:
            return sites[0]
        elif len(sites) > 1:
            print('ERROR: Multiple Plone sites found. Use -s to specify site.')
        else:
            print('ERROR: No Plone site found.')


def setup_site(app, options):
    # Delay import of the Testing module
    # Importing it before the database is opened, will result in opening a
    # DemoStorage database instead of the one from the config file.
    from Testing.makerequest import makerequest  # noqa
    app = makerequest(app)
    site = get_site(app, options)
    if site is not None:
        setSite(site)
    return site
