# Java Wool

The Java Wool is a wool implementation to generate java code skeletons. Additional to the original wool implementation
the java wool is the parent to two more wools which allows to generate akka and jersey code skeletons. The java wool
uses the python library jinja2 for the output generation and the configparser to handle the wool specific options.
The wool extends all YANG statements which are handled by the nodewrapper.

## Structure

The java wool is structured into five files. The primary file is the __init__.py file, this file implements the general
wool registration and the three mandatory methods. The four additional files are dividing the YANG statement types
into different groups, the mayor group is implemented inside the javanodewrapper.py classes which are implemented
there are


..* JavaBaseType
..* JavaNodeWrapper
..* JavaModule
..* JavaBits
..* JavaBit
..* JavaEnum
..* JavaEnumeration
..* JavaUnion
..* JavaRPC


All YANG statements which are representing type based nodes are implemented inside the javatyponder.py file. This file
include the following classes


..* JavaTyponder
..* JavaLeaf
..* JavaTypeDef
..* JavaLeafList


The wrapper classes for YANG statements which can include other YANG statements as children. Python classes which are
included in this file are


..* JavaGrouponder
..* JavaContainer
..* JavaList
..* JavaGrouping
..* JavaCase
..* JavaChoice
..* JavaInput
..* JavaOutput


The last python class file is the javautils.py, this file provides some general java specific functionalities which are
used by all other python class files. This file does not only include classes but also some stand alone methods. The 
following classes and methods are provided


..* ImportDict
..* java_default
..* firstlower
..* firstupper
..* to_package
..* to_camelcase
..* java_class_name


Additional to the mentioned python files the java includes the wool folder for the akka and jersey wool and a config
directory which contains the wool configuration file (wool_config.ini) and the current copyright file (copyright.txt).