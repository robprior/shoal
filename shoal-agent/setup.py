import os
import sys
from os.path import isfile, join, expanduser
from shoal_agent.__version__ import version

try:
    from setuptools import setup
except:
    try:
        from distutils.core import setup
    except:
        print "Couldn't use either setuputils or distutils. Install one of those."
        sys.exit(1)

data_files = []
config_files = ["shoal_agent.conf"]

if not os.geteuid() == 0:
    config_files_dir = expanduser("~/.shoal/")
else:
    config_files_dir = "/etc/shoal/"

    initd_dir = "/etc/init.d/"
    scripts_dir = "scripts/"
    initd_script = "shoal_agent"
    if not isfile(join(initd_dir, initd_script)):
        data_files += [(initd_dir, [join(scripts_dir, initd_script)])]


# check for preexisting config files
for config_file in config_files:
    if not isfile(join(config_files_dir, config_file)):
        data_files += [(config_files_dir, [config_file])]

setup(name='shoal-agent',
      version=version,
      license="'GPL3' or 'Apache 2'",
      install_requires=[
          'netifaces>=0.8',
          'pika>=0.9.9',
      ],
      description='A squid cache publishing and advertising tool designed to work in fast changing environments',
      author='Mike Chester',
      author_email='mchester@uvic.ca',
      url='http://github.com/hep-gc/shoal',
      packages=['shoal_agent'],
      scripts=['shoal-agent'],
      data_files=data_files,
)
