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
executing the following commands.

```python
import alpakka
alpakka.register_wool('<name>', 'wools.<parent>.<name>', parent='<parent>')
```

If a wool is registered successfully it can be used by alpakka through setting the appropriate command line option. The alpakka project requires some
mandatory methods which should be present as part of each wool. Beside this each wool can implement own wrapping classes for each YANG statement type.
How the mandatory methods and the wool specific wrapping classes can be implemented is presented in the following part.

### Initial developer Guide

A wool implementation is build of two parts, the first part is mandatory and predefined by the implementation of the alpakka project. It is common to
implement this part in the __init__.py which should be present on the root level of each wool directory structure. The second part of the wool
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
name of the used parent wool or to 'default if no parent wool exists.

Additional to the wool registration the __init__.py should also include the implementation of the tree mandatory methods. 

```python
def generate_output(module):

	pass
	
def wrapping_postprocessing(module, wrapped_modules):

	pass
	
def parse_config(module, path):
	
	pass
	
```

Each of this methods is called as part of the wrapping process initiated by the alpakka process. The first method (generate_output) is dedicated
to organize the output generation and is called as last step of the wrapping chain, as argument the wrapped_module is given. The second mandatory
method is wrapping_postprocessing, the task which is performed by this method can be chosen freely. The first argument of this method is the wrapped
module which is currently handled, the second argument is a dictionary of all wrapped modules including the current module. A example for the usage
of this method is implemented as part of the java wool, the java wool uses the post-processing to remove duplicated statements and to move statements
which are located inside the wrong module to the correct parenting module. This is needed because pyang handle each YANG module in a standalone way
and imports all required statements, if a grouping is used inside different modules it is imported and processed multiple times. To avoid an
overwriting during the output generation and to place the grouping at the module which is original implementing it the post processing is used.
The last mandatory method (parse_config) is dedicated to handle all wool specific options which are provided as configuration file. The location
and the name of the configuration can be parsed through the configuration-file-location command line option of the alpakka program. The method gets
as argument the current module and the path which is specified by the command line option. The handling of the option can be implemented individually
and accordingly to the requirements of the wool.

#### wrapping classes

Another important part of the wool implementation is the possibility to adapt the wrapping process to the requirements of the specific programming
language, it is possible either to adapt the wrapping of single YANG statements. Independent on how many wrapping classes are changed a registration
step must be performed, therefore the __init__.py of the wool must include the following lines.

```python
PARENT = WOOL.parent
```

If the implementation of the individual wrapper classes is done in different python files (what is recommended) the files must be imported afterwards.
How to implement a wool specific wrapping class will be explained now based on the example of the java specific implementation of the YANG Leaf
statement.

```python
import PARENT

...

class JavaLeaf(JavaTyponder, PARENT['leaf']):
	
	def __init__(self, statement, parent):
		super(JavaLeaf, self).__init__(statement, parent)
		self.java_type = self.type.java_type
		self.java_imports = ...

```

To implement a wool specific first the PARENT parameter from the __init__.py must be imported. The class declaration can contain any inheritance
statement, in the given example the leaf inherits from the JavaTyponder class, additional to that a link to the YANG statement which should be
wrapped by this class should be initialized. This is done by the second inheritance parameter which links the class to the nodewrapper for the 
leaf statement. For other statement types like container the statement should look like PARENT['container'] or accordingly for other YANG statement
types. Inside the each wrapping class the constructor method __init__ must be present, and accept two arguments beside the object reference. The first
of the two parameter is the raw YANG statement provided by pyang. The second argument contain a reference to the wrapped object of the parent
statement, which is required to build the correct tree structure. The minimal implementation if the constructor should contain the super call, which 
initiates the constructor of the inherited class. The super method requires as arguments the name of the current class and the object reference,
additional inside the __init__ call the two arguments statement and parent are parsed which are part of each class.

Beside this minimal requirements it is possible to implement additional data manipulations or functionalities required for the output generation.
Thereby it is possible to use all attributes and methods which are provided by the nodewrapper. An overview of this attributes and methods is given
in the following figure.

![alt text](https://mgn-s-at-source.advaoptical.com/gitlab/anden/alpakka/blob/wrapperRebuild/NodeWrapperRebuildImplemented.jpg)

## bullet based guide line

This section gives a bullet based overview of all steps which should be performed to implement and register a new wool as part of the wool project

* create new directory inside the wools project
	
* create the __init__.py
  * import the register_wool method of the alpakka project
  * call the register_wool method
  * implement the mandatory wools methods (generate_output, wrapping_postprocessing and parse_config)

* create and implement the required classes for the wool specific data transformation
	
* register the wool temporary or permanent

