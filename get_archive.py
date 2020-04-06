import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
from sqlalchemy import create_engine

db = create_engine('sqlite:///wikipedia_rfas.db')
YEARS = {'2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014'}


def get_archive_table(baseurl, year):
    r = requests.get(baseurl.format(year))
    s = bs(r.text)
    return s.find('table', {'class': 'wikitable'})


def get_archive_list(baseurl, year):
    r = requests.get(baseurl.format(year))
    s = bs(r.text)
    return s.find('div', {'class': 'content'}).findAll('li')


def cells_to_dict(cells):
    d = {}
    d['url'] = cells[0].find('a')['href']
    d['candidate'] = cells[0].text
    d['date'] = cells[1].text
    if len(cells) == 4:
        d['closed_by'] = cells[2].text
        d['tally'] = cells[3].find('span').text
    elif len(cells) == 5:
        d['result'] = cells[2].text
        d['closed_by'] = cells[3].text
        d['tally'] = cells[4].find('span').text
    return d


def li_to_dict(item):
    d = {}
    try:
        txt = item.text.split(', (')[0]
    except:
        txt = item.text
    d['url'] = item.next['href']
    d['candidate'] = txt.split(',')[0]
    d['date'] = txt.split(',')[-1].split(' - ')[0].strip()
    d['result'] = txt.split(',')[-1].split(' - ')[1].strip()
    return d


## STORE SUCCESSFUL RFAS
url_success = 'http://en.m.wikipedia.org/wiki/Wikipedia:Successful_requests_for_adminship/{}'

success_archive = []
for year in YEARS:
    table = get_archive_table(url_success, year)
    for row in table.findAll('tr'):
        cells = row.findAll('td')
        if len(cells) == 4:
            try:
                data = cells_to_dict(cells)
                data['year'] = year
                success_archive.append(data)
            except:
                print('FAILED:', str(cells)[1:81])
        else:
            print('skipped:', str(cells)[1:81])

pd.DataFrame(success_archive).to_sql('successful_rfas', db)

## STORE UNSUCCESSFUL RFAS
url_unsuccess = 'http://en.m.wikipedia.org/wiki/Wikipedia:Unsuccessful_adminship_candidacies_%28Chronological%29/{}'

unsuccess_archive = []
for year in YEARS:
    if int(year) > 2007:
        table = get_archive_table(url_unsuccess, year)
        for row in table.findAll('tr'):
            cells = row.findAll('td')
            if len(cells) == 5:
                try:
                    data = cells_to_dict(cells)
                    data['year'] = year
                    unsuccess_archive.append(data)
                except:
                    print('FAILED:', str(cells)[1:81])
            else:
                print('skipped:', str(cells)[1:81])
    elif int(year) <= 2007:
        items = get_archive_list(url_unsuccess, year)
        for i in items:
            if 'Requests_for' in str(i):
                try:
                    data = li_to_dict(i)
                    data['closed_by'] = None
                    data['tally'] = None
                    data['year'] = year
                    unsuccess_archive.append(data)
                except:
                    print('FAILED:', str(i)[0:80])
            else:
                print('skipped:', str(i)[0:80])

pd.DataFrame(unsuccess_archive).to_sql('unsuccessful_rfas', db)
