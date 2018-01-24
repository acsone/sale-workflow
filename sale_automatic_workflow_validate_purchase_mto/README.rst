.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=============================================
Sale Automatic Workflow Validate Purchase Mto
=============================================

When a sale order generates directly a purchase order, validates it automatically

Installation
============


Configuration
=============

* Go to Sales > Configuration > Automatic Workflow > Automatic Workflow
* Select the workflow you want
* Check the box 'Validate Purchase Orders MTO' and configure (if you want) the
corresponding domains

Usage
=====

* Create a sale order with products that have a route that contains a buy rule for the location
you want to
* Validate the sale order
* The corresponding purchase order is automatically confirmed

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/167/10.0


Known issues / Roadmap
======================


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/sale-workflow}/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Denis Roussel <denis.roussel@acsone.eu>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
