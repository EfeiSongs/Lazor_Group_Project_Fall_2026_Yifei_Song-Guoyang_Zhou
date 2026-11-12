"""Generate a random, solvable Lazor puzzle in BFF format."""

import argparse
from collections import Counter
from pathlib import Path
from random import Random

from board import Puzzle, Ray
from optics import build_graph


SIZE = 5
TARGET_COUNT = 4
MOVABLE = ("A", "A", "A", "C")


def _random_laser(rng: Random) -> Ray:
    """Start a laser at a random outside face, pointing into the board."""
    edge = 2 * SIZE
    offset = rng.randrange(1, edge, 2)
    direction = rng.choice((-1, 1))
    return rng.choice(
        (
            (0, offset, 1, direction),
            (edge, offset, -1, direction),
            (offset, 0, direction, 1),
            (offset, edge, direction, -1),
        )
    )


def generate_puzzle(rng: Random) -> Puzzle:
    """Hide movable blocks and select targets reached by the solved layout."""
    edge = 2 * SIZE
    points = tuple(
        (x, y)
        for y in range(edge + 1)
        for x in range(edge + 1)
        if (x + y) % 2
    )
    inventory = dict(Counter(MOVABLE))

    for _ in range(200):
        # Give each blocked, fixed, and hidden tile a distinct cell.
        cells = rng.sample(range(SIZE * SIZE), 6 + len(MOVABLE))
        unavailable, absorber, hidden = cells[:5], cells[5], cells[6:]
        grid = ["o"] * (SIZE * SIZE)
        for cell in unavailable:
            grid[cell] = "x"
        grid[absorber] = "B"
        unsolved = tuple(grid)

        for cell, block in zip(hidden, MOVABLE):
            grid[cell] = block
        solved = tuple(grid)
        lasers = (_random_laser(rng),)
        graph = build_graph(
            Puzzle(SIZE, SIZE, unsolved, inventory, lasers, points)
        )
        newly_reached = graph.reached(solved) & ~graph.reached(unsolved)
        targets = [
            point for index, point in enumerate(points)
            if newly_reached & (1 << index)
        ]
        if len(targets) >= TARGET_COUNT:
            return Puzzle(
                SIZE, SIZE, unsolved, inventory, lasers,
                tuple(rng.sample(targets, TARGET_COUNT)),
            )

    raise RuntimeError("Could not generate a puzzle. Please try again.")


def _format_bff(puzzle: Puzzle) -> str:
    """Serialize the puzzle without revealing the hidden placement."""
    lines = ["# Random Lazor puzzle", "GRID START"]
    for start in range(0, len(puzzle.grid), puzzle.width):
        lines.append(" ".join(puzzle.grid[start : start + puzzle.width]))
    lines.append("GRID STOP")
    for block, count in puzzle.inventory.items():
        lines.append(f"{block} {count}")
    lines.extend(f"L {x} {y} {dx} {dy}" for x, y, dx, dy in puzzle.lasers)
    lines.extend(f"P {x} {y}" for x, y in puzzle.targets)
    return "\n".join(lines) + "\n"


def main() -> int:
    """Prompt for a file name if no command-line argument is given."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "filename", nargs="?", help="output file name or path"
    )
    args = parser.parse_args()
    filename = args.filename
    if filename is None:
        try:
            filename = input("Output file name [random_maze.bff]: ").strip()
        except EOFError:
            parser.error("provide an output file name as an argument")
        filename = filename or "random_maze.bff"

    output = Path(filename)
    if not output.name:
        parser.error("the output path must include a file name")
    if output.suffix.lower() != ".bff":
        output = output.with_name(output.name + ".bff")
    output = Path(__file__).resolve().parent / output

    try:
        content = _format_bff(generate_puzzle(Random()))
        with output.open("x", encoding="utf-8") as file:
            file.write(content)
    except FileExistsError:
        parser.exit(1, f"File already exists. Choose another name: {output}\n")
    except (OSError, RuntimeError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Generated {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
