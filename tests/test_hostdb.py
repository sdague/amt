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

"""
test_hostdb
----------------------------------

Tests for `amt` module's wsman.py file
"""

import appdirs
import fixtures
import mock
import testtools

from amt import hostdb


class TestHostDB(testtools.TestCase):

    def setUp(self):
        super(TestHostDB, self).setUp()
        dirname = fixtures.TempDir()
        self.useFixture(dirname)
        self.out = self.useFixture(fixtures.StringStream('stdout'))
        self.useFixture(fixtures.MonkeyPatch('sys.stdout', self.out.stream))
        with mock.patch('appdirs.user_config_dir', return_value=dirname.path):
            self.db = hostdb.HostDB()

    @property
    def stdout(self):
        return self.out._details['stdout'].as_text()

    def test_list_servers(self):
        self.db.add_server("os1", "10.42.0.50", "foo")
        self.db.add_server("os2", "10.42.0.51", "foo")
        self.db.list_servers()
        self.assertEqual(self.stdout,
                        "Available servers (2):\n    os1\n    os2")

    def test_rm_servers(self):
        self.db.add_server("os1", "10.42.0.50", "foo")
        self.db.add_server("os2", "10.42.0.51", "foo")
        self.db.add_server("os3", "10.42.0.52", "foo")
        self.db.rm_server("os2")
        self.db.list_servers()
        self.assertEqual(self.stdout,
                        "Available servers (2):\n    os1\n    os3")

    def test_get_server(self):
        self.db.add_server("os1", "10.42.0.50", "foo")
        self.db.add_server("os2", "10.42.0.51", "foo")
        server = self.db.get_server("os1")
        self.assertEqual(server,
                         dict(host="10.42.0.50", passwd="foo"))
