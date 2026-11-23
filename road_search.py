"""Five hand-written searches over an OSMnx MultiDiGraph."""
from collections import deque
from heapq import heappush, heappop
from itertools import count
from math import radians, sin, cos, asin, sqrt
from time import perf_counter

METHODS = ('A*', 'Dijkstra', 'Greedy', 'BFS', 'DFS')

def meters(a, b):
    lat1, lon1, lat2, lon2 = map(radians, (a[0], a[1], b[0], b[1]))
    x = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return 12742000 * asin(min(1, sqrt(x)))

def search(G, start, goal, method='A*', closed=(), hazards=None, safety=1.0):
    """Returns (route, visited order, weighted meters, runtime ms, g scores).
    Edges may be directed; weight = length * (1 + safety * hazard).
    Haversine lower bound is admissible for weighted road length.
    """
    if method not in METHODS or not 0 <= safety <= 1:
        raise ValueError('Invalid algorithm or safety')
    closed, hazards = set(closed), hazards or {}
    def neighbors(u):
        for v, multi in G[u].items():
            if (u, v) in closed:
                continue
            lengths = [float(d.get('length', 1)) for d in multi.values()]
            if lengths:
                yield v, min(lengths) * (1 + safety * max(0, hazards.get((u, v), 0)))
    def h(u):
        a, b = G.nodes[u], G.nodes[goal]
        return meters((a['y'],a['x']), (b['y'],b['x']))
    t = perf_counter()
    parent, best, seen, order = {start: None}, {start: 0.}, set(), []
    seq = count()
    if method == 'BFS':
        frontier = deque([(start,0.)])
    elif method == 'DFS':
        frontier = [(start,0.)]
    else:
        frontier = []
        heappush(frontier, (h(start) if method in ('A*','Greedy') else 0., next(seq), start, 0.))
    while frontier:
        if method == 'BFS':
            u, g = frontier.popleft()
        elif method == 'DFS':
            u, g = frontier.pop()
        else:
            _, _, u, g = heappop(frontier)
        if u in seen or (method in ('A*','Dijkstra') and g > best[u] + 1e-8):
            continue
        seen.add(u)
        order.append(u)
        if u == goal:
            break
        for v, w in neighbors(u):
            ng = g+w
            if method in ('BFS','DFS','Greedy'):
                if v in parent:
                    continue
                parent[v], best[v] = u, ng
                if method == 'Greedy':
                    heappush(frontier, (h(v), next(seq), v, ng))
                else:
                    frontier.append((v,ng))
            elif ng < best.get(v,float('inf')) - 1e-8:
                parent[v], best[v] = u, ng
                heappush(frontier, (ng+(h(v) if method=='A*' else 0.),next(seq),v,ng))
    ms = (perf_counter()-t)*1000
    if goal not in seen:
        return [], order, 0., ms, best
    route = []
    u = goal
    while u is not None:
        route.append(u)
        u = parent[u]
    route.reverse()
    return route, order, best[goal], ms, best
