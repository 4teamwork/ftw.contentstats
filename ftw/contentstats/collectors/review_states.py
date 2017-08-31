from ftw.contentstats.interfaces import IStatsCollector
from plone import api
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(IStatsCollector)
@adapter(IPloneSiteRoot, Interface)
class ReviewStatesCollector(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def title(self):
        """Human readable title
        """
        return u'Review state statistics'

    def get_statistic(self):
        """Return a list of dicts (keys: name, amount).
        """
        counts = {}
        catalog = api.portal.get_tool('portal_catalog')
        index = catalog._catalog.indexes['review_state']
        for key in index.uniqueValues():
            t = index._index.get(key)
            if not isinstance(t, int):
                counts[key] = len(t)
            else:
                counts[key] = 1
        return counts
