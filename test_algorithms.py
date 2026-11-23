"""Run with: python test_algorithms.py (no testing framework needed)."""
import random
from algorithms import METHODS, search
from graph import cells, edges

random.seed(42)
checks = 0
for trial in range(120):
    n = random.randint(5,10)
    all_nodes = cells(n,n)
    start,goal = (0,0),(n-1,n-1)
    blocked = set(random.sample(all_nodes[1:-1],random.randint(0,n*n//3)))
    closed = random.sample(list(edges(n,n)),random.randint(0,n))
    hazards = {p:random.choice((4,8,12)) for p in random.sample(all_nodes,random.randint(0,n))}
    safety = random.random()
    results = {m:search((n,n),start,goal,blocked,closed,hazards,m,safety) for m in METHODS}
    a,d = results['A*'],results['Dijkstra']
    assert bool(a[0]) == bool(d[0]), (trial,'reachability')
    assert abs(a[2]-d[2]) < 1e-8, (trial,'optimality')
    closed_set = {frozenset(e) for e in closed}
    for method,(path,explored,cost,ms,g) in results.items():
        assert len(explored)==len(set(explored))
        assert not (set(explored)&blocked)
        if path:
            assert path[0]==start and path[-1]==goal
            assert not (set(path)&blocked)
            for u,v in zip(path,path[1:]):
                assert abs(u[0]-v[0])+abs(u[1]-v[1])==1
                assert frozenset((u,v)) not in closed_set
            actual = sum(1+safety*hazards.get(p,0) for p in path[1:])
            assert abs(actual-cost)<1e-8
        else:
            assert cost==0
        checks += 1
    if results['BFS'][0]:
        assert len(results['BFS'][0])<=len(results['DFS'][0]) if results['DFS'][0] else True
print(f'PASS: {checks} algorithm cases across 120 randomized scenarios')
