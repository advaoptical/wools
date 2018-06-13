# Wools

Is a python project which extends the [alpakka](https://mgn-s-at-source.advaoptical.com/gitlab/anden/alpakka) project. Through the wool project
the output programming language for the code skeletons is defined. For that purpose a wool implementation can manipulate the generated output
data from the wool wrapper of the alpakka project as well as specifying the output format for the code skeletons.

## Getting Started

The following steps are guiding through a basic overview of the wools project and functional routine followed by a basic developer Guide on the subject
writing a new wool.

### General overview on the wool

Each wool inside the wools project represents a programming language or framework for which the alpakka project can create code skeletons. The wools
itself are structured in a tree like way, the root wool is the default from which all other wools are derived.
Each wool must be registered as part of the wools project, this registration can be performed in two different way. The persistent way is to perform
the registration during the wool installation, to do this the wool must be populated inside the setup.py of the wools project

### Initial developer Guide

#### required methods

## bullet based guide line

This section gives a bullet based overview of all steps which should be performed to implement and register a new wool as part of the wool project

* create new directory inside the wools project
	
* create the __init__.py
  * import the register_wool method of the alpakka project
  * call the register_wool method
  * implement the mandatory wools methods (generate_output, clear_data_structure and parse_config)

* create and implement the required classes for the wool specific data transformation
	
* register the wool temporary or permanent

