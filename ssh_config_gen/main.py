import datetime
import argparse
import shutil
import yaml
import sys
import os

from ssh_config_gen.gen import Section, BadTemplateException

home_dir = os.path.expanduser("~")

def create_backup(location):
    """Copy location to a backup next to it"""
    postfix = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    backup_location = "{}.{}".format(location, postfix)
    shutil.copyfile(location, backup_location)
    return backup_location

def get_parser():
    """Make parser for commandline arguments"""
    parser = argparse.ArgumentParser(description="SSH config generator")

    parser.add_argument("--template"
        , help = "The template yaml to base the ssh config off"
        , default = os.path.join(home_dir, '.ssh', 'config.yaml')
        , type = argparse.FileType('r')
        )

    parser.add_argument("--output"
        , help = "Where to write the generated ssh config to"
        , default = sys.stdout
        )

    return parser

def make_ssh_config(yaml):
    """Return generated ssh config from provided yaml"""
    blocks = Section(yaml).generate()
    return '\n\n'.join(list(blocks))

def main(argv=None):
    """Create the ssh config and write it to our output"""
    parser = get_parser()
    args = parser.parse_args(argv)
    output_location = args.output
    if not isinstance(output_location, basestring):
        output_location = output_location.name

    # Create our new config
    try:
        options = yaml.load(args.template)
    except yaml.parser.ParserError as error:
        raise BadTemplateException("Invalid yaml! {}".format(error))

    generated = make_ssh_config(options)

    # Make sure to backup the config if that's what we're writing to
    backup_location = None
    config_location = os.path.join(home_dir, '.ssh', 'config')
    if os.path.abspath(output_location) == config_location:
        backup_location = create_backup(config_location)

    # Turn ~/.ssh/config into writable file after it's backed up
    output = args.output
    if isinstance(args.output, basestring):
        output = open(args.output, 'w')

    # Write to the output
    try:
        output.write(generated)
    except:
        # If we're writing to the config and it failed
        # copy back from the backup incase it's half way through
        # Or something annoying like that
        shutil.copy(backup_location, config_location)
        raise

def catcher_main():
    """Run main with try..excepts to make nicer error messages to console"""
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except BadTemplateException as error:
        print "Failed to parse the template!"
        print "============================="
        print error
        sys.exit(1)

if __name__ == '__main__':
    catcher_main()

