from setuptools import setup

# Setup the project
setup(
      name = "ssh-config-gen"
    , version = '0.1'
    , packages = ['ssh_config_gen']

    , install_requires =
      [ 'pyyaml'
      ]

    , extras_require =
      { 'tests' :
        [ 'noseOfYeti'
        ]
      }

    , entry_points =
      { 'console_scripts' :
        [ 'ssh-config-gen = ssh_config_gen.main:main'
        ]
      }

    # metadata
    , author = "Stephen Moore"
    , author_email = "stephen@delfick.com"
    , description = "Thing to generate an ssh config from"
    , license = "WTFPL"
    )

