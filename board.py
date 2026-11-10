"""Read Lazor board files and describe the blocks on a board."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


Point = tuple[int, int]
Ray = tuple[int, int, int, int]
class Block(Enum):
    """The three block types"""
    REFLECT = "A"
    OPAQUE = "B"
    REFRACT = "C"
    def outgoing(self, straight: int, reflected: int) -> tuple[int, ...]:
        if self is Block.REFLECT:
            return (reflected,)
        if self is Block.OPAQUE:
            return ()
        return (straight, reflected)


class BoardFormatError(ValueError):
    pass
@dataclass(frozen=True)
class Puzzle:

    width: int
    height: int
    grid: tuple[str, ...]
    inventory: dict[str, int]
    lasers: tuple[Ray, ...]
    targets: tuple[Point, ...]


def _numbers(fields: list[str], count: int) -> tuple[int, ...]:
    """Read exactly the requested number of integer fields."""
    if len(fields) != count:
        raise ValueError(f"expected {count} integer field(s)")
    try:
        return tuple(int(field) for field in fields)
    except ValueError as error:
        raise ValueError("expected integer fields") from error


def read_bff(path: Path) -> Puzzle:
    """Load and validate one BFF file"""
    rows = []
    inventory = {}
    laser_records = []
    target_records = []
    block_codes = {block.value for block in Block}
    grid_codes = block_codes | {"o", "x"}
    in_grid = grid_closed = False

    for line_number, raw in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        fields = raw.partition("#")[0].split()
        if not fields:
            continue
        try:
            if fields == ["GRID", "START"]:
                if in_grid or grid_closed:
                    raise ValueError("expected a single GRID START marker")
                in_grid = True
            elif fields == ["GRID", "STOP"]:
                if not in_grid or not rows:
                    raise ValueError("GRID STOP must follow a nonempty grid")
                in_grid = False
                grid_closed = True
            elif in_grid:
                row = "".join(fields)
                if set(row) - grid_codes:
                    raise ValueError("grid cells must be o, x, A, B, or C")
                if rows and len(row) != len(rows[0]):
                    raise ValueError("grid rows must have equal lengths")
                rows.append(row)
            elif fields[0] in block_codes:
                (count,) = _numbers(fields[1:], 1)
                if count < 0 or fields[0] in inventory:
                    raise ValueError("expected one nonnegative count per block type")
                inventory[fields[0]] = count
            elif fields[0] == "L":
                x, y, dx, dy = _numbers(fields[1:], 4)
                if abs(dx) != 1 or abs(dy) != 1:
                    raise ValueError("direction components must be 1 / -1")
                if (x + y) % 2 == 0:
                    raise ValueError("laser must start at a face midpoint")
                laser_records.append((line_number, (x, y, dx, dy)))
            elif fields[0] == "P":
                x, y = _numbers(fields[1:], 2)
                target_records.append((line_number, (x, y)))
            else:
                raise ValueError(f"unknown record {fields[0]!r}")
        except ValueError as error:
            raise BoardFormatError(f"{path}:{line_number}: {error}") from error
    if not grid_closed:
        raise BoardFormatError(f"{path}: expected GRID START and GRID STOP")
    if not laser_records or not target_records:
        raise BoardFormatError(f"{path}: expected both L and P records")

    width, height = len(rows[0]), len(rows)
    for line_number, record in laser_records + target_records:
        x, y = record[:2]
        if not (0 <= x <= 2 * width and 0 <= y <= 2 * height):
            raise BoardFormatError(f"{path}:{line_number}: "f"coordinate ({x}, {y}) lies outside the board")

    grid = tuple("".join(rows))
    if sum(inventory.values()) > grid.count("o"):
        raise BoardFormatError(f"{path}: more movable blocks than available cells")
    lasers = tuple(ray for _, ray in laser_records)
    targets = tuple(dict.fromkeys(point for _, point in target_records))
    return Puzzle(width, height, grid, inventory, lasers, targets)


def format_solution(puzzle: Puzzle, grid: tuple[str, ...]) -> str:
    """Write a solved layout as a reusable BFF file."""
    lines = ["# Lazor solution",
        "# A = mirror, B = absorber, C = splitter",
        "# o = open cell, x = cell that cannot hold a block",
        "# Movable blocks placed (row and column start at 1)",]
    for index, (original, solved) in enumerate(zip(puzzle.grid, grid)):
        if original != solved:
            row, column = divmod(index, puzzle.width)
            lines.append(f"#   {solved} at row {row + 1}, column {column + 1}")
    lines.append("GRID START")
    for start in range(0, len(grid), puzzle.width):
        lines.append(" ".join(grid[start : start + puzzle.width]))
    lines.append("GRID STOP")
    lines.extend(f"L {x} {y} {dx} {dy}" for x, y, dx, dy in puzzle.lasers)
    lines.extend(f"P {x} {y}" for x, y in puzzle.targets)
    return "\n".join(lines) + "\n"
