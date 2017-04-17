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

# This file is a hack and slash implementation of just-enough-wsman
# needed for the commands in amtctrl.
#
# The only python implementation is a set of bindings on openwsman
# library, which is written in C. wsman is just about building /
# parsing XML and sending HTTP requests (with digest auth). Shifting
# out to a C library to do all of this is sub optimal, when this is
# largely built into python. The python openwsman bindings are also
# not straight forward to build, so the code is hard to test, and
# quite non portable.

import uuid
from xml.etree import ElementTree as ET

from amt import client


# Additional useful constants
NS_SOAP_ENV = 'http://www.w3.org/2003/05/soap-envelope'
NS_WS_ADDR = 'http://schemas.xmlsoap.org/ws/2004/08/addressing'
NS_WSMAN = 'http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd'

_ANONYMOUS = 'http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous'
METHOD_GET = "http://schemas.xmlsoap.org/ws/2004/09/transfer/Get"
METHOD_PUT = "http://schemas.xmlsoap.org/ws/2004/09/transfer/Put"


ET.register_namespace('s', NS_SOAP_ENV)
ET.register_namespace('wsa', NS_WS_ADDR)
ET.register_namespace('wsman', NS_WSMAN)

# Pre-define QName wrapper which consist of {uri}local
_QN_MUSTUNDERSTAND = ET.QName(NS_SOAP_ENV, 'mustUnderstand')
_QN_ENVELOPE = ET.QName(NS_SOAP_ENV, 'Envelope')
_QN_HEADER = ET.QName(NS_SOAP_ENV, 'Header')
_QN_ACTION = ET.QName(NS_WS_ADDR, 'Action')
_QN_TO = ET.QName(NS_WS_ADDR, 'To')
_QN_RESOURCEURI = ET.QName(NS_WSMAN, 'ResourceURI')
_QN_BODY = ET.QName(NS_SOAP_ENV, 'Body')
_QN_MESSAGE = ET.QName(NS_WS_ADDR, 'MessageID')
_QN_REPLYTO = ET.QName(NS_WS_ADDR, 'ReplyTo')
_QN_ADDRESS = ET.QName(NS_WS_ADDR, 'Address')
_QN_SELECTORSET = ET.QName(NS_WSMAN, 'SelectorSet')
_QN_SELECTOR = ET.QName(NS_WSMAN, 'Selector')
_QN_NAME = ET.QName(NS_WSMAN, 'Name')
_QN_REFERENCEPARAMETERS = ET.QName(NS_WS_ADDR, 'ReferenceParameters')


POWER_STATES = {
    'on': 2,
    'off': 8,
    'standby': 4,
    'reboot': 5,
}


# Valid boot devices
BOOT_DEVICES = {
    'pxe': 'Intel(r) AMT: Force PXE Boot',
    'hd': 'Intel(r) AMT: Force Hard-drive Boot',
    'cd': 'Intel(r) AMT: Force CD/DVD Boot',
}

FRIENDLY_POWER_STATE = {v: k for (k, v) in POWER_STATES.items()}

def friendly_power_state(state):
    return FRIENDLY_POWER_STATE.get(int(state), 'unknown')


def get_request(host_uri, resource_uri):
    """ Get AMT server info

    :param host_uri: a URI to host
    :param resource_uri: a URI to an XML schema
    :returns: XML string
    """
    xml = wsman_get(host_uri, resource_uri)
    return ET.tostring(xml, encoding="UTF-8")


def power_state_request(host_uri, power_state):
    """ Change AMT Server power state

    :param host_uri: a URI to host
    :param power_state: target power state
    :returns: XML string
    """
    method = 'RequestPowerStateChange'
    selectorset = _create_selectorset('Name',
                                      'Intel(r) AMT Power Management Service')
    method_input = _generate_power_action_input(method, POWER_STATES[power_state])
    xml = wsman_invoke(host_uri, client.CIM_PowerManagementService, method,
                       selectorset, method_input)
    return ET.tostring(xml, encoding="UTF-8")


def enable_remote_kvm(uri, passwd):
    stub = """<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd">
<s:Header>
<wsa:Action s:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2004/09/transfer/Put</wsa:Action>
<wsa:To s:mustUnderstand="true">%(uri)s</wsa:To>
<wsman:ResourceURI s:mustUnderstand="true">http://intel.com/wbem/wscim/1/ips-schema/1/IPS_KVMRedirectionSettingData</wsman:ResourceURI>
<wsa:MessageID s:mustUnderstand="true">uuid:%(uuid)s</wsa:MessageID>
<wsa:ReplyTo>
    <wsa:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
</wsa:ReplyTo>
</s:Header>
<s:Body>
<g:IPS_KVMRedirectionSettingData xmlns:g="http://intel.com/wbem/wscim/1/ips-schema/1/IPS_KVMRedirectionSettingData">
<g:DefaultScreen>0</g:DefaultScreen>
<g:ElementName>Intel(r) KVM Redirection Settings</g:ElementName>
<g:EnabledByMEBx>true</g:EnabledByMEBx>
<g:InstanceID>Intel(r) KVM Redirection Settings</g:InstanceID>
<g:Is5900PortEnabled>true</g:Is5900PortEnabled>
<g:OptInPolicy>false</g:OptInPolicy>
<g:RFBPassword>%(passwd)s</g:RFBPassword>
<g:SessionTimeout>0</g:SessionTimeout>
</g:IPS_KVMRedirectionSettingData>
</s:Body>
</s:Envelope>"""  # noqa
    return stub % {'uri': uri, 'passwd': passwd, 'uuid': uuid.uuid4()}


def kvm_redirect(uri):
    stub = """<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:n1="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_KVMRedirectionSAP">
<s:Header>
<wsa:Action s:mustUnderstand="true">http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_KVMRedirectionSAP/RequestStateChange</wsa:Action>
<wsa:To s:mustUnderstand="true">%(uri)s</wsa:To>
<wsman:ResourceURI s:mustUnderstand="true">http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_KVMRedirectionSAP</wsman:ResourceURI>
<wsa:MessageID s:mustUnderstand="true">uuid:%(uuid)s</wsa:MessageID>
<wsa:ReplyTo>
<wsa:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
</wsa:ReplyTo>
</s:Header>
<s:Body>
<n1:RequestStateChange_INPUT>
<n1:RequestedState>2</n1:RequestedState>
</n1:RequestStateChange_INPUT>
</s:Body></s:Envelope>"""  # noqa
    return stub % {'uri': uri, 'uuid': uuid.uuid4()}


def change_boot_to_pxe_request(uri):
    return change_boot_order_request(
        uri, boot_device='pxe')


def change_boot_order_request(uri, boot_device):
    assert boot_device in BOOT_DEVICES
    stub = """<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:n1="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_BootConfigSetting">
<s:Header>
<wsa:Action s:mustUnderstand="true">http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_BootConfigSetting/ChangeBootOrder</wsa:Action>
<wsa:To s:mustUnderstand="true">%(uri)s</wsa:To>
<wsman:ResourceURI s:mustUnderstand="true">http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_BootConfigSetting</wsman:ResourceURI>
<wsa:MessageID s:mustUnderstand="true">uuid:%(uuid)s</wsa:MessageID>
<wsa:ReplyTo>
    <wsa:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
</wsa:ReplyTo>
<wsman:SelectorSet>
   <wsman:Selector Name="InstanceID">Intel(r) AMT: Boot Configuration 0</wsman:Selector>
</wsman:SelectorSet>
</s:Header>
<s:Body>
  <n1:ChangeBootOrder_INPUT>
     <n1:Source>
        <wsa:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
        <wsa:ReferenceParameters>
            <wsman:ResourceURI>http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_BootSourceSetting</wsman:ResourceURI>
            <wsman:SelectorSet>
                <wsman:Selector wsman:Name="InstanceID">%(boot_device)s</wsman:Selector>
            </wsman:SelectorSet>
         </wsa:ReferenceParameters>
     </n1:Source>
   </n1:ChangeBootOrder_INPUT>
</s:Body></s:Envelope>"""  # noqa
    return stub % {'uri': uri, 'uuid': uuid.uuid4(),
                   'boot_device': BOOT_DEVICES[boot_device]}


def enable_boot_config_request(uri):
    stub = """<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:n1="http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_BootService">
<s:Header>
<wsa:Action s:mustUnderstand="true">http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_BootService/SetBootConfigRole</wsa:Action>
<wsa:To s:mustUnderstand="true">%(uri)s</wsa:To>
<wsman:ResourceURI s:mustUnderstand="true">http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_BootService</wsman:ResourceURI>
<wsa:MessageID s:mustUnderstand="true">uuid:%(uuid)s</wsa:MessageID>
<wsa:ReplyTo><wsa:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address></wsa:ReplyTo>
<wsman:SelectorSet>
    <wsman:Selector Name="Name">Intel(r) AMT Boot Service</wsman:Selector>
</wsman:SelectorSet>
</s:Header>
<s:Body>
<n1:SetBootConfigRole_INPUT>
    <n1:BootConfigSetting>
        <wsa:Address>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:Address>
        <wsa:ReferenceParameters>
             <wsman:ResourceURI>http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_BootConfigSetting</wsman:ResourceURI>
             <wsman:SelectorSet>
                  <wsman:Selector wsman:Name="InstanceID">Intel(r) AMT: Boot Configuration 0</wsman:Selector>
             </wsman:SelectorSet>
        </wsa:ReferenceParameters>
    </n1:BootConfigSetting>
    <n1:Role>1</n1:Role>
</n1:SetBootConfigRole_INPUT>
</s:Body></s:Envelope>"""  # noqa
    return stub % {'uri': uri, 'uuid': uuid.uuid4()}


def wsman_get(host_uri, resource_uri, selectorset=None):
    """ Get target server info

    :param host_uri: a URI to host
    :param resource_uri: a URI to an XML schema
    :param selectorset: selectorset option
    :returns: XML element
    """
    request = _create_soap_request(host_uri, resource_uri,
                                   METHOD_GET, selectorset)
    return request


def wsman_invoke(host_uri, resource_uri, method,
                 selectorset=None, method_input=None):
    """ invoke method on target server

    :param host_uri: a URI to host
    :param resource_uri: a URI to an XML schema
    :param method: invoke method
    :param selectorset: selectorset option
    :param method_input: a XML element as invoke input
    :returns: XML element
    """
    action = resource_uri+'/'+method
    request = _create_soap_request(host_uri, resource_uri, action,
                                   selectorset, method_input)
    return request


def _generate_power_action_input(method, power_state):
    """ Create Power State Change Input

    :param method: Input method name
    :param power_state: target power_state
    :returns: XML element
    """
    ns = client.CIM_PowerManagementService
    el_input = _create_method_input(ns, method)
    qn_power = ET.QName(ns, 'PowerState')
    el_power = ET.SubElement(el_input, qn_power)
    el_power.text = str(power_state)
    el_selector = _create_selectorset('Name', 'ManagedSystem')
    qn_reference = ET.QName(ns, 'ManagedElement')
    el_reference = _create_reference(qn_reference, client.CIM_ComputerSystem,
                                     el_selector)
    el_input.append(el_reference)
    return el_input


def _create_method_input(ns, method):
    """ Create Input method element

    :param ns: namepace of element
    :method: Input method name
    :returns: XML element
    """
    qn_method = ET.QName(ns, method+'_INPUT')
    return ET.Element(qn_method)


def _create_soap_request(host_uri, resource_uri, method,
                         selectorset=None, method_input=None):
    """ Create a soap request using ElementTree

    :param host_uri: a URI to host
    :param resource_uri: a URI to an XML schema
    :param method: calling method
    :param selectorset: selectorset option
    :param method_input: a XML element as input
    :returns: XML element
    """

    root = ET.Element(_QN_ENVELOPE)
    header = _create_header_element(host_uri, resource_uri, method,
                                    selectorset)
    root.append(header)
    body = _create_body_element(method_input)
    root.append(body)
    return root


def _create_header_element(host_uri, resource_uri, method, selectorset):
    """ Create a Header XML element

    :param host_uri: a URI to host
    :param resource_uri: a URI to an XML schema
    :param method: calling method
    :param selectorset: selectorset option
    :returns: XML element
    """
    header = ET.Element(_QN_HEADER)
    el_action = ET.SubElement(header, _QN_ACTION)
    el_action.set(_QN_MUSTUNDERSTAND, 'true')
    el_action.text = method

    el_to = ET.SubElement(header, _QN_TO)
    el_to.text = host_uri
    el_to.set(_QN_MUSTUNDERSTAND, 'true')

    el_resourceURI = ET.SubElement(header, _QN_RESOURCEURI)
    el_resourceURI.set(_QN_MUSTUNDERSTAND, 'true')
    el_resourceURI.text = resource_uri

    el_messageID = ET.SubElement(header, _QN_MESSAGE)
    el_messageID.set(_QN_MUSTUNDERSTAND, 'true')
    el_messageID.text = 'uuid:%s' % uuid.uuid4()

    el_replyto = ET.SubElement(header, _QN_REPLYTO)
    el_address = ET.SubElement(el_replyto, _QN_ADDRESS)
    el_address.text = _ANONYMOUS

    if selectorset is not None:
        header.append(selectorset)

    return header


def _create_body_element(method_input=None):
    """ Create a Body XML element

    :param method_input: a XML element as input
    :returns: XML element
    """
    body = ET.Element(_QN_BODY)
    if method_input is not None:
        body.append(method_input)
    return body


def _create_selectorset(name, item):
    """ Create selectorset XML element

    :param name: the value of selector's 'Name' attribute
    :param item: the value of selector
    :returns: XML element
    """
    # TODO name seems related to item according AMT SDK reference,
    # need to find the relationship
    el_selectorset = ET.Element(_QN_SELECTORSET)
    el_selector = ET.SubElement(el_selectorset, _QN_SELECTOR)
    el_selector.set(_QN_NAME, name)
    el_selector.text = item
    return el_selectorset


def _create_reference(qname, uri, el_selectorset):
    """ Create a reference XML element:

    :param qname: the QName of the reference
    :param uri: the value of referenceURI
    :param el_selectorset: a selectorset XML element
    :returns: XML element
    """
    el_reference = ET.Element(qname)
    el_address = ET.SubElement(el_reference, _QN_ADDRESS)
    el_address.text = _ANONYMOUS
    el_reference_parameters = ET.SubElement(el_reference,
                                            _QN_REFERENCEPARAMETERS)
    el_resourceuri = ET.SubElement(el_reference_parameters,
                                   _QN_RESOURCEURI)
    el_resourceuri.text = uri
    el_reference_parameters.append(el_selectorset)
    return el_reference

# Local Variables:
# eval: (whitespace-mode -1)
# End:
