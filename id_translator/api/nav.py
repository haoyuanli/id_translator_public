from flask_nav import Nav
from flask_nav.elements import NavigationItem
from flask_bootstrap.nav import BootstrapRenderer
from dominate import tags

nav = Nav()


class Alert(NavigationItem):
    """An item representing a JSAlert

    <div data-alerts="alerts"  data-ids="EXAMPLE-alert" data-usebullets=false></div>
    """

    def __init__(self, **attribs):
        self.attribs = attribs


class BSWithAlert(BootstrapRenderer):
    """
    BootstrapRenderer with the addition of an Alert tag
    """

    def visit_Alert(self, node):
        return tags.p(_class="navbar-text",
                      id="nav-alert",
                      data_alerts=node.attribs['alerts'],
                      data_ids=node.attribs['ids'])
