from plone import api
from zope.i18n import translate
from zope.publisher.browser import BrowserView
import json


class ContentStats(BrowserView):
    """Displays content statistics.
    """

    def get_pie_chart(self):
        prefix = 'pie'
        data = self.get_type_counts()
        titles = self.get_type_titles()
        chart = ChartBuilder(data, titles, prefix)
        return chart.render()

    def get_type_titles(self):
        portal_types = api.portal.get_tool('portal_types')
        ftis = portal_types.values()
        titles = [
            (fti.id, translate(
                fti.title, domain=fti.i18n_domain, context=self.request))
            for fti in ftis]
        return dict(titles)

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
            names: %(names)s,
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

    def __init__(self, data, titles, prefix):
        self.data = data
        self.titles = titles
        self.prefix = prefix
        self.chart_id = '%s-chart' % prefix

    def render(self):
        data_columns = json.dumps(self.data)
        data_names = json.dumps(self.titles)
        js = self.JS % dict(
            columns=data_columns, names=data_names, chart_id=self.chart_id)
        markup = self.MARKUP % dict(chart_id=self.chart_id, js=js)
        return markup
