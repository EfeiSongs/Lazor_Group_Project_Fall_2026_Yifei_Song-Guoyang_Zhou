"""Solve one Lazor BFF board from the command line."""

import argparse
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

from board import BoardFormatError, format_solution, read_bff
from solver import solve


def main() -> int:
    """Read a board, solve it, and write the solution"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board",type=Path,nargs="?",default=Path(__file__).resolve().with_name("123.bff"),help="input BFF puzzle",)
    parser.add_argument("-o","--output",type=Path,help="solution path (default is <board>_solution.bff)",)
    args = parser.parse_args()
    source = args.board
    output = args.output or source.with_name(f"{source.stem}_solution.bff")

    try:
        if source.resolve() == output.resolve() or (source.exists() and output.exists() and source.samefile(output)):
            parser.error("the output path must differ from the input board")
        puzzle = read_bff(source)
        started = perf_counter()
        solution = solve(puzzle)
        elapsed = perf_counter() - started
        if solution is None:
            print(f"No solution found for {source} ({elapsed:.3f} s).")
            return 1
        with TemporaryDirectory(dir=output.parent) as directory:
            staged = Path(directory) / "solution.bff"
            content = format_solution(puzzle, solution)
            staged.write_text(content, encoding="utf-8")
            staged.replace(output)
    except (BoardFormatError, OSError, UnicodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    print(f"Solved {source} in {elapsed:.3f} s. Solution written to {output}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
