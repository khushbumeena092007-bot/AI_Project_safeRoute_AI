"""Small helpers for grid coordinates and road selection."""


def name(cell):
    return f'{chr(65 + cell[1])}{cell[0] + 1}'


def cells(rows, cols):
    return [(r, c) for r in range(rows) for c in range(cols)]


def edges(rows, cols):
    for r, c in cells(rows, cols):
        if c + 1 < cols:
            yield ((r, c), (r, c + 1))
        if r + 1 < rows:
            yield ((r, c), (r + 1, c))


def edge_name(edge):
    return f'{name(edge[0])} — {name(edge[1])}'
