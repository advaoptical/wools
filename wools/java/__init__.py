import logging
import re
import os
from alpakka import register_wool
from alpakka.templates import template_var
from alpakka.wrapper.nodewrapper import NodeWrapper
from collections import OrderedDict
from jinja2 import Environment, PackageLoader

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

WOOL = register_wool('Java', __name__, data_type_patterns={
    (r"u?int\d*", "int"),
    (r"string", "String"),
    (r"boolean", "boolean"),
    (r"decimal64", "double"),
    (r"binary", "byte[]"),
    (r"empty", "Object"),
})

PARENT = WOOL.parent

JAVA_RESERVED_WORDS = frozenset(["switch", "case"])

JAVA_LIST_IMPORTS = ('java.util', 'List')

JAVA_LIST_CLASS_APPENDIX = 'ListType'

# Java type used to instantiate lists
JAVA_LIST_INSTANCE_IMPORTS = ('com.google.common.collect', 'ImmutableList')

# list of reserved words in Java
JAVA_RESERVED_WORDS = frozenset(["switch", "case"])

JAVA_WRAPPER_CLASSES = {
    "int": "Integer",
    "boolean": "Boolean",
    "double": "Double"
}

JAVA_FORBIDDEN_ROOTS = ('rpc')

default_values = {
    'int': 0,
    'boolean': 'false'
}


def java_class_name(name):
    """
    Cleanup for names that need to follow Java class name restrictions.
    Add any further processing here.

    :param name: the name to be cleaned up
    :return: class name following Java convention

    >>> java_class_name('some-type')
    'SomeType'
    """
    return name.replace("-", " ").title().replace(" ", "")


def to_camelcase(string):
    """
    Creates a camel case representation by removing hyphens.
    The first letter is lower case everything else remains untouched.

    :param string: string to be processed
    :return: camel case representation of the string

    >>> to_camelcase('Hello-world')
    'helloWorld'
    """
    name = string[0].lower() + string[1:]
    name = re.sub(r'[-](?P<first>[a-zA-Z])',
                  lambda m: m.group('first').upper(),
                  name)
    # check if the name is a reserved word and prepend '_'
    if name in JAVA_RESERVED_WORDS:
        return '_' + name
    else:
        return name


def to_package(string, prefix=None):
    """
    Converts the string to a package name by making it lower case,
    replacing '-' with '.' and adding a prefix if available.

    :param string: the string to be converted
    :param prefix: the prefix for the package
    :return: package name

    >>> to_package('yang-module')
    'yang.module'

    >>> to_package('yang-module', 'fancy')
    'fancy.yang.module'
    """
    package = string.lower().replace("-", ".")
    if prefix:
        package = '%s.%s' % (prefix, package)
    return package


def firstupper(value):
    """
    Makes the first letter of the value upper case without touching
    the rest of the string.
    In case the value starts with an '_' it is removed and the following letter
    is made upper case.

    :param value: the string to be processed
    :return: the value with a upper case first letter

    >>> firstupper('helloworld')
    'Helloworld'
    >>> firstupper('_HelloWorld')
    'HelloWorld'
    """
    value = value.lstrip('_')
    return value and value[0].upper() + value[1:]


def firstlower(value):
    """
    Makes the first letter of the value lower case without touching
    the rest of the string.

    :param value: the string to be processed
    :return: the value with a lower case first letter

    >>> firstlower('HelloWorld')
    'helloWorld'
    """
    return value and value[0].lower() + value[1:]


def java_default(value):
    """
    Maps the java type to the corresponding default value.

    :param value: the java type string
    :return: the default value

    >>> java_default('int')
    0
    >>> java_default('boolean')
    'false'
    >>> java_default('Object')
    'null'
    """
    return default_values.get(value, 'null')


class ImportDict:
    """
    Class that is used to store imports.

    It wraps a dictionary and stores the classes per package as sets.
    This makes it easier to filter imports that are part of a package.

    >>> impdict = ImportDict()
    >>> impdict.add_import('package', 'Class')
    >>> impdict.imports
    {'package': {'Class'}}
    >>> impdict.get_imports()
    {'package.Class'}

    Newly added imports are merged into the existing ones:

    >>> impdict.add_import('package', 'Clazz')
    >>> sorted(impdict.imports['package'])
    ['Class', 'Clazz']
    >>> sorted(impdict.get_imports())
    ['package.Class', 'package.Clazz']

    You can also merge an ``ImportDict`` with another one:

    >>> other = ImportDict()
    >>> other.add_import('package', 'Class')
    >>> other.add_import('package', 'Klass')
    >>> other.add_import('fancy.package', 'Klazz')

    >>> impdict.merge(other)
    >>> sorted(impdict.imports.keys())
    ['fancy.package', 'package']
    >>> sorted(impdict.get_imports())
    ['fancy.package.Klazz', 'package.Class', 'package.Clazz', 'package.Klass']
    """

    def __init__(self):
        # an empty dictionary
        self.imports = {}

    def add_import(self, package, clazz):
        """
        Adds an import.

        :param package: the package name of the import
        :param clazz: the class name of the import
        """
        self.imports.setdefault(package, set()).add(clazz)

    def merge(self, other):
        """
        Merges another dictionary into this one.

        :param other: the :class:`ImportDict` instance to be merged
        """
        for package, classes in other.imports.items():
            pkgclasses = self.imports.setdefault(package, set())
            pkgclasses |= classes

    def get_imports(self):
        """
        Converts the managed imports into a set of imports.

        :return: a ``set`` of fully qualified import strings
        """
        return {'%s.%s' % (pkg, cls) for pkg, classes in self.imports.items()
                for cls in classes}


class JavaBaseType:
    """
    Wrapper class for a java base types, like boolean, double, int and String.
    """

    def __init__(self, data_type):
        self.java_imports = ImportDict()
        self.java_type = data_type
        # is a cast needed to use hashCode
        self.java_cast = JAVA_WRAPPER_CLASSES.get(self.java_type, None)
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
        return to_package(self.yang_module(), WOOL.prefix)

    @template_var
    def subpath(self):
        """
        The subpath of this module.
        :return: the package name
        """
        if WOOL.prefix:
            return '%s/%s' % (WOOL.prefix.replace(".", "/"),
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

    def collect_children(self, caller):

        for item in self.uses.values():
            item.collect_children(caller)
        caller.children.update(self.children)


class JavaTyponder(JavaNodeWrapper):

    def __init__(self, statement, parent):
        super(JavaTyponder, self).__init__(statement, parent)
        if self.data_type:
            if self.data_type == 'enumeration':
                self.type = JavaEnumeration(statement.search_one('type'), self)
            elif self.data_type == 'union':
                self.type = JavaUnion(statement.search_one('type'), self)
            elif self.data_type == 'leafref':
                if self.reference:
                    self.type = self.reference
                else:
                    self.type = 'leafref'
            elif self.data_type == 'bits':
                self.type = JavaBits(statement, self)
            elif self.is_build_in_type:
                self.type = JavaBaseType(self.data_type)
            elif not self.is_build_in_type:
                self.type = self.top().derived_types[self.data_type]
            else:
                logging.warning("Unmatched type: %s", self.data_type)

    @template_var
    def member_imports(self):
        """
        :return: Imports that are needed for this type if it is a member of a
                 class.
        """
        return self.type.java_imports


class JavaGrouponder(JavaNodeWrapper):

    def __init__(self, *args):
        super(JavaGrouponder, self).__init__(*args)
        # find all available variables in the sub-statements
        self.vars = OrderedDict()
        for item in self.children.values():
            java_name = re.sub(r'^_', '', item.yang_name())
            java_name = to_camelcase(java_name)
            self.vars[java_name] = item
        if hasattr(self, 'children'):
            self.collect_children(self)
        for item in list(self.uses.values()):
            self.uses[java_class_name(item.yang_name())] = \
                self.uses.pop(item.yang_name())

    @template_var
    def inherited_vars(self):
        """
        Collects a dictionary of inherited variables that are needed for
        super calls.
        :return: dictionary of inherited variables
        """
        result = OrderedDict()
        for name, parent_group in self.uses.items():
            # collect variables that are inherited by the parent
            for inh_name, var in parent_group.inherited_vars().items():
                result[inh_name] = var
            # collect variables available in the parent class
            for var_name, var in parent_group.vars.items():
                result[var_name] = var
        return result

    @template_var
    def imports(self):
        """
        Collects all the imports that are needed for the grouping.
        :return: set of imports
        """
        imports = ImportDict()
        # imports from children
        for child in self.children.values():
            imports.merge(child.java_imports)
        # imports from super classes
        for inherit in self.uses.values():
            imports.merge(inherit.inheritance_imports())
        for var in self.vars.values():
            # checking if there is at least one list defined in the grouponder
            if hasattr(var, 'group') and var.group == 'list':
                imports.add_import(JAVA_LIST_INSTANCE_IMPORTS[0],
                                   JAVA_LIST_INSTANCE_IMPORTS[1])
                break
        return imports.get_imports()


class JavaModule(JavaNodeWrapper, PARENT['module']):

    def __init__(self, statement, parent=None):
        self.classes = OrderedDict()
        self.rpcs = OrderedDict()
        self.typedefs = OrderedDict()
        self.prefix = WOOL.prefix
        self.java_name = java_class_name(statement.i_prefix)

        self.output_path = self.WOOL.output_path
        # variables for output generation
        path = '/templates'
        item = self.WOOL
        while item.name != 'default':
            path = '/' + item.name[0].lower() + item.name[1:] + path
            item = item.parent
        self.env = Environment(loader=PackageLoader('wools', path))
        # add filters to environment
        self.env.filters['firstupper'] = firstupper
        self.env.filters['firstlower'] = firstlower
        self.env.filters['javadefault'] = java_default

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
        result = to_camelcase(self.yang_name())
        result = result[0].upper() + result[1:]
        return result

    @template_var
    def get_root_elements(self):
        result = dict()
        for name, child in self.children.items():
            if child.yang_type() not in JAVA_FORBIDDEN_ROOTS:
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
        if not WOOL.beans_only:
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
                            rpc_imports.update(child.java_imports.get_imports())

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
        output_path = "%s" % (self.output_path)
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


class JavaContainer(JavaGrouponder, PARENT['container']):

    def __init__(self, statement, parent):
        super(JavaContainer, self).__init__(statement, parent)
        self.java_imports = ImportDict()
        if 'tapi' in self.top().yang_module() and self.parent == self.top():
            # fixing name collision in the ONF TAPI: context
            self.java_type = java_class_name(self.yang_name()) + "Top"
            for name in set(self.uses.keys()):
                self.uses.pop(name)
                self.top().classes.pop(name)
            for ch_name, ch_wrapper in self.children.items():
                # store the yang name
                ch_wrapper.name = ch_wrapper.yang_name()
                # remove leading underscores from the name
                java_name = re.sub(r'^_', '', ch_wrapper.name)
                java_name = to_camelcase(java_name)
                self.vars[java_name] = ch_wrapper
                self.top().add_class(self.java_type, self)
                self.java_imports.add_import(self.package(), self.java_type)
            # containers that just import a grouping don't need a new class
            # -> variable
        elif len(self.uses) == 1 and len(self.vars) == 0:
            class_item = next(iter(self.uses.values()))
            self.java_type = class_item.java_type
            self.java_imports = class_item.java_imports
        else:
            # process exception when statement has i_children but no variables
            if len(statement.i_children) > 0 and len(self.vars) == 0:
                # adding variables to container class class
                for child in self.children.values():
                    if child.yang_type() in [
                        'container', 'grouping', 'list', 'leaf-list',
                    ]:
                        child.name = child.yang_name()
                        java_name = to_camelcase(child.name)
                        self.vars[java_name] = child
            self.java_type = java_class_name(self.yang_name())
            self.top().add_class(self.java_type, self)
            self.java_imports.add_import(self.package(), self.java_type)

    @template_var
    def member_imports(self):
        """
        :return: imports needed if this class is a member
        """
        return self.java_imports


class JavaList(JavaGrouponder, PARENT['list']):

    def __init__(self, statement, parent):
        super(JavaList, self).__init__(statement, parent)
        self.group = 'list'
        self.java_imports = ImportDict()
        # TODO: einmalig genutzt, wirklich als globale variable
        self.java_imports.add_import(JAVA_LIST_IMPORTS[0],
                                     JAVA_LIST_IMPORTS[1])
        # check if a super class exists and assign type
        if self.uses:
            # multiple inheritance is not supported in Java:
            # importing all variables
            if len(self.uses) > 1:
                for use in self.uses.values():
                    for child in use.children.values():
                        java_name = to_camelcase(child.yang_name())
                        self.vars[java_name] = child
            # only one super class -> assign type
            else:
                self.type = next(iter(self.uses.values()))
                self.java_imports.merge(self.type.java_imports)
        # check for any other children not already in the variable list and
        # add them
        # FIXME: the 'if' might not work correctly
        # for child_wr in self.children.values():
        #     if child_wr not in self.vars.values():
        #         child_wr.name = child_wr.statement.arg
        #         java_name = to_camelcase(child_wr.statement.arg)
        #         self.vars[java_name] = child_wr
        # if new variables are defined in the list, a helper class is needed
        # FIXME: the commented code (previous fixme) breaks this check
        if self.children and 0 < len(self.vars):
            self.element_type = (java_class_name(self.yang_name()) +
                                 JAVA_LIST_CLASS_APPENDIX)
            self.top().add_class(self.element_type, self)
            self.java_type = 'List<%s>' % self.element_type
            self.java_imports.add_import(self.package(), self.element_type)
        else:
            # if a type is defined use it
            if hasattr(self, 'type') and hasattr(self.type, 'java_type'):
                self.element_type = self.type.java_type
                self.java_type = 'List<%s>' % self.type.java_type
            # unknown list elements
            else:
                self.java_type = 'List'
        # collect list of keys
        self.keys = [to_camelcase(key.arg)
                     for key in getattr(statement, 'i_key', ())]


class JavaLeaf(JavaTyponder, PARENT['leaf']):

    def __init__(self, statement, parent):
        super(JavaLeaf, self).__init__(statement, parent)
        self.java_type = self.type.java_type
        self.java_imports = ImportDict()
        self.java_imports.merge(self.type.java_imports)
        self.children = OrderedDict()


class JavaGrouping(JavaGrouponder, PARENT['grouping']):

    def __init__(self, statement, parent):
        super(JavaGrouping, self).__init__(statement, parent)
        self.java_type = java_class_name(self.yang_name())
        self.java_imports = ImportDict()
        self.java_imports.add_import(self.package(), self.java_type)
        self.top().add_class(java_class_name(self.yang_name()), self)
        for sub_st in statement.substmts:
            if sub_st.keyword == 'choice':
                for case in sub_st.substmts:
                    if case.keyword == 'case':
                        java_name = to_camelcase(re.sub(r'^_', '', case.arg))
                        var = JavaCase(case, self)
                        var.name = case.arg
                        self.vars[java_name] = var

    @template_var
    def type(self):
        # FIXME: needs fixing for more than one uses
        if not self.vars:
            if len(self.uses) == 1:
                return next(self.uses.keys())
        else:
            return None

    @template_var
    def inheritance_imports(self):
        """
        :return: Imports needed if inheriting from this class.
        """
        return self.java_imports

    @template_var
    def member_imports(self):
        return self.java_imports
        

class JavaTypeDef(JavaTyponder, PARENT['typedef']):

    def __init__(self, statement, parent):
        super(JavaTypeDef, self).__init__(statement, parent)
        self.group = 'type'
        self.java_imports = ImportDict()
        if self.data_type == 'leafref':
            self.java_type = self.reference.data_type
            self.java_imports.merge(self.reference.java_imports)
        else:
            self.java_type = java_class_name(self.yang_name())
            self.top().add_typedef(self.java_type, self)
            self.java_imports.add_import(self.package(), self.java_type)


class JavaLeafList(JavaTyponder, PARENT['leaf-list']):

    def __init__(self, statement, parent):
        super(JavaLeafList, self).__init__(statement,parent)
        self.java_imports = ImportDict()
        self.java_imports.add_import(
            JAVA_LIST_IMPORTS[0], JAVA_LIST_IMPORTS[1])
        self.group = 'list'
        self.children = OrderedDict()
        if hasattr(self, 'type') and hasattr(self.type, 'java_type'):
            self.java_type = 'List<%s>' % self.type.java_type
            # in case of leafrefs this attribute is available
            self.java_imports.merge(self.type.java_imports)
            # else we use a generic list
        else:
            self.java_type = 'List'


class JavaBits(NodeWrapper):
    """
    Wrapper class for bits statement
    """

    def __init__(self, statement, parent):
        super().__init__(statement, parent)
        self.java_imports = ImportDict()
        self.java_type = java_class_name(self.yang_name())
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
        self.java_imports = ImportDict()
        self.java_type = java_class_name(self.yang_name())
        self.java_imports.add_import(
            self.package(), java_class_name(self.parent.yang_name()))
        self.enums = OrderedDict()
        self.group = 'enum'
        # loop through substatements and extract the enum values
        # for item in self.parent.enumeration.enums.values():
        #   self.enums[item.yang_name()] = JavaEnum(item.statement, self)
        # for stmt in statement.search('enum'):
        #     self.enums[stmt.arg] = JavaEnum(stmt, self)

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
        self.java_imports = ImportDict()


class JavaChoice(JavaGrouponder, PARENT['choice']):

    def __init__(self, statement, parent):
        super(JavaChoice, self).__init__(statement, parent)


class JavaCase(JavaGrouponder, PARENT['case']):

    def __init__(self, statement, parent):
        super(JavaCase, self).__init__(statement, parent)
        self.java_imports = ImportDict()
        self.java_type = java_class_name(self.yang_name()) + 'CaseType'
        self.top().add_class(self.java_type, self)
        self.java_imports.add_import(self.package(), self.java_type)


class JavaRPC(JavaNodeWrapper, PARENT['rpc']):

    def __init__(self, statement, parent):
        super(JavaRPC, self).__init__(statement,parent)
        self.java_name = to_camelcase(self.yang_name())
        self.top().add_rpc(self.java_name, self)
        self.children['input'] = self.input
        self.children['output'] = self.output


class JavaInput(JavaGrouponder, PARENT['input']):

    def __init__(self, statement, parent):
        super(JavaInput, self).__init__(statement, parent)


class JavaOutput(JavaGrouponder, PARENT['output']):

    def __init__(self, statement, parent):
        super(JavaOutput, self).__init__(statement, parent)