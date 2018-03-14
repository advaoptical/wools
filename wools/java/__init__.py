import logging
import re
from alpakka import register_wool
import alpakka.wrapper.nodewrapper as nw
from collections import OrderedDict

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

PREFIX = ""

JAVA_WRAPPER_CLASSES = {
    "int": "Integer",
    "boolean": "Boolean",
    "double": "Double"
}



class ImportDict():
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


class JavaCase:

    def __init__(self, statement, parent):
        super().__init__(statement, parent)
        self.java_imports = ImportDict()
        self.java_type = java_class_name(self.statement.arg) + 'CaseType'
        self.top().add_class(self.java_type, self)
        self.java_imports.add_import(self.package(), self.java_type)


# class JavaTyponder:
#
#     def __init__(self):
#         for stmt in self.statement.substmts:
#             if stmt.keyword == 'type':
#                 # is the statement an enumeration
#                 if stmt.arg == 'enumeration':
#                     self.type = Enumeration(stmt, self)
#                 # is the statement a base type
#                 elif self.is_build_in_type:
#                     self.type = JavaBaseType(stmt, self)
#                 # is the statement a union
#                 elif stmt.arg == 'union':
#                     self.type = Union(stmt, self)
#                 # is the statement a lear reference
#                 elif stmt.arg == 'leafref':
#                     self.type = LeafRef(stmt, self)
#                 elif stmt.arg == 'bits':
#                     self.type = Bits(statement, self)
#                 # does the statement contain a type definition
#                 elif hasattr(stmt, 'i_typedef'):
#                     self.type = JavaTypeDef(stmt.i_typedef, self)
#                 else:
#                     logging.warning("Unmatched type: %s", stmt.arg)


class JavaGrouponder:

    def __init__(self, statement, parent):
        super().__init__(statement,parent)
        # find all available variables in the sub-statements
        self.vars = OrderedDict()
        for item in self.uses.values():
            element = self.uses.pop(item.yang_name())
            java_name = java_class_name(element.yang_name())
            self.uses[java_name] = element
        for item in self.children.values():
            java_name = re.sub(r'^_', '', item.yang_name())
            java_name = to_camelcase(java_name)
            self.vars[java_name] = item


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


class JavaModule(PARENT['module']):

    def __init__(self, statement, parent=None):
        self.classes = OrderedDict()
        self.rpcs = OrderedDict()
        self.typedefs = OrderedDict()
        self.java_name = java_class_name(statement.i_prefix)
        super().__init__(statement, parent=parent)

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

    def del_class(self, class_name):
        """
        Deletes a class from the collection.

        :param class_name: the class to be removed
        """
        self.classes.pop(class_name)

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


class JavaContainer(JavaGrouponder, PARENT['container']):

    def __init__(self, statement, parent):
        super(JavaContainer, self).__init__(statement, parent)
        self.java_imports = ImportDict()
        if 'tapi' in self.top().yang_name() and self.parent == self.top():
            # fixing name collision in the ONF TAPI: context
            self.java_type = java_class_name(statement.arg) + "Top"
            for name in self.uses.keys():
                self.uses.pop(name)
                self.top().del_class(name)
            for ch_name, ch_wrapper in self.children.items():
                # store the yang name
                ch_wrapper.name = ch_wrapper.statement.arg
                # remove leading underscores from the name
                java_name = re.sub(r'^_', '', ch_wrapper.name)
                java_name = to_camelcase(java_name)
                self.vars[java_name] = ch_wrapper
                self.top().add_class(self.java_type, self)
                self.java_imports.add_import(to_package(self.top().yang_name(), PREFIX), self.java_type)
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
                    if child.statement.keyword in [
                        'container', 'grouping', 'list', 'leaf-list',
                    ]:
                        child.name = child.statement.arg
                        java_name = to_camelcase(child.name)
                        self.vars[java_name] = child
            self.java_type = java_class_name(statement.arg)
            self.top().add_class(self.java_type, self)
            self.java_imports.add_import(to_package(self.top().yang_name(), PREFIX), self.java_type)


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
                        java_name = to_camelcase(child.statement.arg)
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
            self.element_type = (java_class_name(statement.arg) +
                                 JAVA_LIST_CLASS_APPENDIX)
            self.top().add_class(self.element_type, self)
            self.java_type = 'List<%s>' % self.element_type
            self.java_imports.add_import(to_package(self.top().yang_name(), PREFIX), self.element_type)
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


class JavaLeaf(PARENT['leaf']):

    def __init__(self, statement, parent):
        super().__init__(statement, parent)
        self.java_type = self.data_type
        self.java_imports = ImportDict()
        if self.is_build_in_type:
            self.java_type = JavaBaseType(self.data_type)
        else:
            self.java_type = self.top().typedefs[self.data_type]
        self.java_imports.merge(self.java_type.java_imports)


class JavaGrouping(PARENT['grouping'], JavaGrouponder):

    def __init__(self, statement, parent):
        super(JavaGrouping, self).__init__(statement=statement, parent=parent)
        self.java_type = java_class_name(self.yang_name())
        self.java_imports = ImportDict()
        self.java_imports.add_import(to_package(self.top().yang_name(), PREFIX), self.java_type)
        self.top().add_class(java_class_name(self.yang_name()), self)
        for sub_st in statement.substmts:
            if sub_st.keyword == 'choice':
                for case in sub_st.substmts:
                    if case.keyword == 'case':
                        java_name = to_camelcase(re.sub(r'^_', '', case.arg))
                        var = JavaCase(case, self)
                        var.name = case.arg
                        self.vars[java_name] = var
        

class JavaTypeDef(PARENT['typedef']):

    def __init__(self, statement, parent):
        super().__init__(statement, parent)
        self.group = 'type'
        self.java_imports = ImportDict()
        if self.data_type == 'leafref':
            self.java_type = self.reference.data_type
            self.java_imports.merge(self.reference.java_imports)
        else:
            self.java_type = java_class_name(self.yang_name())
            self.top().add_typedef(self.yang_name(), self)
            self.java_imports.add_import(to_package(self.top().yang_name(), PREFIX), self.java_type)


class JavaLeafList(PARENT['leaf-list']):

    def __init__(self, statement, parent):
        super().__init__(statement,parent)
        self.java_imports = ImportDict()
        self.java_imports.add_import(
            JAVA_LIST_IMPORTS[0], JAVA_LIST_IMPORTS[1])
        self.group = 'list'
        if hasattr(self, 'type') and hasattr(self.type, 'java_type'):
            self.java_type = 'List<%s>' % self.type.java_type
            # in case of leafrefs this attribute is available
            self.java_imports.merge(self.type.java_imports)
            # else we use a generic list
        else:
            self.java_type = 'List'