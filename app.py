import os
import jinja2
import re
import ldapquery
from phabquery import PhabricatorQuerier
import json
from collections import defaultdict
from flask import Flask, render_template, request, Response, session, redirect, flash, url_for

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('tools.contact')

secrets = json.load(open('secrets.json'))

app = Flask(__name__)

app.secret_key = secrets['flask_app_key']

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/<identifier>")
def query(identifier):
    return render_template('index.html', value=identifier)

@app.route("/", methods=['POST'])
def submit():
    identifier = request.form['identifier']
    logger.debug('Identifier is %r' % identifier)
    if not re.match(r"^[ a-zA-Z0-9\-\.]+$", identifier):
       return 'Identifier must be [a-zA-Z0-9]', 500 

    q = ldapquery.LDAPQuerier()
    pq = PhabricatorQuerier()

    wildcard = len(identifier) >= 3
    parts = []

    q.connect()
    user_data = q.user_search(identifier, wildcard)
    group_data = q.group_search(identifier, wildcard)
    q.disconnect()

    for info in user_data.values():
        info['type'] = 'ldap'

    all_users_cn = {}
    all_users_uid = {}

    for dn,u in user_data.items():
        all_users_cn[dn] = u['cn'].lower()
        all_users_uid[dn] = u['uid'].lower()
    
    for group in group_data.values():
        for dn,u in group['member'].items():
            all_users_cn[dn] = u['cn'].lower()
            all_users_uid[dn] = u['uid'].lower()
        filteredname = re.sub(r"[^A-Za-z0-9 ]", " ", group['cn'])
        group['projects'] = pq.get_phabricator_projects(filteredname)
   
    phab_users = pq.get_phabricator_users(identifier)

    for info in phab_users.values():
        info['type'] = 'phab'

    users = {}
    users.update(user_data)
    users.update(phab_users)

    ldap_to_phab = {}
    for dn in all_users_cn.keys():
        retrieved_users = {}
        for name in set([all_users_cn[dn], all_users_uid[dn]]):
            phab_users = pq.get_phabricator_users(name)
            retrieved_users.update(pq.get_phabricator_users(name))
        for username, info in retrieved_users.items():
            if info['LDAP User'].lower() == all_users_cn[dn].lower():
                ldap_to_phab[dn] = {username: info}
                break
        else:
            ldap_to_phab[dn] = retrieved_users
            
    return render_template(
        'result.html',
        query=identifier,
        groups=group_data,
        users=users,
        ldap_to_phab=ldap_to_phab
    )

    
@app.template_filter('wikitech')
def wikitech_link(cn):
    return jinja2.Markup(
        "<a href='https://wikitech.wikimedia.org/wiki/User:%s'>%s</a>"
    ) % (jinja2.utils.unicode_urlencode(cn), cn)

@app.template_filter('querylink')
def query_link(cn):
    return jinja2.Markup(
        "<a href='%s'>%s</a>"
    ) % (url_for('query', identifier=cn), cn)

if __name__ == "__main__":
    app.run(debug=True, port=os.getuid())
