# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import configparser
import os

import appdirs

appauthor = "sdague"
appname = "amtctrl"


class HostDB(object):
    def __init__(self):
        self.confdir = appdirs.user_config_dir(appname, appauthor)
        self.confname = os.path.join(self.confdir, 'hosts.cfg')
        self.config = configparser.ConfigParser()
        self.config.read(self.confname)

    def list_servers(self):
        print("Available servers (%d):" % len(self.config.sections()))
        for item in self.config.sections():
            print("    %s" % item)

    def add_server(self, name, host, passwd):
        self.config.add_section(name)
        self.config.set(name, 'host', host)
        self.config.set(name, 'passwd', passwd)
        # ensure the directory exists
        if not os.path.exists(self.confdir):
            os.makedirs(self.confdir)

        with open(self.confname, 'w') as f:
            self.config.write(f)

    def rm_server(self, name):
        self.config.remove_section(name)

        with open(self.confname, 'w') as f:
            self.config.write(f)

    def get_server(self, name):
        if self.config.has_section(name):
            return {
                'host': self.config.get(name, 'host'),
                'passwd': self.config.get(name, 'passwd')
            }
        else:
            print("No config found for server (%s), "
                  "perhaps you need to add one via ``amtctrl add``")
