from plone import api
from zope.publisher.browser import BrowserView


class ContentStats(BrowserView):
    """Displays content statistics.
    """

    def get_type_counts(self):
        """Return a list of (portal_type, count) tuples.
        """
        counts = {}
        catalog = api.portal.get_tool('portal_catalog')
        index = catalog._catalog.indexes['portal_type']
        for key in index.uniqueValues():
            t = index._index.get(key)
            if not isinstance(t, int):
                counts[str(key)] = len(t)
            else:
                counts[str(key)] = 1
        return sorted(counts.items())
