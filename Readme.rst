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

	hosts:
		prefixed-*:
			proxied_by: some_jumphost
			add_hostname: False

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
					count: 2
					count_start: 3
					formatting:
						- format_options: {'reason': project1}
						  alias: project1-{count}
						- format_options: {'reason': project2}
						  alias: project2-{count}

				a-jumphost:
					alias: jh
					proxying:
						a-server-{count}:
							count: 4

		"another section":
			options:
				SomeOption: someValue
			simple:
				short: long_host_name-1.many.domain.names
			hosts:
				elsewhere:
				somewhere:
					alias: a_nice_place

				place:
					proxied_by: another_place

				with_leading_zero-{count:02d}:
					count: 2

And then you run::

	$ ssh_config_gen --output ~/.ssh/config
	# Or use --template to specify where the template yaml is (it defaults to ~/.ssh/config.yaml)

If the output is ``~/.ssh/config`` it will first create a backup of that file
(other locations aren't good enough for a backup)

And generate a ssh config that looks like::

	Host *
	User bob
	ForwardX11 yes

	Host prefixed-*
	ProxyCommand ssh ssh -q some_jumphost -W %h:%p

	#########################
	###  ANOTHER SECTION
	#########################

	Host elsewhere
	HostName elsewhere
	SomeOption someValue

	Host place
	HostName place
	ProxyCommand ssh -q another_place -W %h:%p
	SomeOption someValue

	Host somewhere a_nice_place
	HostName somewhere
	SomeOption someValue

	Host with_leading_zero-01
	HostName with_leading_zero-01
	SomeOption someValue

	Host with_leading_zero-02
	HostName with_leading_zero-02
	SomeOption someValue

	Host long_host_name-1.many.domain.names short
	HostName long_host_name-1.many.domain.names
	SomeOption someValue

	#########################
	###  WORK
	#########################

	Host a-jumphost jh
	HostName a-jumphost

	Host a-server-1
	HostName a-server-1
	ProxyCommand ssh -q a-jumphost -W %h:%p

	Host a-server-2
	HostName a-server-2
	ProxyCommand ssh -q a-jumphost -W %h:%p

	Host a-server-3
	HostName a-server-3
	ProxyCommand ssh -q a-jumphost -W %h:%p

	Host a-server-4
	HostName a-server-4
	ProxyCommand ssh -q a-jumphost -W %h:%p

	Host aws-project1-3 project1-3
	HostName aws-project1-3
	IdentifyFile ~/.ssh/aws-identity
	User ubuntu

	Host aws-project1-4 project1-4
	HostName aws-project1-4
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

