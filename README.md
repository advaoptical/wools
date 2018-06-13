# Wools

Is a python project which extends the [alpakka](https://mgn-s-at-source.advaoptical.com/gitlab/anden/alpakka) project. Through the wool project
the output programming language for the code skeletons is defined. For that purpose a wool implementation can manipulate the generated output
data from the wool wrapper of the alpakka project as well as specifying the output format for the code skeletons.

## Getting Started

The following steps are guiding through a basic overview of the wools project and functional routine followed by a basic developer Guide on the subject
writing a new wool.

### General overview on the wool

Each wool inside the wools project represents a programming language or framework for which the alpakka project can create code skeletons. The wools
itself are structured in a tree like way, the root wool is the default from which all other wools are derived from. The tree like structure is also
presented by directory structure of the project. 

Each wool must be registered as part of the wools project, this registration can be performed in two different way. The persistent way is to perform
the registration during the wool installation, to do this the wool must be populated inside the setup.py of the wools project as entry point. Another
way to register a wool is a temporary way, for that the alpakka project has to be loaded in a terminal and than the population of the wool can be done
executing *<command for wool population is missing>*.

If a wool is registered successfully it can be used by the alpakka by setting the appropriate command line option. The alpakka project requires some
mandatory methods which should be present as part of each wool. Beside this each wool can implement own wrapping classes for each YANG statement type.
How the mandatory methods and the wool specific wrapping classes can be implemented is presented in the following part.

### Initial developer Guide

A wool implementation is build of two parts, the first part is mandatory and predefined by the implementation of the alpakka project. It is common to
implement this part in the __init__.py which should be present on the root level of the wool directory structure. The second part of the wool
implementation contains the wool specific wrapper classes for the different type of YANG statement, which are extending the node wrapper classes of
the alpakka project.

#### required methods

All required methods and attributes are implemented and set in the __init__.py file which is located at the top level of the individual wool directory.
The head of each wool __init__.py file must include the following lines:

```python
from alpakka import register_wool
WOOL = register_wool('<name of the wool>', __name__, parent='<name of the parent wool>')
```

This lines are required for a correct wool registration, the name of the wool can freely be chosen, the name of the parent wool has to be set to the
name of the parent wool or to 'default if no parent wool exists.

Additional to the wool registration the __init__.py should also include the implementation of the tree mandatory methods. 

```python
def generate_output(wrapped_module):

	pass
	
def wrapping_postprocessing(wrapped_modules, module):

	pass
	
def parse_config(module, path):
	
	pass
	
```

Each of this methods is called as part of the wrapping process initiated by the alpakka process. The first methods (generate_output) is dedicated
to organize the output generation and is called as last step of the wrapping chain, as argument the wrapped_module is given. The second mandatory
method is wrapping_postprocessing, the task of this method is to remove duplicated statements and to sort the statements by there parent. The reason for
that is that pyang handle each YANG module in a stand alone way, so that statements which are used by different modules are imported and wrapped
multiple times and are placed in the tree structure of the importing modules. To replace them at the importing module and to avoid overwriting
during the output generation this method is called after the wrapping task is finalized 

#### wrapping classes

## bullet based guide line

This section gives a bullet based overview of all steps which should be performed to implement and register a new wool as part of the wool project

* create new directory inside the wools project
	
* create the __init__.py
  * import the register_wool method of the alpakka project
  * call the register_wool method
  * implement the mandatory wools methods (generate_output, wrapping_postprocessing and parse_config)

* create and implement the required classes for the wool specific data transformation
	
* register the wool temporary or permanent

