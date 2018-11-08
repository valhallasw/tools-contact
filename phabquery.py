import requests
import json
from bs4 import BeautifulSoup

import sys
if sys.version_info[0] == 2:
    from repoze.lru import lru_cache
else:
    from functools import lru_cache

cachesize = 1024

class PhabricatorQuerier(object):
    def __init__(self):
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'https://tools.wmflabs.org/contact by valhallasw'
        self.base = 'https://phabricator.wikimedia.org'
       
    @lru_cache(cachesize) 
    def get_user_info(self, p):
        req = self.session.get(self.base + p)
        soup = BeautifulSoup(req.text, 'lxml')
        data = soup.find(**{'class': 'phui-property-list-properties'})
        data = [e.text.strip() for e in data]
        data = dict(zip(data[::2], data[1::2]))
        return data

    @lru_cache(cachesize)
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
            data['MediaWiki User'] = data['MediaWiki User'].replace(" [ Global Accounts ]", "")
            users[username] = data
            
        return users
 
    @lru_cache(cachesize)
    def get_phabricator_projects(self, q):
        projects = {"Tools":
            {"url": "https://phabricator.wikimedia.org/project/view/703/",
             "name": "Tools",
             "tags": ["Tools", "tools", "tool-labs-tools-other"]
            }
        }
        req = self.session.get(
            self.base + '/typeahead/class/PhabricatorProjectDatasource/',
            params={'q': q, '__ajax__': True},
        )
        
        projectlist = json.loads(req.text[len('for (;;);'):])['payload']
        print(projectlist)
        for entry in projectlist:
            tags, p, PHID, _, name = entry[:5]
            data = {}
            data['name'] = name
            data['url'] = self.base + p
            data['tags'] = tags.split(' ')
            projects[name] = data
            
        return projects
        
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)

    pq = PhabricatorQuerier()
    print(json.dumps(pq.get_phabricator_users('val')))

    print(json.dumps(pq.get_phabricator_projects('tools')))
