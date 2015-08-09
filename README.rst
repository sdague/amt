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

The ``amt`` library installs a binary ``amtctrl`` for working with AMT
enabled machines.

machine enrollment
~~~~~~~~~~~~~~~~~~

To simplify the control commands ``amtcrtl`` has a machine
registry. New machines are added via:

    amtctrl add <name> <address> <amtpassword>

You can see a list of all machines with:

   amtctrl list

And remove an existing machine with:

   amtctrl rm <name>


controlling machines
~~~~~~~~~~~~~~~~~~~~

Once machines are controlled you have a number of options exposed:

   amtctrl <name> <command>

Command is one of:

* on - power on the machine

* off - power off the machine

* reboot - power cycle the machine

* pxeboot - set the machine to pxeboot the next time it reboots, and
  reboot the machine. This is extremely useful if you have install
  automation on pxeboot.

* status - return power status as an ugly CIM blob (TODO: make this better)

Futures
-------

* More extensive in tree testing (there currently is very little of
  this)

* Retry http requests when they fail. AMT processors randomly drop
some connections, built in limited retry should be done.

* Fault handling. The current code is *very* optimistic. Hence, the
  0.x nature.

* Remove console control. There are AMT commands to expose a VNC
  remote console on the box. Want to support those.
