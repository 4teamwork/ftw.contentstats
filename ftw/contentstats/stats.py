from ftw.contentstats.interfaces import IStatsCollector
from zope.component import getAdapters
from zope.component.hooks import getSite


class ContentStats(object):
    """Gather content statistic from the plone site.plone.
    """

    def __init__(self):
        """ContentStats only works if there is a plone site.
        """
        if not self.plone:
            raise Exception('Please setup a plone site')

    @property
    def plone(self):
        """Get plone site from globals
        """
        return getSite()

    def _all_adapters(self):

        return getAdapters((self.plone, self.plone.REQUEST),
                           IStatsCollector)

    def get_collector_names(self):
        return [name for name, adapter_ in self._all_adapters()]

    def statistics(self):
        stats = {}
        for name, collector in self._all_adapters():
            stats[name] = dict(title=collector.title(),
                               data=collector.get_statistic())

        return stats
