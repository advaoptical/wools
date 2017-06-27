from alpakka import register_wool


WOOL = register_wool('Akka', __name__, parent='Java')

PARENT_WRAPPERS = WOOL.PARENT_YANG_NODE_WRAPPERS


class AkkaGrouping(PARENT_WRAPPERS['grouping']):
    pass
