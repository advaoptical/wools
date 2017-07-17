from alpakka import register_wool


WOOL = register_wool('Akka', __name__, parent='Java')


class AkkaGrouping(WOOL.parent['grouping']):
    pass
