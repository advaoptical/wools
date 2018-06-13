# Wools

Is a python project which extends the [alpakka](https://mgn-s-at-source.advaoptical.com/gitlab/anden/alpakka) project. Through the wool project
the output programming language for the code skeletons is defined. For that purpose a wool implementation can manipulate the generated output
data from the wool wrapper of the alpakka project as well as specifying the output format for the code skeletons.

## Getting Started

The following steps whill guide 

### General overview on the wool

### Initial developer Guide

#### required methods

The *alpakka* project provides the following command line options

* '--alpakka-output-path' (**required**)
	- output path for the generated classes
	- indicates the root directory of the java/maven project
	
* '-w; --wool' (**required**)
	- The Wool to use for knitting the code
	- indicates to wool, which is representing the different programming languages and frameworks
	
* '--wool-package-prefix'
	- package prefix to be prepended to the generated classes
	- could be for example the java name prefix like com.example
	
* '--akka-beans-only'
	- @Thomas was macht diese Option eigentlich?
	
* '-i; --interactive'
	- run alpakka in interactive mode by starting an IPython shell before template generation

