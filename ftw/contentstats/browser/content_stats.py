from zope.publisher.browser import BrowserView
from ftw.contentstats.stats import ContentStats
import json


class ContentStatsView(BrowserView):
    """Displays content statistics.
    """

    def __init__(self, context, request):
        super(ContentStatsView, self).__init__(context, request)
        self.type_counts = ContentStats().get_type_counts()

    def get_type_counts_for_table(self):
        return sorted(self.type_counts.items())

    def get_type_counts_json(self):
        return json.dumps(self.type_counts)
