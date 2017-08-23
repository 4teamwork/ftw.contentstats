from plone import api
from zope.component.hooks import getSite
from zope.i18n import translate


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

    @property
    def get_type_title_mapping(self):
        """Return a id, title mapping of all portal types
        """
        portal_types = api.portal.get_tool('portal_types')
        ftis = portal_types.values()
        titles = [
            (fti.id, translate(
                fti.title, domain=fti.i18n_domain, context=self.plone.REQUEST))
            for fti in ftis]
        return dict(titles)

    def get_type_counts(self):
        """Return a list of (portal_type title, count) tuples.
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

        return sorted(counts.items())
