from alpakka import register_wool

WOOL = register_wool('Jersey', __name__, parent='Java')


class AkkaGrouping(WOOL.parent['grouping']):
    pass
