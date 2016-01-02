import requests
import json
from BeautifulSoup import BeautifulSoup

class PhabricatorUserQuerier(object):
    def __init__(self):
        self.cache = {}
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'https://tools.wmflabs.org/contact by valhallasw'
        self.base = 'https://phabricator.wikimedia.org'
        
    def get_user_info(self, p):
        if p in self.cache:
            return self.cache[p]
        req = self.session.get(self.base + p + "/")
        soup = BeautifulSoup(req.text)
        data = soup.find(**{'class': 'phui-property-list-properties'})
        data = [e.text for e in data]
        data = dict(zip(data[::2], data[1::2]))
        self.cache[p] = data
        return data

    def get_phabricator_users(self, q):
        users = {}
        req = self.session.get(
            self.base + '/typeahead/class/PhabricatorPeopleDatasource/',
            params={'q': q, '__ajax__': True},
        )
        
        userlist = json.loads(req.text[len('for (;;);'):])['payload']
        
        for entry in userlist[:5]:
            formatted_name, p, PHID, username = entry[:4]
            data = self.get_user_info(p)
            data['formatted_name'] = formatted_name
            data['username'] = username
            data['url'] = self.base + p
            users[username] = data
            
        return users
        
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)

    pq = PhabricatorUserQuerier()
    print json.dumps(pq.get_phabricator_users('val'))
