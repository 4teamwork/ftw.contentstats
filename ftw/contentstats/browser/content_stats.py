from plone import api
from zope.publisher.browser import BrowserView
import json


class ContentStats(BrowserView):
    """Displays content statistics.
    """

    def get_chart_js(self):
        data = self.get_type_counts()
        js_builder = ChartJSBuilder(data)
        return js_builder()

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


class ChartJSBuilder(object):
    """Build the JavaScript required to render a C3 Chart.
    """

    JS = """\
    var chart = c3.generate({
        data: {
            columns: %s,
            type : 'pie',
            legend: false
        }
    });

    $("#content-stats-type-counts tr")
        .on("mouseover", (event) => {
            chart.focus(event.currentTarget.dataset.id)
    });

    $("#content-stats-type-counts tr")
        .on("mouseout", (event) => {
            chart.focus();
    });

    $("#content-stats-type-counts tr")
        .each(function( index ) {
            var data_id = this.dataset.id;
            d3.select(this).selectAll('td .legend-color')
                .style('background-color', chart.color(data_id)
    )});

    chart.legend.hide;
    """

    def __init__(self, data):
        self.data = data

    def __call__(self):
        data_columns = json.dumps(self.data)
        return self.JS % data_columns
