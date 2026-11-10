"""Precompute the straight and reflected steps for each laser state."""

from dataclasses import dataclass
from itertools import product

from board import Block, Puzzle, Ray


@dataclass(frozen=True)
class Step:
    """The cell a beam is about to enter and the possible next rays."""

    cell: int | None
    outgoing: dict[str, tuple[int, ...]]
    target: int


@dataclass(frozen=True)
class BeamGraph:
    """Optical transitions indexed by position and incoming direction."""

    steps: tuple[Step, ...]
    starts: tuple[int, ...]
    all_targets: int

    def reached(self, grid: tuple[str, ...]) -> int:
        """Return a bit mask of targets reached on a complete board."""
        pending = list(self.starts)
        seen = set()
        reached = 0
        while pending:
            ray = pending.pop()
            if ray in seen:
                continue
            seen.add(ray)
            step = self.steps[ray]
            reached |= step.target
            tile = "x" if step.cell is None else grid[step.cell]
            pending.extend(step.outgoing[tile])
        return reached


def _entry(
    ray: Ray, width: int, height: int
) -> tuple[int | None, Ray, Ray]:
    """Find the entered cell and the two possible successor states."""
    x, y, dx, dy = ray
    straight = (x + dx, y + dy, dx, dy)
    if x % 2 == 0:
        # x is even at a vertical face. Reflect the horizontal component.
        row, column = y // 2, (x + dx) // 2
        reflected = (x - dx, y + dy, -dx, dy)
    else:
        row, column = (y + dy) // 2, x // 2
        reflected = (x + dx, y - dy, dx, -dy)
    cell = row * width + column
    if not (0 <= row < height and 0 <= column < width):
        cell = None
    return cell, straight, reflected


def build_graph(puzzle: Puzzle) -> BeamGraph:
    """Build the finite state graph for all cell-edge midpoints."""
    directions = tuple(product((-1, 1), repeat=2))
    rays = [(x, y, dx, dy)
        for y in range(2 * puzzle.height + 1)
        for x in range(2 * puzzle.width + 1)
        if (x + y) % 2
        for dx, dy in directions]
    indices = {ray: index for index, ray in enumerate(rays)}
    target_bits = {point: 1 << index for index, point in enumerate(puzzle.targets)}
    steps = []
    for ray in rays:
        cell, straight, reflected = _entry(ray, puzzle.width, puzzle.height)
        forward_id = indices.get(straight, -1)
        reflected_id = indices.get(reflected, -1)
        passing = (forward_id,) if forward_id >= 0 else ()
        outgoing = {"x": passing, "o": passing}
        for block in Block:
            outgoing[block.value] = tuple(
                next_ray
                for next_ray in block.outgoing(forward_id, reflected_id)
                if next_ray >= 0)

        steps.append(Step(cell, outgoing, target_bits.get(ray[:2], 0)))

    starts = tuple(indices[ray] for ray in puzzle.lasers)
    return BeamGraph(tuple(steps), starts, (1 << len(target_bits)) - 1)
