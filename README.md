# Wools

> Licensed under the [Apache License, Version 2.0][license]

[license]: http://www.apache.org/licenses/LICENSE-2.0

[![Supported Python versions][pyversions]][python]
[![PyPI package version][version]][pypi]

[pyversions]: https://img.shields.io/pypi/pyversions/wools.svg

[python]: https://python.org

[version]: https://img.shields.io/pypi/v/wools.svg

[pypi]: https://pypi.python.org/pypi/wools

[![Travis CI build status][status]][travis]

[status]: https://travis-ci.org/advaoptical/wools.svg?branch=master

[travis]: https://travis-ci.org/advaoptical/wools

Wools is a python project extending the [Alpakka][alpakka] project. The selected wool defines the target programming language for the code skeletons. For this purpose, a wool implementation can adapt the wrapping procedure of the `alpakka` project as well as define the code generation process and output format for the code skeletons.

[alpakka]: https://github.com/advaoptical/alpakka

## Getting Started

The following sections give a short overview of the `wools` project and provide a basic developer guide on how to write a new wool.

### General Overview of the Wool

Every wool of the `wools` project represents a programming language or framework for which the `alpakka` can create code skeletons. Wools are structured like a tree. The default wool represents the root from which all other wools are derived. The tree-like structure is also applied to the directory structure of the project.

Every wool that is part of the `wools` project must be registered. Usually, this registration is performed in two steps. First all available wools are announced during the wool installation by providing an entry point in the `setup.py`, e.g.:

```python
setup(
    ...
    entry_points={'alpakka_wools': [
        'Java=wools.java',
        'Akka=wools.java.akka',
        'Jersey=wools.java.jersey',
    ]},
    ...
)
```

In a second step all wools that provide these entry points are added to the available wools during startup. This can be done with the following code that shows an example for the Java wool:

```python
from alpakka import WOOLS

WOOL = <WoolClassName>(
    '<name of the wool>',
    __package__,
    parent='<name of the parent wool>')

WOOLS.register(WOOL)

PARENT = WOOL.parent
```

These lines are required for a correct wool registration. The name of the wool can be chosen freely, the name of the parent wool has to be set to the name of the used parent wool or to `default` if no parent wool exists. If a wool is registered successfully it can be used by setting `alpakka`'s `-w` command line option. `alpakka` expects a few mandatory methods that should be present as part of each wool. In addition, the wrapping process for YANG statements can be modified. This is covered in the next part.

### Basic Developer Guide

A wool implementation is built up of two parts. The first part is mandatory and defines a few required methods that the wool needs to implement. The second part of the wool implementation is optional. It may contain wool specific wrapper classes for different YANG statements, which are extending or overwriting the existing statement wrapper classes of the `alpakka` project.

#### Required Methods

A wool needs to implement three mandatory methods beside its registration.

```python
    def parse_config(self, path):
        raise NotImplementedError

    def wrapping_postprocessing(self, module, wrapped_modules):
        raise NotImplementedError

    def generate_output(self, module):
        raise NotImplementedError
```

Each of these methods is called as part of the wrapping process initiated by `alpakka`.

The first mandatory method `parse_config` handles all wool specific options that are provided through a configuration file. The location and the name of the configuration is passed through the configuration-file-location command line option of `alpakka`. The method receives the path which is specified by the command line option. The handling of the configuration can be implemented individually according to the requirements of the wool.

The second method is `wrapping_postprocessing`, which provides the ability to perform some post processing after all modules have been wrapped. The currently handled module as well as the set of all wrapped modules are passed. An example for the usage of this method is implemented as part of the Java wool. This wool uses the postprocessing to remove duplicated classes and to move statements to the correct module. This is needed because pyang handles each YANG module individually and imports all required statements. If a grouping is used inside different modules it is imported and processed multiple times. To avoid overwriting existing files during the output generation and to place the class in the correct package the postprocessing is applied.

Finally, `generate_output` is called with the module that needs to be handled in order to coordinate the output generation.

#### Wrapping Classes

Another important part of the wool implementation is the ability to adapt the wrapping process to the requirements of the specific programming language. It is possible to adapt the wrapping of all available YANG statements.

If the implementation of the modified wrapper classes is done in different python files, the files must be imported afterwards. How to implement a wool specific wrapping class will be explained based on the example of the Java specific implementation of the YANG Leaf statement.

```python
import PARENT

...

class JavaLeaf(JavaTyponder, PARENT['leaf']):

    def __init__(self, statement, parent):
        super(JavaLeaf, self).__init__(statement, parent)
        self.java_type = self.type.java_type
        self.java_imports = ...
```

It is recommended to define and import a `PARENT` parameter in the `__init__.py`. The class declaration may contain any inheritance statement. In the given example the leaf inherits from the `JavaTyponder` class. In addition, a link to the YANG type which should be wrapped by this class should be initialized. This is done by the second inheritance parameter which links the class to the node wrapper for the leaf statement. For other statement types, such as containers, the statement should look like `PARENT['container']` and accordingly for other YANG statement types. Inside each wrapped class the constructor method `__init__` must be present, and accept two arguments beside the object reference. The first of the two parameter is the raw YANG statement provided by pyang. The second argument contains a reference to the wrapped object of the parent statement, which is required to build the correct tree structure. The minimal implementation of the constructor should contain the `super` call, which initiates the constructor of the parent classes.

Beside these requirements it is possible to implement additional handling or functionality required for the output generation.
Thereby, all attributes and methods that are provided by the node wrappers can be used.

For more details see the [java wool] documentation and implementation.

[java wool]: https://github.com/advaoptical/wools/tree/master/wools/java

## Summary for Creating a Wool

This section gives a short overview of all steps which need to be performed to implement a new wool as part of the `wools` project:

* create new directory inside the `wools` project

* implement a wool class that covers all the mandatory methods (`parse_config`, `wrapping_postprocessing`, and `generate_output`)

* create the `__init__.py` and register the wool

* implement the required classes for the wool specific data transformation
