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

from xml.etree import ElementTree

import pywsman

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

# XML generation routines


def _generate_enable_boot_config_input():
    """Generate Xmldoc as enable_boot_config input.

    This generates a Xmldoc used as input for enable_boot_config.

    :returns: Xmldoc.
    """
    method_input = "SetBootConfigRole_INPUT"
    namespace = CIM_BootService
    doc = pywsman.XmlDoc(method_input)
    root = doc.root()
    root.set_ns(namespace)

    child = root.add(namespace, 'BootConfigSetting', None)
    child.add(_ADDRESS, 'Address', _ANONYMOUS)

    grand_child = child.add(_ADDRESS, 'ReferenceParameters', None)
    grand_child.add(_WSMAN, 'ResourceURI', CIM_BootConfigSetting)
    g_grand_child = grand_child.add(_WSMAN, 'SelectorSet', None)
    g_g_grand_child = g_grand_child.add(_WSMAN, 'Selector',
                                        'Intel(r) AMT: Boot Configuration 0')
    g_g_grand_child.attr_add(_WSMAN, 'Name', 'InstanceID')
    root.add(namespace, 'Role', '1')
    return doc


def _change_boot_order_input(device):
    """Generate Xmldoc as change_boot_order input.

    This generates a Xmldoc used as input for change_boot_order.

    :param device: the boot device.
    :returns: Xmldoc.
    """
    method_input = "ChangeBootOrder_INPUT"
    namespace = CIM_BootConfigSetting
    doc = pywsman.XmlDoc(method_input)
    root = doc.root()
    root.set_ns(namespace)

    child = root.add(namespace, 'Source', None)
    child.add(_ADDRESS, 'Address', _ANONYMOUS)

    grand_child = child.add(_ADDRESS, 'ReferenceParameters', None)
    grand_child.add(_WSMAN, 'ResourceURI', CIM_BootSourceSetting)
    g_grand_child = grand_child.add(_WSMAN, 'SelectorSet', None)
    g_g_grand_child = g_grand_child.add(_WSMAN, 'Selector', device)
    g_g_grand_child.attr_add(_WSMAN, 'Name', 'InstanceID')
    return doc


def _generate_power_action_input(action):
    """Generate Xmldoc as set_power_state input.

    This generates a Xmldoc used as input for set_power_state.

    :param action: the power action.
    :returns: Xmldoc.
    """
    method_input = "RequestPowerStateChange_INPUT"
    address = 'http://schemas.xmlsoap.org/ws/2004/08/addressing'
    anonymous = ('http://schemas.xmlsoap.org/ws/2004/08/addressing/'
                 'role/anonymous')
    wsman = 'http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd'
    namespace = CIM_PowerManagementService

    doc = pywsman.XmlDoc(method_input)
    root = doc.root()
    root.set_ns(namespace)
    root.add(namespace, 'PowerState', action)

    child = root.add(namespace, 'ManagedElement', None)
    child.add(address, 'Address', anonymous)

    grand_child = child.add(address, 'ReferenceParameters', None)
    grand_child.add(wsman, 'ResourceURI', CIM_ComputerSystem)

    g_grand_child = grand_child.add(wsman, 'SelectorSet', None)
    g_g_grand_child = g_grand_child.add(wsman, 'Selector', 'ManagedSystem')
    g_g_grand_child.attr_add(wsman, 'Name', 'Name')
    return doc


class Client(object):
    """AMT client.

    Create a pywsman client to connect to the target server
    """
    def __init__(self, address, password, username='admin', protocol='http'):
        port = AMT_PROTOCOL_PORT_MAP[protocol]
        path = '/wsman'
        self.client = pywsman.Client(address, port, path, protocol,
                                     username, password)

    def _wsman_get(self, resource_uri, options=None):
        """Get target server info

        :param options: client options
        :param resource_uri: a URI to an XML schema
        :returns: XmlDoc object
        :raises: AMTFailure if get unexpected response.
        :raises: AMTConnectFailure if unable to connect to the server.
        """
        if options is None:
            options = pywsman.ClientOptions()
        doc = self.client.get(options, resource_uri)
        item = 'Fault'
        fault = xml_find(doc, _SOAP_ENVELOPE, item)
        if fault is not None:
            Exception("Call to AMT with URI %(uri)s failed:"
                              "got Fault %(fault)s" %
                      {'uri': resource_uri, 'fault': fault.text})
        return doc

    def _wsman_invoke(self, options, resource_uri, method, data=None):
        """Invoke method on target server

        :param options: client options
        :param resource_uri: a URI to an XML schema
        :param method: invoke method
        :param data: a XmlDoc as invoke input
        :returns: XmlDoc object
        :raises: AMTFailure if get unexpected response.
        :raises: AMTConnectFailure if unable to connect to the server.
        """
        if data is None:
            doc = self.client.invoke(options, resource_uri, method)
        else:
            doc = self.client.invoke(options, resource_uri, method, data)
        item = "ReturnValue"
        print doc
        return_value = xml_find(doc, resource_uri, item).text
        if return_value != '0':
            raise Exception(doc)
        return doc

    def power_on(self):
        """Power on the box."""
        # 2 is the magic enum for Power On
        payload = _generate_power_action_input('2')
        method = 'RequestPowerStateChange'
        options = pywsman.ClientOptions()
        options.add_selector('Name', 'Intel(r) AMT Power Management Service')
        self._wsman_invoke(
            options, CIM_PowerManagementService, method, payload)

    def power_off(self):
        """Power off the box."""
        # 8 is the magic enum for Power Cycle Off (Hard)
        payload = _generate_power_action_input('8')
        method = 'RequestPowerStateChange'
        options = pywsman.ClientOptions()
        options.add_selector('Name', 'Intel(r) AMT Power Management Service')
        print payload
        self._wsman_invoke(
            options, CIM_PowerManagementService, method, payload)

    def pxe_next_boot(self):
        """Sets the machine to PXE boot on it's next reboot

        Will default back to normal boot list on the reboot that follows.
        """
        # we need 2 cim calls for this, one to request a boot order
        # change... for unknown reasons.
        payload = _change_boot_order_input('Intel(r) AMT: Force PXE Boot')
        method = 'ChangeBootOrder'
        options = pywsman.ClientOptions()
        options.add_selector(
            'InstanceID', 'Intel(r) AMT: Boot Configuration 0')
        self._wsman_invoke(options, CIM_BootConfigSetting,
                            method, payload)

        method = 'SetBootConfigRole'
        doc = _generate_enable_boot_config_input()
        options = pywsman.ClientOptions()
        options.add_selector('Name', 'Intel(r) AMT Boot Service')
        return self._wsman_invoke(options, CIM_BootService,
                                  method, doc)

    def power_status(self):
        return self._wsman_get(CIM_AssociatedPowerManagementService)


def xml_find(doc, namespace, item):
    """Find the first element with namespace and item, in the XML doc

    :param doc: a doc object.
    :param namespace: the namespace of the element.
    :param item: the element name.
    :returns: the element object or None
    :raises: AMTConnectFailure if unable to connect to the server.
    """
    if doc is None:
        raise Exception()
    tree = ElementTree.fromstring(doc.root().string())
    query = ('.//{%(namespace)s}%(item)s' % {'namespace': namespace,
                                             'item': item})
    return tree.find(query)
