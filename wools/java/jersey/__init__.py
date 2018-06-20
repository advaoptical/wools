from alpakka import register_wool

WOOL = register_wool('Jersey', __name__, parent='Java')


def generate_output(module):
    """
    organizes and orchestrate the class file generation

    :return:
    """
    WOOL.parent.generate_output(module)


def wrapping_postprocessing(module, wrapped_modules):
    """
    organizes and orchestrate the duplication check and the correct module
    organization

    :param wrapped_modules: dictionary of all modules
    :return:
    """
    WOOL.parent.wrapping_postprocessing(module, wrapped_modules)


def parse_config(module, path):
    """
    organizes and orchestrate the wool specific option and configuration
    handling

    :param module:
    :param path:
    :return:
    """
    WOOL.parent.parse_config(module, path)
