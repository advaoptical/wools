import re

JAVA_LIST_IMPORTS = ('java.util', 'List')

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

JAVA_FORBIDDEN_ROOTS = {'rpc'}

default_values = {
    'int': 0,
    'boolean': 'false',
    'double': '0.0',
    'String': '""'
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


def to_java_name(name):
    """
    Transforms the name into camel case and removes leading underscores.

    :param name: the name to be processed
    :return: valid Java camel case name

    >>> to_java_name('_Java-name')
    'javaName'
    """
    return to_camelcase(re.sub(r'^_', '', name))


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
