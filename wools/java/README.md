# Java Wool

The Java wool is a wool implementation to generate java code skeletons.
In Addition to the original wool implementation, the java wool is the parent to two more wools for akka and jersey code skeletons.
The Java wool uses the python library jinja2 for the output generation and the configparser to handle the wool specific options.
The wool extends all YANG statements which are handled by the node wrapper.

## Structure

The java wool, which is defined in `wool.py` is divided into multiple files.
The `__init__.py` is the starting point of the wool.
It implicitly triggers the registration of the wool, which is performed by `wool.py`.
The additional files are dividing the YANG statement types into groups.
The majority is implemented inside the `javanodewrapper.py`.
The implemented classes comprise

* JavaBaseType
* JavaNodeWrapper
* JavaModule
* JavaBits
* JavaBit
* JavaEnum
* JavaEnumeration
* JavaUnion
* JavaRPC

All YANG statements, which represent type nodes, are implemented inside the `javatyponder.py`:

* JavaTyponder
* JavaLeaf
* JavaTypeDef
* JavaLeafList

The wrapper classes for YANG statements that contain other YANG statements as children are collected in `javagrouponder.py`:

* JavaGrouponder
* JavaContainer
* JavaList
* JavaGrouping
* JavaCase
* JavaChoice
* JavaInput
* JavaOutput

The last python class file is `javautils.py`
This file provides some general java specific functionalities which are used by all other wrapper classes.
This file does not only contain classes but also standalone methods.

* ImportDict
* java_default
* firstlower
* firstupper
* to_package
* to_camelcase
* java_class_name

In addition to the mentioned python files, the Java folder contains a wool folder for the akka and jersey wool and a config directory, which contains the wool configuration file (`wool_config.ini`) and a copyright file (`copyright.txt`).
