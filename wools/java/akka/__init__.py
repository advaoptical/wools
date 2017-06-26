from alpakka import register_wool


WOOL = register_wool('akka', __name__, parent='java')

PARENT_WRAPPERS = WOOL.PARENT_YANG_NODE_WRAPPERS


class AkkaGrouping(PARENT_WRAPPERS['grouping']):
    pass
