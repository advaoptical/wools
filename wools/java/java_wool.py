from alpakka import Wool
import configparser
import re

TYPE_PATTERNS = {
    (r"u?int\d*", "int"),
    (r"string", "String"),
    (r"boolean", "boolean"),
    (r"decimal64", "double"),
    (r"binary", "byte[]"),
    (r"empty", "Object"),
}


class JavaWool(Wool):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, type_patterns=TYPE_PATTERNS)

    def generate_output(self, module):
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
            if_name = '%sInterface' % module.java_name
            rpc_imports = {imp for rpc in module.rpcs.values()
                           if hasattr(rpc, 'imports')
                           for imp in rpc.imports()}
            for root in module.get_root_elements().values():
                for child in root.children.values():
                    if hasattr(child, 'keys'):
                        if module.yang_module().replace('-', '.') not in \
                                child.java_imports.imports:
                            rpc_imports.update(
                                child.java_imports.get_imports())
            rpc_dict = {'rpcs': module.rpcs,
                        'imports': rpc_imports,
                        'package': module.package(),
                        'path': module.subpath(),
                        'module': module}
            module.fill_template('backend_interface.jinja', {
                if_name: rpc_dict})
            rpc_dict['interface_name'] = if_name
            module.fill_template('backend_impl.jinja', {
                '%sBackend' % module.java_name: rpc_dict})
            module.fill_template('routes.jinja', {
                '%sRoutes' % module.java_name: rpc_dict})
        module.generate_pom('pom.jinja', module)

    def wrapping_postprocessing(self, module, wrapped_modules):
        """
        organizes and orchestrate the duplication check and the correct module
        organization

        :param module: module that postprocessing is applied to
        :param wrapped_modules: dictionary of all modules
        :return:
        """
        for name, child in set(module.classes.items()):
            original_module = child.statement.i_orig_module.arg
            if original_module != module.yang_module():
                if name in wrapped_modules[original_module].classes:
                    module.classes.pop(name)
                else:
                    wrapped_modules[original_module].classes[name] = child
                    module.classes.pop(name)

    def parse_config(self, path):
        """
        organizes and orchestrate the wool specific option and configuration
        handling

        :param path: the location of the config file
        :return:
        """
        config = configparser.ConfigParser()
        config.read(path)
        self.config = config['Wool']
        self.copyright = re.sub('wool_config.ini',
                                config['Wool']['copyright'],
                                path)
