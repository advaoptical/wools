from alpakka import register_wool


WOOL = register_wool('Akka', __name__, parent='Java')


class AkkaGrouping(WOOL.parent['grouping']):
    pass


def generate_output(wrapped_module):
    """
    organizes and orchestrate the class file generation

    :return:
    """
    WOOL.parent.generate_output(wrapped_module)