import ldapsupportlib
import ldap

class ObjectNotFoundException(Exception):
    """LDAP object not found"""

def base(ou):
    return 'ou=%s,dc=wikimedia,dc=org' % ou


class LDAPQuerier(object):
    def __init__(self):
        self.ldapConn = None

    def connect(self):
        self.ldapConn = ldapsupportlib.LDAPSupportLib().connect()

    def disconnect(self):
        self.ldapConn.unbind()
        self.ldapConn = None

    def search_s(self, *args, **kwargs):
        return self.decode(self.ldapConn.search_s(*args, **kwargs))

    def decode(self, element):
        if isinstance(element, str):
            return element
        if isinstance(element, bytes):
            return element.decode('utf-8')
        if isinstance(element, (list, tuple)):
            return [self.decode(x) for x in element]
        if isinstance(element, dict):
            return {self.decode(k): self.decode(v) for k,v in element.items()}
        raise Exception('no clue how to decode type %r: %r' % (type(element), element))

    def fixup_user_info(self, info):
        out = {}
        for attr,value in info.items():
            assert(len(value) == 1)
            out[attr] = value[0]
        return out

    def user_by_cn(self, cn):
        info = dict(self.search_s(
            base=cn,
            scope=ldap.SCOPE_BASE,
            attrlist=['cn', 'sn', 'uid', 'uidNumber']
        )[0][1])
        return self.fixup_user_info(info)

    def user_search(self, q, wildcard=False):
        wq = "*%s*" % q if wildcard else q
     
        result = self.search_s(
            base=base('people'),
            scope=ldap.SCOPE_ONELEVEL,
            filterstr='(|(uidNumber=%(q)s)(cn=%(wq)s)(sn=%(wq)s)(uid=%(wq)s))' % {'q': q, 'wq': wq},
            attrlist=['cn', 'sn', 'uid', 'uidNumber']
        )
        result = dict(result)

        for cn,info in result.items():
            result[cn] = info = self.fixup_user_info(info)
            info['groups'] = self.groups_for_member(cn)
        return result

    def groups_for_member(self, member_cn):
        filterstr = '(member=%s)' % member_cn
        return self.group_query(filterstr, attrlist=['cn', 'gidNumber'])

    def group_query(self, filterstr, attrlist=['cn', 'member', 'gidNumber']):
        servicegroups = self.search_s(
            base=base('servicegroups'),
            scope=ldap.SCOPE_ONELEVEL,
            filterstr=filterstr,
            attrlist=attrlist
        )
        groups = self.search_s(
            base=base('groups'),
            scope=ldap.SCOPE_ONELEVEL,
            filterstr=filterstr,
            attrlist=attrlist
        )
        all_groups = dict(servicegroups + groups)
 
        for cn,info in all_groups.items():
            info['cn'] = info['cn'][0]
            info['gidNumber'] = info.get('gidNumber', ['unknown'])[0] # missing for some ldap-only groups

        return all_groups

    def group_search(self, q, wildcard=False):
        wq = "*%s*" % q if wildcard else q
        filterstr = '(|(gidNumber=%(q)s)(cn=%(wq)s))' % {'q': q, 'wq': wq}
        result = self.group_query(filterstr)

        for cn,info in result.items():
            member_details = {}
            for member in info.get('member', []):
                member_details[member] = self.user_by_cn(member)
            info['member'] = member_details
        return result

if __name__ == '__main__':
    q = LDAPQuerier()
    q.connect()
    #q.ldapConn._trace_level = 1
    import json
    print(json.dumps(q.user_search('merlijn', True),indent=2))
    print(json.dumps(q.user_search('1092'),indent=2))
    print(json.dumps(q.group_search('ikibu', True),indent=2))
    print(json.dumps(q.group_search('52773'), indent=2))
