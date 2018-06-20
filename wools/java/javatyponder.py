from wools.java.javanodewrapper import JavaEnumeration
from wools.java.javanodewrapper import JavaNodeWrapper
from wools.java.javanodewrapper import JavaBaseType
from wools.java.javanodewrapper import JavaUnion
from wools.java.javanodewrapper import JavaBits
from .wool import PARENT
from . import javautils as ju

from alpakka.templates import template_var

from collections import OrderedDict
import logging


class JavaTyponder(JavaNodeWrapper):

    def __init__(self, statement, parent):
        super(JavaTyponder, self).__init__(statement, parent)
        if self.data_type:
            if self.data_type == 'enumeration':
                self.type = JavaEnumeration(statement.search_one('type'), self)
            elif self.data_type == 'union':
                self.type = JavaUnion(statement.search_one('type'), self)
            elif self.data_type == 'leafref':
                if hasattr(self, 'reference'):
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


class JavaLeaf(JavaTyponder, PARENT['leaf']):

    def __init__(self, statement, parent):
        super(JavaLeaf, self).__init__(statement, parent)
        self.java_type = self.type.java_type
        self.java_imports = ju.ImportDict()
        self.java_imports.merge(self.type.java_imports)
        self.children = OrderedDict()


class JavaTypeDef(JavaTyponder, PARENT['typedef']):

    def __init__(self, statement, parent):
        super(JavaTypeDef, self).__init__(statement, parent)
        self.group = 'type'
        self.java_imports = ju.ImportDict()
        if self.data_type == 'leafref':
            self.java_type = self.reference.data_type
            self.java_imports.merge(self.reference.java_imports)
        else:
            self.java_type = self.generate_java_type()
            self.top().add_typedef(self.java_type, self)
            self.java_imports.add_import(self.package(), self.java_type)


class JavaLeafList(JavaTyponder, PARENT['leaf-list']):

    def __init__(self, statement, parent):
        super(JavaLeafList, self).__init__(statement, parent)
        self.java_imports = ju.ImportDict()
        self.java_imports.add_import(
            ju.JAVA_LIST_IMPORTS[0], ju.JAVA_LIST_IMPORTS[1])
        self.group = 'list'
        self.children = OrderedDict()
        if hasattr(self, 'type') and hasattr(self.type, 'java_type'):
            self.java_type = 'List<%s>' % self.type.java_type
            # in case of leafrefs this attribute is available
            self.java_imports.merge(self.type.java_imports)
            # else we use a generic list
        else:
            self.java_type = 'List'
