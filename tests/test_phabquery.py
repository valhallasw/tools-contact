import json

import phabquery

def test_get_users():
    pq = phabquery.PhabricatorQuerier()

    result = pq.get_phabricator_users('valha')

    assert 'valhallasw' in result

    details = result['valhallasw']

    assert '/p/valhallasw' in details["url"]
    assert details['username'] == 'valhallasw'
    assert details['LDAP User'] == 'Merlijn van Deen'
    assert details['MediaWiki User'] == 'Valhallasw'
    assert 'Oct 3 2014, 1:14 PM' in details['User Since']
