from alpakka import register_wool


WOOL = register_wool('Java', __name__)

PARENT_WRAPPERS = WOOL.PARENT_YANG_NODE_WRAPPERS


class JavaGrouping(PARENT_WRAPPERS['grouping']):
    pass
