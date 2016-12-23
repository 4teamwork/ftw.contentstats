from plone import api
from zope.i18n import translate
from zope.publisher.browser import BrowserView
import json


class ContentStats(BrowserView):
    """Displays content statistics.
    """

    def get_type_titles(self):
        portal_types = api.portal.get_tool('portal_types')
        ftis = portal_types.values()
        titles = [
            (fti.id, translate(
                fti.title, domain=fti.i18n_domain, context=self.request))
            for fti in ftis]
        return dict(titles)

    def get_type_titles_json(self):
        return json.dumps(self.get_type_titles())

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

    def get_type_counts_json(self):
        return json.dumps(self.get_type_counts())
