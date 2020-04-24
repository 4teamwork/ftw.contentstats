from ftw.contentstats.stats import ContentStats
from zope.publisher.browser import BrowserView
import json


class ContentStatsView(BrowserView):
    """Displays content statistics.
    """

    VISUALIZED_STATS = (
        'portal_types',
        'review_states',
        'checked_out_docs',
        'file_mimetypes',
    )

    def data_url_for(self, stat_name):
        """Build the data URL for a particular stat.
        """
        base_url = '/'.join(
            (self.context.absolute_url(), 'content-stats-json?stat=%s'))
        return base_url % stat_name

    def get_visualized_stats(self):
        """Used in template to render chart containers for each stat.

        Limits the returned stats to ones we want to visualize.

        The actual *data* from these stats is only used in template to render
        the HTML table for graceful degradation - the actual charts fetch
        their data from the JSON view below.
        """
        stats = {}
        all_stats = ContentStats().get_human_readable_stats()

        # Filter out stats not marked for visualization and
        # inject respective data URL for each stat
        for name, stats_data in all_stats.items():
            if name not in self.VISUALIZED_STATS:
                continue

            stats_data['data_url'] = self.data_url_for(name)
            stats[name] = stats_data

        return stats.items()


class ContentStatsJSONView(BrowserView):
    """Return stats from a particular stats provider as JSON.

    Used to fetch data via data.url from the C3 charts. This will return the
    human readable representation of the stats.
    """

    def __call__(self):
        self.request.response.setHeader('Content-Type', 'application/json')

        stat_name = self.request.form.get('stat')
        all_stats = ContentStats().get_human_readable_stats()

        try:
            stats = all_stats[stat_name]
        except KeyError:
            self.request.response.setStatus(404)
            return json.dumps({})

        return json.dumps(stats['data'])
