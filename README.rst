===============================
Python AMT Tools
===============================

.. image:: https://img.shields.io/travis/sdague/amt.svg
        :target: https://travis-ci.org/sdague/amt

.. image:: https://img.shields.io/pypi/v/amt.svg
        :target: https://pypi.python.org/pypi/amt


Tools for interacting with Intel's Active Management Technology

* Free software: Apache 2

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
OpenStack Baremetal (Ironic) service. It has native support for AMT hardware
control.

This project is derivative work from Ironic. The heavy lifting of
understanding all the CIM magic incantations, and oh the magic they
are, comes from that code. Refactored for a more minimal usage.

Features
--------

* TODO
