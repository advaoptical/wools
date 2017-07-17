from alpakka import register_wool


WOOL = register_wool('Java', __name__)


class JavaGrouping(WOOL.parent['grouping']):
    pass
