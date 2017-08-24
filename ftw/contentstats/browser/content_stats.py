from zope.publisher.browser import BrowserView
from ftw.contentstats.stats import ContentStats
import json


class ContentStatsView(BrowserView):
    """Displays content statistics.
    """

    def __init__(self, context, request):
        super(ContentStatsView, self).__init__(context, request)
        self.content_stats = ContentStats().statistics()

    def get_type_counts_json(self):
        if self.__name__ == 'content-stats.json':
            self.request.response.setHeader('Content-Type', 'application/json')
        return json.dumps(self.content_stats)

    def get_all_statictics(self):
        return self.content_stats.items()

    def jsonify(self, data):
        return json.dumps(data)
