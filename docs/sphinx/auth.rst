
.. _auth:

SDSS Authentication
===================

For collaboration members, when downloading proprietary collaboration data products, 
``sdss_access`` requires authentication using the ``.netrc`` file.  To set this up, create or 
edit a file in your home called ``.netrc`` and copy the following lines, depending on which
SDSS collaboration you are a member of.

SDSS-IV members
---------------
::

    machine data.sdss.org
       login <username>
       password <password>


SDSS-V members
--------------
::

    machine data.sdss5.org
       login <username>
       password <password>

In the above, replace ``<username>`` and ``<password>`` with your login credentials. The default 
SDSS username and password is also acceptable for anonymous access.  
**Finally, run** ``chmod 600 ~/.netrc`` **to make the file only accessible to your user.**

.. note::

  The default SDSS username and password is different for SDSS-IV and SDSS-V members. 