===============================
Python AMT Tools
===============================

.. image:: https://img.shields.io/travis/sdague/amt.svg
        :target: https://travis-ci.org/sdague/amt

.. image:: https://img.shields.io/pypi/v/amt.svg
        :target: https://pypi.python.org/pypi/amt


Tools for interacting with Intel's Active Management Technology

Background
----------

AMT is a light weight hardware control interface put into some Intel
based laptops and desktops as a tool for corporate fleets to manage
hardware. It provides the basics of power control, as well as remote
console via VNC. It functions by having a dedicated service processor
sniff traffic off the network card on specific ports before it gets to
the operating system. Some versions of Intel NUC boxes have AMT, which
make them ideal candidates for building a reasonable cluster in your
basement.

There was once a tool called ``amttool`` which let you interact with
these systems from Linux. This used the SOAP interface to AMT. That
was removed in v9 of the firmware, which means it no longer works with
modern AMT in the field.

The interface that remains is CIM, a standard from the DMTF that
builds XML models for all the things. There exist very few examples
for how to make this work on the internet, with one exception: the
OpenStack Baremetal (Ironic) service. It has native support for AMT
hardware control.

This project is derivative work from Ironic. The heavy lifting of
understanding all the CIM magic incantations, and oh the magic they
are, comes from that code. Refactored for a more minimal usage.

Hardware that includes AMT
--------------------------

AMT is branded as vPro in products by Intel. It is found in many Intel
based laptops. There are also specific models of Intel NUC that
include vPro.

* `Intel NUC KIT Core Processor BLKNUC5I5MYHE <http://amzn.to/1OZshhF>`_

This code gets tested with ``5i5MYHE`` NUCs as well as an older NUC
that I have laying around.

Some motherboards includes vPro. Listed below can run this code:

* `GIGABYTE MW50-SV0 <https://www.gigabyte.com/Server-Motherboard/MW50-SV0-rev-10#ov>`_


Configuring AMT
---------------

AMT must be enabled in the BIOS before it can be used externally. This
is done by pressing ``Ctrl-P`` during initial boot. Initial user /
pass is ``admin`` / ``admin``. You will be required to create a new
admin password that has at least 1: number, capital letter, and non
alphanumeric symbol.

One you do that, reboot and you are on your way.

amtctrl
-------

The ``amt`` library installs binaries ``amtctrl``  and ``amthostdb`` for working
with AMT enabled machines.

machine enrollment
~~~~~~~~~~~~~~~~~~

To simplify the control commands ``amthostdb`` has a machine
registry. New machines are added via:

   amthostdb add <name> <address> <amtpassword>

You can see a list of all machines with:

   amthostdb list

And remove an existing machine with:

   amthostdb rm <name>


controlling machines
~~~~~~~~~~~~~~~~~~~~

Once machines are controlled you have a number of options exposed:

   amtctrl <name> <command> [subcommand] [arguments]

Command is one of:

* power on - power on the machine

* power off - power off the machine

* power reboot - power cycle the machine

* power status - return power status as an ugly CIM blob (TODO: make this better)

* pxeboot - set the machine to pxeboot the next time it reboots, and
  reboot the machine. This is extremely useful if you have install
  automation on pxeboot.

* pki list certs - list PKI certificates

* pki list keys - list PKI keys

* pki add cert <filename> - add PKI certificate

* pki add cert -t <filename> - add trusted PKI certificate

* pki add key <filename> - add PKI RSA key

* pki generate 2048 - generate 2048-bit PKI RSA key

* pki request <filename> <id> - sign a PKI CSR

* pki rm cert <id> - remove PKI certificate

* pki rm key <id> - remove PKI key

* pki tls <id> - configure TLS to use PKI key

* time - set AMT system time

* tls enable -r <-s|-p> [-m] [-c <common name>] - configure and enable remote TLS
  (with/without mutual authentication, with/without allowing plaintext)

* tls enable -l - configure and enable local TLS

* tls status - get current TLS settings

* tls disable -r - disable remote TLS

* tls disable -l - disable local TLS

* uuid - get AMT system UUID

* version - get AMT version


configuring TLS
~~~~~~~~~~~~~~~

The AMT supports 2048-bit keys for end-entity certificates and 4096-bit keys for
certificate authorities/intermediate certificates. It supports SHA512 hashes.

Various actions will not work without taking appropriate steps:

  * TLS cannot be enabled until it is configured
  * Certificates and keys in active use for TLS cannot be removed
    (this includes all trusted certificates when mutual authentication is enabled)

Client certificates must have extended key usage ``1.3.6.1.5.5.7.3.2``
(TLS Web Client Authentication) and ``2.16.840.1.113741.1.2.1`` (Intel AMT Remote Console).

Configuring the supported Common Names (``tls enable -c ... -c ... -c ...``) is optional.

Repeatedly updating the certificate (e.g. using Let's Encrypt) may wear out the
AMT flash. Use your own root CA.

Configuring a Certificate Recovation List is not supported by this application.

Be careful not to prevent yourself from accessing the AMT while configuring TLS,
i.e. allow plaintext while making changes until TLS has been tested.

1. Generate a key with ``amtctrl ... pki generate 2048``
2. Get it with ``amtctrl ... pki list keys`` and save to ``amt_rsa_public_key.pem``
3. Convert it to a generic public key with ``openssl rsa -RSAPublicKey_in -in amt_rsa_public_key.pem -pubout -out amt_public_key.pem``
4. Create a CSR with ``openssl genrsa | openssl x509 -x509toreq -new -subj /CN=example.com -signkey /dev/stdin -force_pubkey amt_public_key.pem -out amt_csr.pem``
   (requires OpenSSL 3.0.0+)
5. Use ``amtctrl ... pki request amt_csr.pem <id>`` to get the AMT to sign the CSR
6. Issue a certificate from your CA using the CSR
7. Import the certificate with ``amtctrl ... pki add cert amt_cert.pem``
8. Configure the new certificate to be used with TLS with ``amtctrl ... pki tls <id>``
9. Enable TLS (allowing plaintext) with ``amtctrl ... tls enable -r -l -p``
10. Test HTTPS access, using ``amthostdb`` to configure the root CA
11. Enable TLS (disallowing plaintext) with ``amtctrl ... tls enable -r -l -s``
12. Use ``amtctrl ... pki add cert -t root_ca.pem`` to import the root CA for client authentication
13. Enable TLS (allowing plaintext) with ``amtctrl ... tls enable -r -l -p -m``
14. Test HTTPS access, using ``amthostdb`` to configure the root CA, user key and user cert
15. Enable TLS (disallowing plaintext) with ``amtctrl ... tls enable -r -l -s -m``

Futures
-------

* More extensive in tree testing (there currently is very little of
  this)

* Retry http requests when they fail. AMT processors randomly drop
  some connections, built in limited retry should be done.

* Fault handling. The current code is *very* optimistic. Hence, the
  0.x nature.

* Remote console control. There are AMT commands to expose a VNC
  remote console on the box. Want to support those.
