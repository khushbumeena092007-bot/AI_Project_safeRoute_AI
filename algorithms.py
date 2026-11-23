"""Five original graph searches; no library pathfinding calls."""
from collections import deque
from heapq import heappush, heappop
from itertools import count
from time import perf_counter

METHODS = ('A*', 'Dijkstra', 'Greedy', 'BFS', 'DFS')

def search(grid, start, goal, blocked=(), roads=(), hazards=None, method='A*', safety=1.0):
    """Return path, exploration order, actual weighted cost, milliseconds, g-scores.

    cost of entering v = 1 + safety * max(0, hazard[v]); Manhattan h admissible.
    BFS/DFS optimize discovery order, not weighted costs.
    """
    rows, cols = grid
    if method not in METHODS or not 0 <= safety <= 1:
        raise ValueError('Invalid algorithm or safety weight')
    hazards = hazards or {}
    blocked, closed = set(blocked), {frozenset(e) for e in roads}
    if start in blocked or goal in blocked:
        return [], [], 0, 0.0, {}
    def neighbors(u):
        r, c = u
        for v in ((r-1,c), (r,c+1), (r+1,c), (r,c-1)):
            if 0 <= v[0] < rows and 0 <= v[1] < cols and v not in blocked and frozenset((u,v)) not in closed:
                yield v
    def weight(v):
        return 1 + safety * max(0, hazards.get(v, 0))
    def h(v):
        return abs(v[0]-goal[0]) + abs(v[1]-goal[1])
    t = perf_counter()
    parent, best, explored, visited = {start:None}, {start:0.0}, [], set()
    seq = count()
    if method == 'BFS':
        queue = deque([(start,0.0)])
    elif method == 'DFS':
        queue = [(start,0.0)]
    else:
        queue = []
        heappush(queue, (h(start) if method in ('A*','Greedy') else 0, next(seq), start, 0.0))
    while queue:
        if method == 'BFS':
            u,g = queue.popleft()
        elif method == 'DFS':
            u,g = queue.pop()
        else:
            _,_,u,g = heappop(queue)
        if u in visited or (method in ('A*','Dijkstra') and g > best[u] + 1e-9):
            continue
        visited.add(u)
        explored.append(u)
        if u == goal:
            break
        for v in neighbors(u):
            ng = g + weight(v)
            if method in ('BFS','DFS','Greedy'):
                if v in parent:
                    continue
                parent[v],best[v] = u,ng
                if method == 'Greedy':
                    heappush(queue, (h(v),next(seq),v,ng))
                else:
                    queue.append((v,ng))
            elif ng < best.get(v,float('inf')) - 1e-9:
                parent[v],best[v] = u,ng
                heappush(queue, (ng + (h(v) if method == 'A*' else 0),next(seq),v,ng))
    ms = (perf_counter()-t)*1000
    if goal not in visited:
        return [], explored, 0.0, ms, best
    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path,explored,sum(weight(v) for v in path[1:]),ms,best
