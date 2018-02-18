tools.contact
-------------

This is the backend code for https://tools.wmflabs.org/contact/. `app.py`
contains the main application; `ldapquery.py` and `phabuserquery.py` contain
code to talk to LDAP and Phabricator, respectively.

`service.manifest` and `uwsgi.ini` are Toolforge specific configuration files;
the first is symlinked from $HOME, the second from $HOME/www/python.

Dependencies are listed in requirements.txt; ldapsupportlib is a Cloud
VPS-specific python library which is available Cloud VPS-wide.
