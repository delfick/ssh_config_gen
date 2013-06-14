SSH Config Gen
==============

A little utility for generating an ssh config from a yaml specification.

Installation
------------

Either from pip::

	$ pip install ssh_config_gen

Or if you're developing::

	$ mkvirtualenv ssh_config_gen
	$ git clone git@github.com:delfick/ssh_config_gen.git
	$ cd ssh_config_gen
	$ pip install -e .
	$ pip install ssh_config_gen[tests]
	$ ./test.sh

Usage
-----

Make a yaml specification inside your ``~/.ssh`` folder:

.. code-block:: yaml

	verbatim: |
		Host *
		User bob
		ForwardX11 yes
	
	sections:
		work:
			hosts:
				computer:
					options:
						User: bob

				aws-{reason}-{count}:
					options:
						User: ubuntu
						IdentifyFile: ~/.ssh/aws-identity
					formatting:
						- format_options: {'reason': project1}
						  count: 3
						  alias: project1-{count}
						- format_options: {'reason': project2}
						  count: 4
						  alias: project2-{count}

		"another section":
			options:
				SomeOption: someValue
			hosts:
				elsewhere:
				somewhere:
					alias: a_nice_place

And then you run::

	$ ssh_config_gen --output ~/.ssh/config
	# Or use --template to specify where the template yaml is (it defaults to ~/.ssh/config.yaml)

If the output is ``~/.ssh/config`` it will first create a backup of that file
(other locations aren't good enough for a backup)

And generate a ssh config that looks like::

	Host *
	User bob
	ForwardX11 yes

	#########################
	###  ANOTHER SECTION
	#########################

	Host elsewhere
	HostName elsewhere
	SomeOption somevalue

	Host somewhere a_nice_place
	HostName somewhere
	SomeOption someValue

	#########################
	###  WORK
	#########################

	Host aws-project1-1 project1-1
	HostName aws-project1-1
	IdentifyFile ~/.ssh/aws-identity
	User ubuntu

	Host aws-project1-2 project1-2
	HostName aws-project1-2
	IdentifyFile ~/.ssh/aws-identity
	User ubuntu

	Host aws-project1-3 project1-3
	HostName aws-project1-3
	IdentifyFile ~/.ssh/aws-identity
	User ubuntu

	Host aws-project2-1 project2-1
	HostName aws-project2-1
	IdentifyFile ~/.ssh/aws-identity
	User ubuntu

	Host aws-project2-2 project2-2
	HostName aws-project2-2
	IdentifyFile ~/.ssh/aws-identity
	User ubuntu

	Host aws-project2-3 project2-3
	HostName aws-project2-3
	IdentifyFile ~/.ssh/aws-identity
	User ubuntu

	Host aws-project2-4 project2-4
	HostName aws-project2-4
	IdentifyFile ~/.ssh/aws-identity
	User ubuntu

	Host computer
	HostName computer
	User bob

Is it production ready?
=======================

It has few tests, less documentation and it was hacked together
in a few lazy hours on a friday night.

So probably not.

