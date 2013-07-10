#Shoal Agent v0.6.X README

##Basic Commands
With the basic `shoal_agent` initd script you can do the following:
- Start Shoal Agent
 - `service shoal_agent start`
- Stop Shoal Agent
 - `service shoal_agent stop` 
- Restart Shoal Agent
 - `service shoal_agent reload` 
- Status of Shoal Agent
 - `service shoal_agent status` 
- Force restart Shoal Agent
 - `service shoal_agent force-restart`

##Installation

 _**Note**: Requires you have a working RabbitMQ AMQP Server, and Python 2.6+_

###Using Pip

1. `pip install shoal-agent` or `sudo pip install shoal-agent`
2. Check settings in either `~/.shoal/shoal_agent.conf` or `/etc/shoal/shoal_agent.conf` and update as needed.

**If sudo was used**

1. `chmod +x /etc/init.d/shoal_agent`
 - You may need to adjust the `EXECUTABLEPATH` and `PYTHON` variables in `/etc/init.d/shoal_agent` to point at the proper paths.

2. Add `shoal_client` to start on boot, via `chkconfig` or similiar service.
 1. `chkconfig --add shoal_agent`
 2. `chkconfig shoal_agent on`

###Using Git
1. `git clone git://github.com/hep-gc/shoal.git`
2. `cd shoal/shoal-agent/`
3. `python setup.py install` or `sudo python setup.py install`
4. Check settings in either `~/.shoal/shoal_agent.conf` or `/etc/shoal/shoal_agent.conf` and update as needed.

**If sudo was used**

1. `chmod +x /etc/init.d/shoal_agent`
 - You may need to adjust the `EXECUTABLEPATH` and `PYTHON` variables in `/etc/init.d/shoal_agent` to point at the proper paths.

2. Add `shoal_client` to start on boot, via `chkconfig` or similiar service.
 1. `chkconfig --add shoal_agent`
 2. `chkconfig shoal_agent on`
