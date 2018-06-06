from alpakka.wrapper.nodewrapper import NodeWrapper
from alpakka.templates import template_var
from collections import OrderedDict

from . import utils as ju
from . import PARENT

from jinja2 import Environment, PackageLoader

import logging
import os
import re


class JavaBaseType:
    """
    Wrapper class for a java base types, like boolean, double, int and String.
    """

    def __init__(self, data_type):
        self.java_imports = ju.ImportDict()
        self.java_type = data_type
        # is a cast needed to use hashCode
        self.java_cast = ju.JAVA_WRAPPER_CLASSES.get(self.java_type, None)
        self.group = 'base'
        self.is_base = True


class JavaNodeWrapper:

    def __init__(self, *args):
        super().__init__(*args)

    @template_var
    def package(self):
        """
        The pakackage name of this module.
        :return: the package name
        """
        return ju.to_package(self.yang_module(), self.top().prefix)

    @template_var
    def subpath(self):
        """
        The subpath of this module.
        :return: the package name
        """
        if self.top().prefix:
            return '%s/%s' % (self.top().prefix.replace(".", "/"),
                              self.yang_module().lower().replace("-", "/"))
        else:
            return self.yang_module().lower().replace("-", "/")

    @template_var
    def collect_keys(self, only_parents=False):
        """
        Collects the list keys all the way up through the hierarchy.

        :param only_parents: flag that decides if the own keys are skipped
        :return: list of keys
        """
        result = self.parent and self.parent.collect_keys() or []
        if not only_parents:
            result += getattr(self, 'keys', ())
        return result

    def generate_java_type(self):

        if self.is_augmented:
            java_type = self.generate_java_key()
        else:
            java_type = ju.java_class_name(self.yang_name())
            if java_type in self.top().classes.keys():
                twin = self.top().classes[java_type]
                if self.yang_type() != twin.yang_type():
                    java_type = java_type + 'Top'

        return java_type

    def generate_java_key(self):

        key = ''
        if self.parent.parent:
            key = self.parent.generate_java_key()
        if key:
            return key + ju.java_class_name(self.yang_name())
        else:
            return ju.java_class_name(self.yang_name())


class JavaModule(JavaNodeWrapper, PARENT['module']):

    def __init__(self, statement, parent=None):
        self.classes = OrderedDict()
        self.rpcs = OrderedDict()
        self.typedefs = OrderedDict()
        self.prefix = self.WOOL.config['prefix']
        self.beans_only = self.WOOL.config['beans-only']
        self.java_name = ju.java_class_name(statement.i_prefix)

        self.output_path = self.WOOL.output_path
        # variables for output generation
        path = '/templates'
        item = self.WOOL
        while item.name != 'default':
            path = '/' + item.name[0].lower() + item.name[1:] + path
            item = item.parent
        self.env = Environment(loader=PackageLoader('wools', path))
        # add filters to environment
        self.env.filters['firstupper'] = ju.firstupper
        self.env.filters['firstlower'] = ju.firstlower
        self.env.filters['javadefault'] = ju.java_default

        super(JavaModule, self).__init__(statement, parent)

    @template_var
    def enums(self):
        """
        Extracts the enumeration definitions from the typedefs.

        :return: dictionary of enums
        """
        return {name: data for name, data in self.typedefs.items()
                if data.type.group == 'enum'}

    @template_var
    def base_extensions(self):
        """
        Extracts extension of base types from the typedefs.

        :return: dictionary of base type extensions
        """
        return {name: data for name, data in self.typedefs.items()
                if data.type.group == 'base'}

    @template_var
    def types(self):
        """
        Extracts extension of defined types from the typedefs.

        :return: dictionary of type extensions
        """
        return {name: data for name, data in self.typedefs.items()
                if data.type.group == 'type'}

    @template_var
    def unions(self):
        """
        Extracts all unions from the typedefs.

        :return:  dictionary of unions
        """
        return {name: data for name, data in self.typedefs.items()
                if data.type.group == 'union'}

    @template_var
    def rpc_imports(self):
        return {imp for _, data in getattr(self, 'rpcs', {}).items()
                for imp in getattr(data, 'imports', ())}

    @template_var
    def group_id(self):
        result = ju.to_camelcase(self.yang_name())
        result = result[0].upper() + result[1:]
        return result

    @template_var
    def get_root_elements(self):
        result = dict()
        for name, child in self.children.items():
            if child.yang_type() not in ju.JAVA_FORBIDDEN_ROOTS:
                result[name] = child
        return result

    def add_class(self, class_name, wrapped_description):
        """
        Add a class to the collection that needs to be generated.

        :param class_name: the class name to be used
        :param wrapped_description: the wrapped node description
        """
        # TODO: might need additional processing
        if class_name in self.classes.keys():
            logging.debug("Class already in the list: %s", class_name)
            if len(wrapped_description.children) != len(
                    self.classes[class_name].children
            ):
                logging.warning(
                    "Number of children mismatch for %s between stored "
                    "module %s and new module %s",
                    class_name, self.classes[class_name].yang_name(),
                    self.yang_name())
            # print(self.classes[class_name].children.keys())
            old = set(self.classes[class_name].children.keys())
            new = set(wrapped_description.children.keys())
            # print the different children
            diff = old ^ new
            if diff:
                logging.warning(
                    "Child mismatch for class %s between module %s and %s: %s",
                    class_name, self.classes[class_name].yang_name(),
                    self.yang_name(), diff)
        else:
            self.classes[class_name] = wrapped_description

    def add_rpc(self, rpc_name, wrapped_description):
        """
        Add an RPC that needs to be generated.

        :param rpc_name: the name of the RPC
        :param wrapped_description:  the wrapped node description
        """
        self.rpcs[rpc_name] = wrapped_description

    def add_typedef(self, typedef_name, wrapped_description):
        """
        Add a type definition that needs to be generated.

        :param typedef_name: the name of the type definition
        :param wrapped_description: the wrapped node description
        """
        # TODO: might need additional processing
        self.typedefs[typedef_name] = wrapped_description

    def generate_classes(self):
        """
        organizes and orchestrate the class file generation

        :return:
        """
        # generate enum classes
        self.fill_template('enum_type.jinja', self.enums())
        # generate class extensions
        self.fill_template('class_extension.jinja', self.types())
        # generate base class extensions
        self.fill_template('class_type.jinja', self.base_extensions())
        # generate classes
        self.fill_template('grouping.jinja', self.classes)
        # generate unions
        self.fill_template('union.jinja', self.unions())
        if not self.WOOL.beans_only:
            # generate empty xml_config template for NETCONF use
            # self.fill_template('empty_config.jinja',
            #                    {'empty_XML_config': module})
            # run only if rpcs are available
            # if module.rpcs:
            if_name = '%sInterface' % self.java_name
            rpc_imports = {imp for rpc in self.rpcs.values()
                           if hasattr(rpc, 'imports')
                           for imp in rpc.imports()}
            for root in self.get_root_elements().values():
                for child in root.children.values():
                    if hasattr(child, 'keys'):
                        if self.yang_module().replace('-', '.') not in \
                                child.java_imports.imports:
                            rpc_imports.update(
                                child.java_imports.get_imports())

            rpc_dict = {'rpcs': self.rpcs,
                        'imports': rpc_imports,
                        'package': self.package(),
                        'path': self.subpath(),
                        'module': self}
            self.fill_template('backend_interface.jinja',
                               {if_name: rpc_dict})
            rpc_dict['interface_name'] = if_name
            self.fill_template('backend_impl.jinja',
                               {'%sBackend' % self.java_name: rpc_dict})
            self.fill_template('routes.jinja',
                               {'%sRoutes' % self.java_name: rpc_dict})
        self.generate_pom('pom.jinja', self)

    def fill_template(self, template_name, description_dict):
        """
        Fills the template with the descriptions given in the dictionary.
        :param template_name: the template to be used
        :param description_dict: the dictionary with descriptions
        """
        template = self.env.get_template(template_name)
        for key, context in description_dict.items():
            if hasattr(context, 'subpath'):
                subpath = context.subpath()
            else:
                subpath = context['path']
            # get the output path for the file
            output_path = "%s/%s/%s" % (self.output_path, 'src', subpath)
            # create folder if not available
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            # render the template
            output = template.render(ctx=context, name=key)
            # print the output for debugging
            logging.debug(output)
            # write to file
            with open("%s/%s.java" % (output_path, key), 'w', encoding="utf-8",
                      newline="\n") as f:
                f.write(output)

    def generate_pom(self, template_name, description_dict):

        template = self.env.get_template(template_name)
        # get the output path for the file
        output_path = "%s" % self.output_path
        # create folder if not available
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        # render the template
        output = template.render(ctx=description_dict, name='')
        # print the output for debugging
        logging.debug(output)
        # write to file
        with open("%s/%s.xml" % (output_path, 'pom'), 'w', encoding="utf-8",
                  newline="\n") as f:
            f.write(output)


class JavaBits(NodeWrapper):
    """
    Wrapper class for bits statement
    """

    def __init__(self, statement, parent):
        super().__init__(statement, parent)
        self.java_imports = ImportDict()
        self.java_type = self.generate_java_type()
        self.java_imports.add_import(self.package(), self.java_type)
        self.bits = OrderedDict()
        self.group = 'bits'
        for stmt in statement.search('bit'):
            self.bits[stmt.arg] = JavaBit(stmt, self)


class JavaBit(NodeWrapper):
    """
    Wrapper class for bit values.
    """

    def __init__(self, statement, parent):
        super().__init__(statement, parent)
        javaname = self.yang_name()
        javaname = javaname.replace('-', '_').replace('.', '_')
        self.javaname = javaname


class JavaEnum(JavaNodeWrapper, PARENT['enum']):
    """
    Wrapper class for enum values.
    """

    def __init__(self, statement, parent):
        super(JavaEnum, self).__init__(statement, parent)
        # add an underscore in case the name starts with a number
        javaname = re.sub(r'^(\d)', r'_\1', self.yang_name().upper())
        javaname = javaname.replace('-', '_').replace('.', '_')
        if javaname != self.yang_name():
            self.javaname = javaname


class JavaEnumeration(JavaNodeWrapper, PARENT['enumeration']):
    """
    Wrapper class for enumeration statements.
    """

    def __init__(self, statement, parent):
        super(JavaEnumeration, self).__init__(statement, parent)
        self.java_imports = ju.ImportDict()
        self.java_type = self.generate_java_type()
        self.java_imports.add_import(
            self.package(), ju.java_class_name(self.parent.yang_name()))
        self.group = 'enum'

    @template_var
    def has_javanames(self):
        """
        Checks if at least one enum name was modified.
        :return: did enum names change
        """
        return any(hasattr(data, 'javaname') for _, data in self.enums.items())


class JavaUnion(JavaNodeWrapper, PARENT['union']):
    """
    Wrapper class for union statements
    """

    def __init__(self, statement, parent):
        super().__init__(statement, parent)
        self.group = 'union'
        self.type = None
        # list of types that belong to the union
        self.java_imports = ju.ImportDict()


class JavaRPC(JavaNodeWrapper, PARENT['rpc']):

    def __init__(self, statement, parent):
        super(JavaRPC, self).__init__(statement, parent)
        self.java_name = ju.to_camelcase(self.yang_name())
        self.top().add_rpc(self.java_name, self)
        self.children['input'] = self.input
        self.children['output'] = self.output