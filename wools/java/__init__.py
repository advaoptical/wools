from alpakka import register_wool

import logging
import configparser

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

WOOL = register_wool('Java', __name__, data_type_patterns={
    (r"u?int\d*", "int"),
    (r"string", "String"),
    (r"boolean", "boolean"),
    (r"decimal64", "double"),
    (r"binary", "byte[]"),
    (r"empty", "Object"),
}, options=['prefix', 'beans-only', 'interface-levels'])

PARENT = WOOL.parent

from wools.java.javanodewrapper import JavaNodeWrapper
from wools.java.javagrouponder import JavaGrouponder
from wools.java.javatyponder import JavaTyponder


def generate_output(module):
    """
    organizes and orchestrate the class file generation

    :return:
    """
    # generate enum classes
    module.fill_template('enum_type.jinja', module.enums())
    # generate class extensions
    module.fill_template('class_extension.jinja', module.types())
    # generate base class extensions
    module.fill_template('class_type.jinja', module.base_extensions())
    # generate classes
    module.fill_template('grouping.jinja', module.classes)
    # generate unions
    module.fill_template('union.jinja', module.unions())
    if not module.beans_only:
        # generate empty xml_config template for NETCONF use
        # module.fill_template('empty_config.jinja',
        #                    {'empty_XML_config': module})
        # run only if rpcs are available
        # if module.rpcs:
        if_name = '%sInterface' % module.java_name
        rpc_imports = {imp for rpc in module.rpcs.values()
                       if hasattr(rpc, 'imports')
                       for imp in rpc.imports()}
        for root in module.get_root_elements().values():
            for child in root.children.values():
                if hasattr(child, 'keys'):
                    if module.yang_module().replace('-', '.') not in \
                            child.java_imports.imports:
                        rpc_imports.update(child.java_imports.get_imports())

        rpc_dict = {'rpcs': module.rpcs,
                    'imports': rpc_imports,
                    'package': module.package(),
                    'path': module.subpath(),
                    'module': module}
        module.fill_template('backend_interface.jinja',
                           {if_name: rpc_dict})
        rpc_dict['interface_name'] = if_name
        module.fill_template('backend_impl.jinja',
                           {'%sBackend' % module.java_name: rpc_dict})
        module.fill_template('routes.jinja',
                           {'%sRoutes' % module.java_name: rpc_dict})
    module.generate_pom('pom.jinja', module)


def wrapping_postprocessing(module, wrapped_modules):
    """
    organizes and orchestrate the duplication check and the correct module
    organization

    :param wrapped_modules: dictionary of all modules
    :return:
    """
    for name, child in set(module.classes.items()):
        if child.statement.i_orig_module.arg != module.yang_module():
            if name in wrapped_modules[child.statement.i_orig_module.arg].classes:
                module.classes.pop(name)
            else:
                wrapped_modules[child.statement.i_orig_module.arg].classes[name] = child
                module.classes.pop(name)


def parse_config(module, path):
    """
    organizes and orchestrate the wool specific option and configuration
    handling

    :param module:
    :param path:
    :return:
    """
    location = path
    config = configparser.ConfigParser()
    config.read(location)
    module.config = config['Wool']