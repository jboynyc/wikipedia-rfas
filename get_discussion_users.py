import re
import requests
import pandas as pd
from time import sleep
from urllib.parse import unquote
from bs4 import BeautifulSoup as bs
from sqlalchemy import create_engine

db = create_engine('sqlite:///wikipedia_rfas.db')


def get_users_from_page(location):
    BASEURL = 'http://en.m.wikipedia.org{}'
    USER_URL = re.compile(r'/wiki/User:(.*)')
    users = set()
    try:
        r = requests.get(BASEURL.format(location))
    except:
        return None
    s = bs(r.text)
    links = s.findAll('a', {'href': USER_URL})
    for link in links:
        try:
            user = USER_URL.match(link['href']).group(1)
            if '/' not in user and '#' not in user and '?' not in user:
                users.add(unquote(user))
        except AttributeError:
            print('failed:', link)
            pass
    return users


successful_rfas = pd.read_sql('successful_rfas', db)
successful_rfas['result'] = 'success'
all_rfas = successful_rfas.append(pd.read_sql('unsuccessful_rfas', db))
all_rfas['date'] = all_rfas['date'].map(pd.to_datetime)

users = []
for _, r in all_rfas.iloc[len(users):].iterrows():
    u = get_users_from_page(r['url'])
    users.append(u)
    sleep(1)

all_rfas['participants'] = users

# some rfa discussions are missing
valid_rfas = all_rfas[all_rfas['participants'].notnull()]

valid_rfas['num_participants'] = valid_rfas['participants'].map(len)

# some rfa discussions have been "courtesy blanked"
valid_rfas = valid_rfas[valid_rfas['num_participants'] > 0]

# a few doubles due to sloppiness in archiving prior to 2008
valid_rfas.sort('year').drop_duplicates('url', take_last=True, inplace=True)

# how many rfas are we left with?
valid_rfas['success'] = valid_rfas['result'].map(lambda x: x == 'success')
valid_rfas.pivot_table(columns=['success'], aggfunc=len, index=['year'], values='url', margins=True)

# persist dataframe for further analysis (pickle because there's no
# straightforward sqlite data type for sets)
valid_rfas.to_pickle('valid_rfas.pickle')
