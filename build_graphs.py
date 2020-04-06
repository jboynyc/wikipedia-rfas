import igraph as ig
import pandas as pd
from itertools import combinations
from collections import defaultdict, Counter


valid_rfas = pd.read_pickle('valid_rfas.pickle')

graphs = defaultdict(lambda: ig.Graph(directed=False))
lookups = dict()
edges = defaultdict(list)

for year, rfas in valid_rfas.groupby('year'):
    vertices = set.union(*[s for s in rfas['participants']])
    lookups[year] = {i:n for n, i in enumerate(vertices)}
    graphs[year].add_vertices(len(vertices))
    graphs[year].vs['label'] = list(vertices)

for i, d in valid_rfas.groupby(['year', 'url']):
    year = i[0]
    lu = lookups[year]
    ps = set(*d['participants'])
    ps.discard(*d['candidate'])
    for link in combinations(ps, 2):
        edges[year].append(link)

for y in range(2004, 2015):
    year = str(y)
    edges_by_ids = list(map(lambda t: tuple(lookups[year][i] for i in t), edges[year]))
    graphs[year].add_edges(Counter(edges_by_ids).keys())
    #graphs[year].es['weight'] = list(Counter(edges_by_ids).values())
    graphs[year].write_graphml('rfas_ties_{}.graphml'.format(year))
