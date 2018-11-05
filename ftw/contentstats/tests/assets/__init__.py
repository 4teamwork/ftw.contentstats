from pkg_resources import resource_filename
from pkg_resources import resource_string


def load(asset_filename):
    return resource_string('ftw.contentstats.tests.assets', asset_filename)


def path_to_asset(asset_filename):
    return resource_filename('ftw.contentstats.tests.assets', asset_filename)
