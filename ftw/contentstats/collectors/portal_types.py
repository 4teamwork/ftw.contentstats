from ftw.contentstats.interfaces import IStatsCollector
from plone import api
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zope.component import adapter
from zope.i18n import translate
from zope.interface import implementer
from zope.interface import Interface


@implementer(IStatsCollector)
@adapter(IPloneSiteRoot, Interface)
class PortalTypesCollector(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def title(self):
        """Human readable title
        """
        return u'Portal type statistics'

    @property
    def get_type_title_mapping(self):
        """Return a id, title mapping of all portal types
        """
        portal_types = api.portal.get_tool('portal_types')
        ftis = portal_types.values()
        titles = [
            (fti.id, translate(
                fti.title, domain=fti.i18n_domain, context=self.request))
            for fti in ftis]
        return dict(titles)

    def get_statistic(self):
        """Return a list of dicts (keys: name, amount).
        """
        counts = {}
        catalog = api.portal.get_tool('portal_catalog')
        index = catalog._catalog.indexes['portal_type']
        for key in index.uniqueValues():
            t = index._index.get(key)
            title = self.get_type_title_mapping[str(key)]
            if not isinstance(t, int):
                counts[title] = len(t)
            else:
                counts[title] = 1
        return counts
