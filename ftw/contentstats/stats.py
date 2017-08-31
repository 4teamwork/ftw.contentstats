from ftw.contentstats.interfaces import IStatsCollector
from zope.component import getAdapters
from zope.component.hooks import getSite


class ContentStats(object):
    """Gather content statistic from the Plone site.
    """

    def __init__(self):
        """This utility class requires a Plone site.
        """
        if not self.plone:
            raise Exception('Please setup a Plone site')

    @property
    def plone(self):
        """Get Plone site from globals
        """
        return getSite()

    def _all_adapters(self):

        return getAdapters((self.plone, self.plone.REQUEST),
                           IStatsCollector)

    def get_collector_names(self):
        """Get names of all registered collectors.
        """
        return [name for name, adapter_ in self._all_adapters()]

    def get_raw_stats(self):
        """Get a dictionary with raw stats from all registered collectors.

        This is the main API for accessing the machine readable representation
        of the collected stats.
        """
        stats = {}
        for name, collector in self._all_adapters():
            stats[name] = collector.get_raw_stats()
        return stats

    def get_stats_titles(self):
        """Get a name:title mapping for titles of all collectors.
        """
        titles = {}
        for name, collector in self._all_adapters():
            titles[name] = collector.title()
        return titles

    def get_stats_display_names(self):
        """Get a name:display_names mapping with display_names dicts of
        all collectors.

        If a collector returns None for its display_names mapping, this
        method substitutes it with an empty dict for easy processing below.
        """
        display_names = {}
        for name, collector in self._all_adapters():
            display_names[name] = {}
            names = collector.get_display_names()
            if names:
                display_names[name] = names
        return display_names

    def get_human_readable_stats(self):
        """Get a dictionary that combines all stats with their metadata.

        This includes stat titles as well as rewriting internal keys to
        display names. This is used in the template and JSON view, where
        a human readable representation is desired.
        """
        raw_stats = self.get_raw_stats()
        titles = self.get_stats_titles()
        display_names = self.get_stats_display_names()

        human_readable_stats = {}
        for stat_name in self.get_collector_names():
            stat_dict = {}
            stat_dict['title'] = titles[stat_name]
            stat_dict['data'] = {}

            # Rewrite internal keys to display names if necessary
            names = display_names.get(stat_name, {})
            for key, value in raw_stats[stat_name].items():
                # Try for a display name, default to key
                display_name = names.get(key, key)
                stat_dict['data'][display_name] = value

            human_readable_stats[stat_name] = stat_dict

        return human_readable_stats
