# Lazor_Group_Project_Fall_2026_Yifei_Song_ and_Guoyang_Zhou
Lazor_Group_Project_Fall_2026_Yifei_Song&amp;Guoyang_Zhou

This project was jointly completed by Yifei Song and Guoyang Zhou.

This Python solver reads a `.bff` puzzle, places the supplied blocks, and saves a board where the lasers collectively hit every target. It supports multiple lasers and fixed or movable mirrors, absorbers, and splitters.

## Run the solver

Use Python 3.10 or later. The solver uses only the Python standard library.

```text
python lazor.py examples/mad_1.bff
python lazor.py examples/mixed_7x7.bff -o solved_7x7.bff
python lazor.py examples/mixed_9x9.bff -o solved_9x9.bff
```

On Windows, `py -3` also works if the Python launcher is installed. Run the commands from this project folder.

By default, the solver writes `<board>_solution.bff` beside the input. The output contains the completed grid, a list of newly placed blocks with one-based row and column numbers, and the original laser and target records. It can be read again by the solver. Exit codes are `0` for success, `1` for a valid puzzle with no solution, and `2` for an input or output error.

## Board files

The grid sits between `GRID START` and `GRID STOP`. Rows can be written with or without spaces. A `#` starts a comment.

| Record or symbol | Meaning |
| --- | --- |
| `o` | Open cell where a movable block may be placed |
| `x` | Empty cell that cannot hold a block |
| `A`, `B`, `C` in the grid | Fixed mirror, absorber, or splitter |
| `A 2` outside the grid | Two movable mirrors |
| `L 2 7 1 -1` | Laser starting at `(2, 7)` and moving right and up |
| `P 3 0` | Target at `(3, 0)` |

Coordinates are measured in half-cell steps from the upper-left corner. The x axis points right and the y axis points down. Laser sources are at cell-face midpoints. A mirror reverses the direction component normal to its face. A splitter sends both a reflected ray and a straight ray. An absorber ends the ray after it reaches the face.

## How the solver searches

- `board.py` reads and validates the board and defines the `Block` class.
- `optics.py` computes the next rays for each position and incoming direction once. The search reuses these transitions and tracks visited states so cycles terminate.
- `solver.py` traces the lasers and assigns each open cell only when a ray first tries to enter it. It tries each distinct available tile type once per decision. If a target cannot be reached even when every undecided cell may take any available tile independently, the solver abandons that branch. On harder boards it alternates between two placement orders, one that tries leaving a cell open first and one that tries a splitter first. Once all targets are reached, it places any remaining blocks in unused cells, which preserves the paths already found.
- `lazor.py` provides the command-line entry point and saves the solution.

## Tests and timing

```text
python -m unittest discover -s tests -v
```

The tests cover parsing errors, multiple lasers, fixed blocks, all three optical interactions, cycles, unsolvable boards, and output that can be read back. The search is also compared with exhaustive placement on 100 seeded small puzzles.

The command line prints the time spent building the beam graph and searching. The local timings below are medians of seven runs on Windows with Python 3.12.

| Board | Source | Solve time |
| --- | --- | --- |
| `mad_1.bff` | Fall 2026 handout | 0.0005 s |
| `mixed_7x7.bff` | Generated test board | 0.0029 s |
| `mixed_9x9.bff` | Generated test board | 0.0030 s |

The Mad 1 layout matches the handout's screenshot on page 1. Use the same commands with the instructor's boards to measure grading-set performance.



## Group release

The group should review the code together, have each member commit their actual contributions, and run the tests and instructor benchmarks before tagging the final commit. Create a GitHub Release for the tag and submit the repository link through Canvas and the course form. Each group member should complete the peer review in Canvas.

