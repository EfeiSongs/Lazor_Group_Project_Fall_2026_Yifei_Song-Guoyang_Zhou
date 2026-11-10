"""Find legal placements by following the beams through a partial board."""

from collections.abc import Generator, Iterator
from dataclasses import dataclass

from board import Puzzle
from optics import BeamGraph, build_graph


CHOICE_ORDERS = (("o", "A", "C", "B"), ("C", "A", "o", "B"))
SEARCH_SLICE = 1024
UNASSIGNED = "?"


@dataclass
class Decision:
    """A placement decision and the trace state before that placement."""

    cell: int
    choices: Iterator[str]
    pending: tuple[int, ...]
    seen: int
    missing: int


def _possibly_reaches_all(
    graph: BeamGraph,
    grid: list[str],
    remaining: dict[str, int],
    frontier: list[int],
    seen: int,
    missing: int,
) -> bool:
    """Rule out targets unreachable even with relaxed block placement."""
    pending = list(frontier)
    can_reflect = remaining["A"] or remaining["C"]
    can_pass = remaining["o"] or remaining["C"]
    if can_reflect:
        relaxed_tile = "C" if can_pass else "A"
    else:
        relaxed_tile = "o" if can_pass else "B"
    while pending and missing:
        ray = pending.pop()
        ray_bit = 1 << ray
        if seen & ray_bit:
            continue

        seen |= ray_bit
        step = graph.steps[ray]
        missing &= ~step.target
        tile = "x" if step.cell is None else grid[step.cell]
        if tile == UNASSIGNED:

            tile = relaxed_tile
        pending.extend(step.outgoing[tile])
    return missing == 0



def solve(puzzle: Puzzle) -> tuple[str, ...] | None:
    """Return one solution using the full inventory, or None, if impossible."""
    graph = build_graph(puzzle)


    searches = [_search(puzzle, graph, order) for order in CHOICE_ORDERS]


    try:
        while True:
            for search in searches:
                next(search)
    except StopIteration as result:
        return result.value

def _search(
    puzzle: Puzzle, graph: BeamGraph, order: tuple[str, ...]
) -> Generator[None, None, tuple[str, ...] | None]:


    """Pause periodically and return the result when this search finishes."""
    grid = [UNASSIGNED if tile == "o" else tile for tile in puzzle.grid]
    remaining = {tile: puzzle.inventory.get(tile, 0) for tile in order}
    remaining["o"] = grid.count(UNASSIGNED) - sum(remaining.values())


    pending = list(graph.starts)
    seen = 0
    missing = graph.all_targets
    decisions: list[Decision] = []
    attempts = 0


    while True:

        while pending and missing:
            ray = pending.pop()
            ray_bit = 1 << ray
            if seen & ray_bit:
                continue
            step = graph.steps[ray]
            missing &= ~step.target
            if not missing:
                break
            tile = "x" if step.cell is None else grid[step.cell]
            if tile == UNASSIGNED:
                pending.append(ray)
                if not _possibly_reaches_all(
                    graph, grid, remaining, pending, seen, missing):
                    break
                choices = [code for code in order if remaining[code]]
                decisions.append(Decision(step.cell, iter(choices), tuple(pending), seen, missing))
                break
            seen |= ray_bit
            pending.extend(step.outgoing[tile])

        if not missing:


            leftovers = iter(tile for tile in order for _ in range(remaining[tile]))
            return tuple(next(leftovers) if tile == UNASSIGNED else tile
                for tile in grid)

        while decisions:
            decision = decisions[-1]
            previous = grid[decision.cell]
            if previous != UNASSIGNED:
                remaining[previous] += 1
            choice = next(decision.choices, None)
            if choice is not None:
                grid[decision.cell] = choice
                remaining[choice] -= 1
                pending = list(decision.pending)
                seen, missing = decision.seen, decision.missing
                attempts += 1
                if attempts == SEARCH_SLICE:
                    attempts = 0
                    yield
                break
            grid[decision.cell] = UNASSIGNED
            decisions.pop()
        else:
            return None
