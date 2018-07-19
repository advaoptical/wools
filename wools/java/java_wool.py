from pathlib import Path
from alpakka import Wool
from alpakka.logger import LOGGER
import configparser

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
        self.beans_only = False
        self.copyright = None
        self.prefix = ""
        self.iface_levels = 100

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
        if not self.beans_only:
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
                        'module': module,
                        'levels': self.iface_levels}
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
            orig_mod_name = child.statement.i_orig_module.arg
            if orig_mod_name != module.yang_module():
                orig_mod = wrapped_modules[orig_mod_name]
                if name in orig_mod.classes:
                    diff = orig_mod.class_difference(name, child)
                    if diff:
                        LOGGER.warn(
                            "Different attributes detected when merging "
                            "%s: %s", name, diff)
                else:
                    orig_mod.classes[name] = child
                module.classes.pop(name)

    def parse_config(self, path):
        """
        Loads the configuration from the given path and stores the values in
        the wool.

        :param path: location of the config file
        :return:
        """
        config = configparser.ConfigParser()
        config.read(path)
        ppath = Path(path).parent
        wool_config = config['Wool']
        self.beans_only = wool_config.getboolean("beans-only",
                                                 fallback=self.beans_only)
        if config.has_option('Wool', 'copyright'):
            # TODO: needs to be fixed for absolute and general relative paths
            self.copyright = str(ppath.joinpath(wool_config['copyright']))
        self.iface_levels = wool_config.getint('interface-levels',
                                               fallback=self.iface_levels)
        self.prefix = wool_config.get('prefix', fallback=self.prefix)
