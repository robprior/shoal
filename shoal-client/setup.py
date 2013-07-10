import os
import sys
from os.path import isfile, join
from shoal_client.__version__ import version

try:
    from setuptools import setup
except:
    try:
        from distutils.core import setup
    except:
        print "Couldn't use either setuputils or distutils. Install one of those."
        sys.exit(1)

data_files = []
config_files = ["shoal_client.conf"]

if not os.geteuid() == 0:
    config_files_dir = os.path.expanduser("~/.shoal/")
else:
    config_files_dir = "/etc/shoal/"
    initd_dir = "/etc/init.d/"
    scripts_dir = "scripts/"
    initd_script = "shoal_client"

    # Check if init.d script already exists, otherwise add it.
    if not isfile(join(initd_dir, initd_script)):
        data_files += [(initd_dir, join(scripts_dir, initd_script))]

# check for preexisting config file
for config_file in config_files:
    if not isfile(join(config_files_dir, config_file)):
        data_files += [(config_files_dir, [config_file])]

setup(name='shoal-client',
      version=version,
      license="'GPL3' or 'Apache 2'",
      install_requires=[],
      description='A squid cache publishing and advertising tool designed to work in fast changing environments',
      author='Mike Chester',
      author_email='mchester@uvic.ca',
      url='http://github.com/hep-gc/shoal',
      packages=['shoal_client'],
      scripts=['shoal-client'],
      data_files=data_files,
)
