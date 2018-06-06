from alpakka import register_wool

WOOL = register_wool('Jersey', __name__, parent='Java')


def generate_output(wrapped_module):
    """
    organizes and orchestrate the class file generation

    :return:
    """
    WOOL.parent.generate_output(wrapped_module)


def clear_data_structure(wrapped_modules, module):
    """
    organizes and orchestrate the duplication check and the correct module
    organization

    :param wrapped_modules: dictionary of all modules
    :return:
    """
    WOOL.parent.clear_data_structure(wrapped_modules, module)