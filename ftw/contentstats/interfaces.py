from zope.interface import Interface


class IStatsCollector(Interface):
    """Interface for StatsCollector adapter
    """

    def __init__(context, request):
        """Adapts context and request, context is usually a PloneSite"""

    def title():
        """Return a human readable title of the stats collector
        """

    def get_statistic():
        """Collect stats informations.
        Return value is a dict with label as key and amount as value.
        """
