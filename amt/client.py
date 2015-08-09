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
#
# This file is heavily derived from the Ironic AMT driver at
# https://github.com/openstack/ironic/tree/master/ironic/drivers/modules/amt
#
# Thanks much for the hard work of people in that project to produce
# Open Source software that acts as one of the few bits of example
# code for this interface.

import xml.dom.minidom
from xml.etree import ElementTree

import requests
from requests.auth import HTTPDigestAuth

from amt import wsman


"""CIM schema urls

Conceptually you can query a Service, everything else is for update
only or modeling only. And, yes this is as redundant as it looks.
"""

SCHEMA_BASE = 'http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/'

CIM_AssociatedPowerManagementService = (SCHEMA_BASE +
                                        'CIM_AssociatedPowerManagementService')
CIM_PowerManagementService = (SCHEMA_BASE +
                              'CIM_PowerManagementService')
CIM_BootService = SCHEMA_BASE + 'CIM_BootService'

CIM_ComputerSystem = SCHEMA_BASE + 'CIM_ComputerSystem'
CIM_BootConfigSetting = SCHEMA_BASE + 'CIM_BootConfigSetting'
CIM_BootSourceSetting = SCHEMA_BASE + 'CIM_BootSourceSetting'

# Additional useful constants
_SOAP_ENVELOPE = 'http://www.w3.org/2003/05/soap-envelope'
_ADDRESS = 'http://schemas.xmlsoap.org/ws/2004/08/addressing'
_ANONYMOUS = 'http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous'
_WSMAN = 'http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd'


# magic ports to connect to
AMT_PROTOCOL_PORT_MAP = {
    'http': 16992,
    'https': 16993,
}


def pp_xml(body):
    """Pretty print format some XML so it's readable."""
    pretty = xml.dom.minidom.parseString(body)
    return pretty.toprettyxml(indent="  ")


class Client(object):
    """AMT client.

    Manage interactions with AMT host.
    """
    def __init__(self, address, password, username='admin', protocol='http'):
        port = AMT_PROTOCOL_PORT_MAP[protocol]
        path = '/wsman'
        self.uri = "%(protocol)s://%(address)s:%(port)s%(path)s" % {
            'address': address,
            'protocol': protocol,
            'port': port,
            'path': path}
        self.username = username
        self.password = password

    def power_on(self):
        """Power on the box."""
        payload = wsman.power_state_request(self.uri, "on")
        resp = requests.post(self.uri,
                             auth=HTTPDigestAuth(self.username, self.password),
                             data=payload)
        if resp.status_code == 200:
            rv = _return_value(resp.content, CIM_PowerManagementService)
            if rv == 0:
                return 0
            print(pp_xml(resp.content))
        else:
            print(resp.content)
            return 1

    def power_off(self):
        """Power off the box."""
        payload = wsman.power_state_request(self.uri, "off")
        resp = requests.post(self.uri,
                             auth=HTTPDigestAuth(self.username, self.password),
                             data=payload)
        if resp.status_code == 200:
            rv = _return_value(resp.content, CIM_PowerManagementService)
            if rv == 0:
                return 0
            print(pp_xml(resp.content))
        else:
            print(resp.content)
            return 1

    def power_cycle(self):
        """Power cycle the box."""
        payload = wsman.power_state_request(self.uri, "reboot")
        resp = requests.post(self.uri,
                             auth=HTTPDigestAuth(self.username, self.password),
                             data=payload)
        if resp.status_code == 200:
            rv = _return_value(resp.content, CIM_PowerManagementService)
            if rv == 0:
                return 0
            print(pp_xml(resp.content))
        else:
            print(resp.content)
            return 1

    def pxe_next_boot(self):
        """Sets the machine to PXE boot on it's next reboot

        Will default back to normal boot list on the reboot that follows.
        """
        payload = wsman.change_boot_to_pxe_request(self.uri)
        resp = requests.post(self.uri,
                             auth=HTTPDigestAuth(self.username, self.password),
                             data=payload)
        if resp.status_code == 200:
            print(pp_xml(resp.content))
            # rv = _return_value(resp.content, CIM_PowerManagementService)
            # if rv != 0:
            #     print(pp_xml(resp.content))
            #     return 1

        payload = wsman.enable_boot_config_request(self.uri)
        resp = requests.post(self.uri,
                             auth=HTTPDigestAuth(self.username, self.password),
                             data=payload)
        if resp.status_code == 200:
            print(pp_xml(resp.content))
            # rv = _return_value(resp.content, CIM_PowerManagementService)
            # if rv != 0:
            #     print(pp_xml(resp.content))
            #     return 1

    def power_status(self):
        payload = wsman.get_request(
            self.uri,
            CIM_AssociatedPowerManagementService)
        resp = requests.post(self.uri,
                             auth=HTTPDigestAuth(self.username, self.password),
                             data=payload)
        return pp_xml(resp.content)


def _return_value(content, ns):
    """Find the return value in a CIM response.

    The xmlns is needed because everything in CIM is a million levels
    of namespace indirection.
    """
    doc = ElementTree.fromstring(content)
    query = './/{%(ns)s}%(item)s' % {'ns': ns, 'item': 'ReturnValue'}
    rv = doc.find(query)
    return int(rv.text)
