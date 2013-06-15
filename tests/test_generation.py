# coding: spec

from ssh_config_gen.main import make_ssh_config

from textwrap import dedent
import unittest
import yaml
import re

describe unittest.TestCase, "Generating ssh configs":
	def assertExpectedGeneration(self, template, expected):
		"""Make sure the template generates what we expect"""
		def replace_indentation(match):
			"""I don't want to mix tabs and spaces in my test file and I'm keeping tabs by default and yaml complains about tabbed indentation"""
			groups = match.groups()
			return '{}{}'.format('    ' * len(groups[0]), groups[1])

		template = '\n'.join(re.sub('^(\t*)(.*)', replace_indentation, line) for line in dedent(template).strip().split('\n'))
		expected = dedent(expected).strip()
		generated = make_ssh_config(yaml.load(template)).strip()

		things = {'border':'=' * 80, 'template': template, 'expected': expected, 'got': generated}
		error_msg = "\n{border}\nTEMPLATE:\n{border}\n{template}\n\n{border}\nEXPECTED:\n{border}\n{expected}\n\n{border}\nGOT:\n{border}\n{got}\n".format(**things)

		self.assertEqual(generated, expected, error_msg)

	it "has verbatim option":
		template = """
		verbatim: |
			Host *
			User bob
			ServerAliveInterval 60
		"""

		expected = """
		Host *
		User bob
		ServerAliveInterval 60
		"""

		self.assertExpectedGeneration(template, expected)

	it "has hosts":
		template = """
		hosts:
			blah:
				options:
					User: tim
			meh:
				options:
					ForwardX11: yes
		"""

		expected = """
		Host blah
		HostName blah
		User tim

		Host meh
		HostName meh
		ForwardX11 yes
		"""

		self.assertExpectedGeneration(template, expected)

	it "has sections":
		template = """
		sections:
			blah:
				hosts:
					stuff:
						options:
							User: tim
			meh:
				hosts:
					tree:
						options:
							ForwardX11: yes
		"""

		expected = """
		#########################
		###  BLAH
		#########################

		Host stuff
		HostName stuff
		User tim

		#########################
		###  MEH
		#########################

		Host tree
		HostName tree
		ForwardX11 yes
		"""

		self.assertExpectedGeneration(template, expected)

	it "has inheritance":
		template = """
		options:
			User: tim
		sections:
			blah:
				options:
					ForwardX11: yes

				hosts:
					differentUser:
						options:
							User: bob

					noForwardX11:
						options:
							ForwardX11: no

			meh:
				hosts:
					anotherDifferentUser:
						options:
							User: Jo
						proxying:
							anotherPlace:
		"""

		expected = """
		#########################
		###  BLAH
		#########################

		Host differentUser
		HostName differentUser
		ForwardX11 yes
		User bob

		Host noForwardX11
		HostName noForwardX11
		ForwardX11 no
		User tim

		#########################
		###  MEH
		#########################

		Host anotherDifferentUser
		HostName anotherDifferentUser
		User Jo

		Host anotherPlace
		HostName anotherPlace
		ProxyCommand ssh -q anotherDifferentUser -W %h:%p
		User Jo
		"""

		self.assertExpectedGeneration(template, expected)

	it "has verbatim at all levels":
		template = """
		verbatim: |
			Host *
			Blah stuff
		options:
			User: tim
		sections:
			blah:
				verbatim: |
					Host things-*
					creativity none

			meh:
				hosts:
					place:
		"""

		expected = """
		Host *
		Blah stuff

		#########################
		###  BLAH
		#########################

		Host things-*
		creativity none

		#########################
		###  MEH
		#########################

		Host place
		HostName place
		User tim
		"""

		self.assertExpectedGeneration(template, expected)

	it "simple aliased hosts":
		template = """
		simple:
			a: b
			c: d
		"""

		expected = """
		Host b a
		HostName b

		Host d c
		HostName d
		"""

		self.assertExpectedGeneration(template, expected)

	it "can pass format_options from section to hosts":
		template = """
		format_options:
			prefix: stuff

		hosts:
			"{prefix}-blah-{count}":
				count: 2
		"""

		expected = """
		Host stuff-blah-1
		HostName stuff-blah-1

		Host stuff-blah-2
		HostName stuff-blah-2
		"""

		self.assertExpectedGeneration(template, expected)

	describe "Hosts":
		def assertExpectedGenerationHosts(self, template, expected):
			template = dedent("""
			hosts:
				{}
			""").format('\n\t'.join(line for line in dedent(template).strip().split('\n')))
			self.assertExpectedGeneration(template, expected)

		it "can have an alias":
			template = """
			blah:
				alias: stuff
			"""

			expected = """
			Host blah stuff
			HostName blah
			"""

			self.assertExpectedGenerationHosts(template, expected)

		it "can have format options":
			template = """
			blah-{typ}-{loc}:
				alias: stuff-{typ}-{loc}
				formatting:
					- format_options:
						typ: one
						loc: forest

					- format_options:
						typ: two
						loc: office
			"""

			expected = """
			Host blah-one-forest stuff-one-forest
			HostName blah-one-forest

			Host blah-two-office stuff-two-office
			HostName blah-two-office
			"""

			self.assertExpectedGenerationHosts(template, expected)

		it "can do things with the formatted hosts":
			template = """
			blah-{typ}-{loc}:
				alias: stuff-{typ}-{loc}
				formatting:
					- format_options:
						typ: one
						loc: forest
					  options:
						ForwardX11: yes

					- format_options:
						typ: two
						loc: office
					  proxying:
						things:
							alias: things-alias-{loc}
							options:
								User: Reggie
			"""

			expected = """
			Host blah-one-forest stuff-one-forest
			HostName blah-one-forest
			ForwardX11 yes

			Host blah-two-office stuff-two-office
			HostName blah-two-office

			Host things things-alias-office
			HostName things
			ProxyCommand ssh -q blah-two-office -W %h:%p
			User Reggie
			"""

			self.assertExpectedGenerationHosts(template, expected)

		it "can have ranges of hosts":
			template = """
			blah-{count}:
				count: 5

			meh-{count}:
				count: 2
				count_start: 2

			meh-{typ}-{count}:
				alias: "{typ}-{count}"
				formatting:
					- format_options: {typ: 'one'}
					  count: 2
					- format_options: {typ: 'two'}
					  count: 1
			"""

			expected = """
			Host blah-1
			HostName blah-1

			Host blah-2
			HostName blah-2

			Host blah-3
			HostName blah-3

			Host blah-4
			HostName blah-4

			Host blah-5
			HostName blah-5

			Host meh-2
			HostName meh-2

			Host meh-3
			HostName meh-3

			Host meh-one-1 one-1
			HostName meh-one-1

			Host meh-one-2 one-2
			HostName meh-one-2

			Host meh-two-1 two-1
			HostName meh-two-1
			"""

			self.assertExpectedGenerationHosts(template, expected)

		it "has a proxied_by option":
			template = """
			blah:
				proxied_by: a-place
			"""

			expected = """
			Host blah
			HostName blah
			ProxyCommand ssh -q a-place -W %h:%p
			"""

			self.assertExpectedGenerationHosts(template, expected)

		it "supports 0 based counts":
			template = """
			blah-{count:02d}:
				alias: blah-{count}
				count: 2
			"""

			expected = """
			Host blah-01 blah-1
			HostName blah-01

			Host blah-02 blah-2
			HostName blah-02
			"""

			self.assertExpectedGenerationHosts(template, expected)

		it "can be told not to add a hostname":
			template = """
			prefixed-* *-postfixed:
				proxied_by: a_jh
				add_hostname: False
			"""

			expected = """
			Host prefixed-* *-postfixed
			ProxyCommand ssh -q a_jh -W %h:%p
			"""

			self.assertExpectedGenerationHosts(template, expected)

