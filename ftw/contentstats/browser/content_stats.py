from datetime import datetime
from DateTime import DateTime
from dateutil.relativedelta import relativedelta
from plone import api
from zope.i18n import translate
from zope.publisher.browser import BrowserView
import json


class ContentStats(BrowserView):
    """Displays content statistics.
    """

    def get_portal_types(self):
        portal_types = api.portal.get_tool('portal_types')
        return portal_types.objectIds()

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

    def calc_historical_creations(self):
        catalog = api.portal.get_tool('portal_catalog')
        buckets = {}
        now = datetime.now() + relativedelta(minutes=1)
        for m in range(0, 6):
            end = now - relativedelta(months=m)
            start = now - relativedelta(months=(m + 1))
            date_range = {
                'query': (
                    DateTime(start),
                    DateTime(end),
                ),
                'range': 'min:max',
            }

            buckets[end.strftime('%Y-%m')] = {}
            for portal_type in self.get_portal_types():
                brains = catalog.unrestrictedSearchResults(
                    created=date_range, portal_type=portal_type)
                buckets[end.strftime('%Y-%m')][portal_type] = len(brains)

        return buckets

    def get_historical_creations(self):
        buckets = self.calc_historical_creations()

        creations_by_type = {}
        months, creations = buckets.keys(), buckets.values()
        months = ['x'] + ['%s-01' % m for m in months]
        for monthly_creations in creations:
            for portal_type in monthly_creations.keys():
                if portal_type not in creations_by_type:
                    creations_by_type[portal_type] = []
                creations_by_type[portal_type].append(
                    monthly_creations[portal_type])

        columns = [months]
        for key, value in creations_by_type.items():
            columns.append([key] + value)
        return columns

    def get_historical_creations_json(self):
        return json.dumps(self.get_historical_creations())
