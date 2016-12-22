from plone import api
from zope.publisher.browser import BrowserView
import json


class ContentStats(BrowserView):
    """Displays content statistics.
    """

    def get_pie_chart(self):
        prefix = 'pie'
        data = self.get_type_counts()
        chart = ChartBuilder(data, prefix)
        return chart.render()

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


class ChartBuilder(object):
    """Build the JavaScript required to render a C3 Chart.
    """

    JS = """\
    var chart = c3.generate({
        bindto: '#%(chart_id)s',
        data: {
            columns: %(columns)s,
            type : 'pie',
            legend: false
        },
        size: {
            height: 360,
            width: 480
        },
        pie: {
            label: {
                format: function (value, ratio, id) {
                    return value;
                }
            }
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

    chart.legend.hide();
    """

    MARKUP = """\
    <div id="%(chart_id)s"></div>
    <script type="text/javascript">%(js)s</script>
    """

    def __init__(self, data, prefix):
        self.prefix = prefix
        self.chart_id = '%s-chart' % prefix
        self.data = data

    def render(self):
        data_columns = json.dumps(self.data)
        js = self.JS % dict(columns=data_columns, chart_id=self.chart_id)
        markup = self.MARKUP % dict(chart_id=self.chart_id, js=js)
        return markup
