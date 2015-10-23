from itertools import combinations
from collections import defaultdict, Counter

import igraph as ig
import pandas as pd


PERIODS = {1: (2004, 2007),
           2: (2008, 2010),
           3: (2011, 2014)}

def year_to_period(year):
    for period, years in PERIODS.items():
        if int(year) in range(years[0], years[1]+1):
            return period


valid_rfas = pd.read_pickle('valid_rfas.pickle')
valid_rfas['period'] = valid_rfas['year'].map(year_to_period)

graphs = defaultdict(lambda: ig.Graph(directed=False))
lookups = dict()
edges = defaultdict(list)

for period, rfas in valid_rfas.groupby('period'):
    vertices = set.union(*[s for s in rfas['participants']])
    lookups[period] = {i:n for n, i in enumerate(vertices)}
    graphs[period].add_vertices(len(vertices))
    graphs[period].vs['label'] = list(vertices)

for i, d in valid_rfas.groupby(['period', 'url']):
    period = i[0]
    lu = lookups[period]
    ps = set(*d['participants'])
    ps.discard(*d['candidate'])
    for link in combinations(ps, 2):
        edges[period].append(link)
        #mk_weighted_edge(graphs[period], lu[link[0]], lu[link[1]])

for period, y in PERIODS.items():
    edges_by_ids = list(map(lambda t: tuple(lookups[period][i] for i in t), edges[period]))
    graphs[period].add_edges(Counter(edges_by_ids).keys())
    graphs[period].es['weight'] = list(Counter(edges_by_ids).values())
    graphs[period].write_graphml('rfas_ties_{0}-{1}.graphml'.format(y[0], y[1]))
