from zope.interface import Interface


class IStatsCollector(Interface):
    """Interface for StatsCollector adapter
    """

    def __init__(context, request):
        """Adapts context and request, context is usually a PloneSite"""

    def title():
        """Return a human readable title of the stats collector
        """

    def get_raw_stats():
        """Collect and return raw stats.

        Return value is a dict with key:value pairs, where key should be a
        stable, internal ID. If a different display name is desired, a mapping
        should be provided by implementing get_display_names().
        """

    def get_display_names():
        """Return a key: display_name mapping of human readable key names.

        If no alternate display names are needed, this should return None.
        """
