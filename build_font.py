#!/usr/bin/env python3
"""
OpenCode Complete Font Builder (26 Unicase Letters a-z) — Edition 2.100
Incorporates proportional modular widths (+1 module width 5x7 for 'w' and 'm',
symmetric 3x7 for 'i' and 'l', and standard 4x7 for the remaining 22 letters)
while strictly preserving:
- 1 module = 6 SVG units = 120 font units
- Uniform 120u (1-module) inter-letter gap (60u LSB + 60u RSB on every glyph)
- 1:1 stroke contrast (120u / 120u, sigma = 0; no 2x2 solid ink blocks)
- 0 curves, 0 diagonals (strictly H and V segments)
- Lower-counter shade (`shadow`) rule in rows 3..5
"""

import json
import os
import struct
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = "/home/ivascu/.gemini/antigravity/scratch/opencode-font"
os.makedirs(OUT_DIR, exist_ok=True)

ORIGINAL_GLYPHS_MJS = {
    "o": {"shadow": "M18 30H6V18H18V30Z", "ink": "M18 12H6V30H18V12ZM24 36H0V6H24V36Z"},
    "p": {"shadow": "M18 30H6V18H18V30Z", "ink": "M6 30H18V12H6V30ZM24 36H6V42H0V6H24V36Z"},
    "e": {"shadow": "M24 24V30H6V24H24Z", "ink": "M24 24H6V30H24V36H0V6H24V24ZM6 18H18V12H6V18Z"},
    "n": {"shadow": "M18 36H6V18H18V36Z", "ink": "M18 12H6V36H0V6H18V12ZM24 36H18V12H24V36Z"},
    "c": {"shadow": "M24 30H6V18H24V30Z", "ink": "M24 12H6V30H24V36H0V6H24V12Z"},
    "d": {"shadow": "M18 30H6V18H18V30Z", "ink": "M18 12H6V30H18V12ZM24 36H0V6H18V0H24V36Z"},
}

GRID_SPECS = {
    "a": {
        "origin": "Derived (180° inversion of e)",
        "family": "Double-storey x-height (e-family)",
        "rule": "Inverted e: top arch at row 1, upper-left aperture at row 2, midline crossbar at row 3, closed lower bowl in rows 3..5 with 2 shade modules at row 4.",
        "rows": [
            "....",
            "####",
            "...#",
            "####",
            "#SS#",
            "####",
            "....",
        ],
        "variants": {
            "Default (Inverted e)": ["....", "####", "...#", "####", "#SS#", "####", "...."],
            "Notched Top-Left (.###)": ["....", ".###", "...#", "####", "#SS#", "####", "...."],
        },
    },
    "b": {
        "origin": "Derived (horizontal mirror of d / vertical mirror of p)",
        "family": "Bowl + stem quartet (o/p/d/b/q)",
        "rule": "Canonical o-bowl in rows 1..5 plus 1-module ascender at (col 0, row 0). Shade fills lower counter (cols 1..2, rows 3..4).",
        "rows": [
            "#...",
            "####",
            "#..#",
            "#SS#",
            "#SS#",
            "####",
            "....",
        ],
    },
    "c": {
        "origin": "OpenCode wordmark (No. 005)",
        "family": "Open aperture (c-family)",
        "rule": "o-bowl with right wall (col 3, rows 2..4) opened. Shade expands across cols 1..3 in rows 3..4 (6 modules).",
        "rows": [
            "....",
            "####",
            "#...",
            "#SSS",
            "#SSS",
            "####",
            "....",
        ],
    },
    "d": {
        "origin": "OpenCode wordmark (No. 006)",
        "family": "Bowl + stem quartet (o/p/d/b/q)",
        "rule": "Canonical o-bowl in rows 1..5 plus 1-module ascender at (col 3, row 0). Shade fills lower counter (cols 1..2, rows 3..4).",
        "rows": [
            "...#",
            "####",
            "#..#",
            "#SS#",
            "#SS#",
            "####",
            "....",
        ],
    },
    "e": {
        "origin": "OpenCode wordmark (No. 003)",
        "family": "Double-storey x-height (e-family)",
        "rule": "Closed upper eye (cols 1..2, row 2), midline crossbar at row 3, open lower aperture (cols 1..3, row 4) filled with 3 shade modules.",
        "rows": [
            "....",
            "####",
            "#..#",
            "####",
            "#SSS",
            "####",
            "....",
        ],
    },
    "f": {
        "origin": "Derived (ascender arch + high crossbar)",
        "family": "Ascender crossbar pair (f/t)",
        "rule": "Stem at col 1, top arch overhanging right at row 0 (cols 1..3), crossbar at row 2 (cols 0..2), 4 shade modules under crossbar in cols 2..3, rows 3..4.",
        "rows": [
            ".###",
            ".#..",
            "###.",
            ".#SS",
            ".#SS",
            ".#..",
            "....",
        ],
        "variants": {
            "High Crossbar (Row 2)": [".###", ".#..", "###.", ".#SS", ".#SS", ".#..", "...."],
            "Midline Crossbar (Row 3)": [".###", ".#..", ".#..", "####", ".#SS", ".#SS", "...."],
        },
    },
    "g": {
        "origin": "Derived (raised bowl + hooked descender loop)",
        "family": "Descender loop (g/y)",
        "rule": "Closed upper bowl in rows 1..4 (shaded at row 3, cols 1..2), right stem descending through row 5 into full 1-module descender hook at row 6.",
        "rows": [
            "....",
            "####",
            "#..#",
            "#SS#",
            "####",
            "...#",
            "####",
        ],
    },
    "h": {
        "origin": "Derived (n + left ascender at col 0, row 0)",
        "family": "Corner-stepped arch (n-family)",
        "rule": "Exact n glyph in rows 1..5 plus 1-module ascender at (col 0, row 0), following the o -> d/b ascender extension rule.",
        "rows": [
            "#...",
            "###.",
            "#..#",
            "#SS#",
            "#SS#",
            "#SS#",
            "....",
        ],
    },
    "i": {
        "origin": "Derived (3×7 symmetric serifed stem + ascender tittle)",
        "family": "Narrow symmetric stem (i/l, 3×7)",
        "rule": "3-module width (3×7): tittle at (col 1, row 0), 1-module gap at row 1, top-left flag at (col 0, row 2), stem down col 1 (rows 2..5), symmetric 3-module base at row 5, 2 shade modules at col 2, rows 3..4.",
        "rows": [
            ".#.",
            "...",
            "##.",
            ".#S",
            ".#S",
            "###",
            "...",
        ],
        "variants": {
            "3×7 Symmetric Serif": [".#.", "...", "##.", ".#S", ".#S", "###", "..."],
            "4×7 Wide Foot": [".#..", "....", "##..", ".#SS", ".#SS", "####", "...."],
        },
    },
    "j": {
        "origin": "Derived (right-stemmed i with descender hook)",
        "family": "Descender hook (j)",
        "rule": "Tittle at (col 3, row 0), 1-module gap at row 1, top flag at (col 2, row 2), right stem down col 3 (rows 2..6), descender hook across row 6 with upturned tip at (col 0, row 5), 6 shade modules in cols 1..2, rows 3..5.",
        "rows": [
            "...#",
            "....",
            "..##",
            ".SS#",
            ".SS#",
            "#SS#",
            "####",
        ],
    },
    "k": {
        "origin": "Derived (ascender stem + n-style corner-stepped arm and leg)",
        "family": "Corner-stepped vertex (k/v/x/z)",
        "rule": "Left stem in col 0 (rows 0..5), midline junction bar at row 3 (cols 0..2), upper arm (col 3, rows 1..2) and lower leg (col 3, rows 4..5) connected via corner-touch at x=18 (like n). 4 shade modules in cols 1..2, rows 4..5.",
        "rows": [
            "#...",
            "#..#",
            "#..#",
            "###.",
            "#SS#",
            "#SS#",
            "....",
        ],
        "variants": {
            "Box-Stepped (n-Style)": ["#...", "#..#", "#..#", "###.", "#SS#", "#SS#", "...."],
            "Diagonal Staircase": ["#...", "#..#", "#.#.", "##..", "#S#.", "#SS#", "...."],
        },
    },
    "l": {
        "origin": "Derived (3×7 continuous ascender stem with top flag & symmetric foot)",
        "family": "Narrow symmetric stem (i/l, 3×7)",
        "rule": "3-module width (3×7): top-left flag at row 0 (cols 0..1), stem down col 1 (rows 0..5), symmetric 3-module baseline foot at row 5, 2 shade modules at col 2, rows 3..4.",
        "rows": [
            "##.",
            ".#.",
            ".#.",
            ".#S",
            ".#S",
            "###",
            "...",
        ],
        "variants": {
            "3×7 Symmetric Serif": ["##.", ".#.", ".#.", ".#S", ".#S", "###", "..."],
            "4×7 Wide Foot": ["##..", ".#..", ".#..", ".#SS", ".#SS", "####", "...."],
        },
    },
    "m": {
        "origin": "Derived (5×7 +1 module wide double-n arch)",
        "family": "Wide 3-stem pair (m/w, 5×7)",
        "rule": "5-module width (+1 module rule for 3-stem legibility): three 1-module stems at cols 0, 2, 4 separated by two 1-module counters at cols 1 and 3, topped by n-style notched arch (row 1: ####.). 6 shade modules in cols 1 & 3, rows 3..5.",
        "rows": [
            ".....",
            "####.",
            "#.#.#",
            "#S#S#",
            "#S#S#",
            "#S#S#",
            ".....",
        ],
        "variants": {
            "5×7 Double-N Arch (####.)": [".....", "####.", "#.#.#", "#S#S#", "#S#S#", "#S#S#", "....."],
            "5×7 Stepped Twin-Arch (##.#.)": [".....", "##.#.", "#.#.#", "#S#S#", "#S#S#", "#S#S#", "....."],
            "5×7 Symmetric Twin-Arch (.#.#.)": [".....", ".#.#.", "#.#.#", "#S#S#", "#S#S#", "#S#S#", "....."],
            "4×7 Strict Grid": ["....", "#.#.", "##.#", "#SS#", "#SS#", "#SS#", "...."],
        },
    },
    "n": {
        "origin": "OpenCode wordmark (No. 004)",
        "family": "Corner-stepped arch (n-family)",
        "rule": "Left stem in col 0 (rows 1..5) with top bar cols 0..2 (notched at col 3, row 1), corner-touching right stem in col 3 (rows 2..5) at vertex (18, 12). 6 shade modules in cols 1..2, rows 3..5.",
        "rows": [
            "....",
            "###.",
            "#..#",
            "#SS#",
            "#SS#",
            "#SS#",
            "....",
        ],
    },
    "o": {
        "origin": "OpenCode wordmark (No. 001)",
        "family": "Bowl + stem quartet (o/p/d/b/q)",
        "rule": "Canonical 4x5 x-height ring (rows 1..5, cols 0..3) enclosing a 2x3 counter (cols 1..2, rows 2..4) with 4 shade modules in the lower counter (cols 1..2, rows 3..4).",
        "rows": [
            "....",
            "####",
            "#..#",
            "#SS#",
            "#SS#",
            "####",
            "....",
        ],
    },
    "p": {
        "origin": "OpenCode wordmark (No. 002)",
        "family": "Bowl + stem quartet (o/p/d/b/q)",
        "rule": "Canonical o-bowl in rows 1..5 plus 1-module descender at (col 0, row 6). Shade fills lower counter (cols 1..2, rows 3..4).",
        "rows": [
            "....",
            "####",
            "#..#",
            "#SS#",
            "#SS#",
            "####",
            "#...",
        ],
    },
    "q": {
        "origin": "Derived (horizontal mirror of p / vertical mirror of d)",
        "family": "Bowl + stem quartet (o/p/d/b/q)",
        "rule": "Canonical o-bowl in rows 1..5 plus 1-module descender at (col 3, row 6). Shade fills lower counter (cols 1..2, rows 3..4).",
        "rows": [
            "....",
            "####",
            "#..#",
            "#SS#",
            "#SS#",
            "####",
            "...#",
        ],
    },
    "r": {
        "origin": "Derived (n-arch with open lower right side)",
        "family": "Corner-stepped arch (n-family)",
        "rule": "Identical top arch and corner-stepped right terminal to n in rows 1..2 (col 3, row 2 ear), with lower right stem removed in rows 3..5. 6 shade modules in cols 1..2, rows 3..5.",
        "rows": [
            "....",
            "###.",
            "#..#",
            "#SS.",
            "#SS.",
            "#SS.",
            "....",
        ],
    },
    "s": {
        "origin": "Derived (3-bar serpentine x-height contour)",
        "family": "Double-storey x-height (e-family)",
        "rule": "Top bar (row 1), upper-left connector (col 0, row 2), midline bar (row 3), lower-right connector (col 3, row 4), bottom bar (row 5). 3 shade modules in lower counter (cols 0..2, row 4), mirroring e.",
        "rows": [
            "....",
            "####",
            "#...",
            "####",
            "SSS#",
            "####",
            "....",
        ],
    },
    "t": {
        "origin": "Derived (ascender stem + symmetric x-height crossbar + baseline hook)",
        "family": "Ascender crossbar pair (f/t)",
        "rule": "Ascender tip at (col 1, row 0), symmetric 3-module crossbar at x-height row 1 (cols 0..2), stem down col 1 to baseline hook at row 5 (cols 1..3). 4 shade modules in cols 2..3, rows 3..4.",
        "rows": [
            ".#..",
            "###.",
            ".#..",
            ".#SS",
            ".#SS",
            ".###",
            "....",
        ],
        "variants": {
            "Trim Crossbar (###.)": [".#..", "###.", ".#..", ".#SS", ".#SS", ".###", "...."],
            "Full 4-Col Crossbar (####)": [".#..", "####", ".#..", ".#SS", ".#SS", ".###", "...."],
        },
    },
    "u": {
        "origin": "Derived (180° rotation of n)",
        "family": "Corner-stepped arch (n-family)",
        "rule": "Exact 180° inversion of n: left stem in col 0 (rows 1..4) notched at bottom-left (col 0, row 5), corner-touching bottom bar (cols 1..3, row 5) and full right stem in col 3 (rows 1..5). 4 shade modules in cols 1..2, rows 3..4.",
        "rows": [
            "....",
            "#..#",
            "#..#",
            "#SS#",
            "#SS#",
            ".###",
            "....",
        ],
    },
    "v": {
        "origin": "Derived (symmetric corner-stepped convergence at baseline)",
        "family": "Corner-stepped vertex (k/v/x/z)",
        "rule": "Symmetric outer walls in cols 0 and 3 (rows 1..4) stepping via corner-touches at (6, 30) and (18, 30) into centered 2-module vertex (cols 1..2, row 5). 4 shade modules in cols 1..2, rows 3..4.",
        "rows": [
            "....",
            "#..#",
            "#..#",
            "#SS#",
            "#SS#",
            ".##.",
            "....",
        ],
    },
    "w": {
        "origin": "Derived (5×7 +1 module wide twin-vertex double-v)",
        "family": "Wide 3-stem pair (m/w, 5×7)",
        "rule": "5-module width (+1 module rule for unmistakable w legibility): outer walls at cols 0 and 4 (rows 1..4), recessed central spire at col 2 (rows 2..4), converging via corner-touches into twin baseline vertices at cols 1 and 3 (row 5: .#.#.). 4 shade modules in cols 1 & 3, rows 3..4.",
        "rows": [
            ".....",
            "#...#",
            "#.#.#",
            "#S#S#",
            "#S#S#",
            ".#.#.",
            ".....",
        ],
        "variants": {
            "5×7 Twin-Vertex (Recessed Peak)": [".....", "#...#", "#.#.#", "#S#S#", "#S#S#", ".#.#.", "....."],
            "5×7 Twin-Vertex (Full Peak)": [".....", "#.#.#", "#.#.#", "#S#S#", "#S#S#", ".#.#.", "....."],
            "5×7 Notched Base (.###.)": [".....", "#...#", "#.#.#", "#S#S#", "#S#S#", ".###.", "....."],
            "5×7 Double-U (.####)": [".....", "#.#.#", "#.#.#", "#S#S#", "#S#S#", ".####", "....."],
            "4×7 Strict Grid": ["....", "#..#", "#..#", "#SS#", "#S##", ".#.#", "...."],
        },
    },
    "x": {
        "origin": "Derived (4-way symmetric corner-stepped crossover)",
        "family": "Corner-stepped vertex (k/v/x/z)",
        "rule": "Upper legs (cols 0, 3 in rows 1..2) and lower legs (cols 0, 3 in rows 4..5) meeting via 4 corner-touches at central 2-module midline bridge (cols 1..2, row 3). 4 shade modules in cols 1..2, rows 4..5.",
        "rows": [
            "....",
            "#..#",
            "#..#",
            ".##.",
            "#SS#",
            "#SS#",
            "....",
        ],
    },
    "y": {
        "origin": "Derived (u-cup in rows 1..4 + g-descender hook in rows 5..6)",
        "family": "Descender loop (g/y)",
        "rule": "Open-top u-cup in rows 1..4 (notched at col 0, row 4 via corner-touch at (6, 24), shaded at row 3, cols 1..2), right stem descending through row 5 into full descender hook at row 6.",
        "rows": [
            "....",
            "#..#",
            "#..#",
            "#SS#",
            ".###",
            "...#",
            "####",
        ],
    },
    "z": {
        "origin": "Derived (corner-stepped diagonal bridge across 3-row interior)",
        "family": "Corner-stepped vertex (k/v/x/z)",
        "rule": "Top bar at row 1, upper-right drop at (col 3, row 2), corner-stepped center bridge at row 3 (cols 1..2), lower-left drop at (col 0, row 4), bottom bar at row 5. 3 shade modules in cols 1..3, row 4.",
        "rows": [
            "....",
            "####",
            "...#",
            ".##.",
            "#SSS",
            "####",
            "....",
        ],
    },
}


def cells_to_contours(cells, unit=6):
    cell_set = set(cells)
    if not cell_set:
        return []

    edge_owner = {}
    for (c, r) in cell_set:
        x0, y0 = c * unit, r * unit
        x1, y1 = (c + 1) * unit, (r + 1) * unit
        candidates = [
            ((x0, y0), (x1, y0)),
            ((x1, y0), (x1, y1)),
            ((x1, y1), (x0, y1)),
            ((x0, y1), (x0, y0)),
        ]
        for p1, p2 in candidates:
            if (p2, p1) in edge_owner:
                del edge_owner[(p2, p1)]
            else:
                edge_owner[(p1, p2)] = (c, r)

    out_edges = defaultdict(list)
    for (p1, p2), owner in edge_owner.items():
        out_edges[p1].append((p2, owner))

    unused = set(edge_owner.keys())
    raw_loops = []

    while unused:
        start_edge = sorted(unused)[0]
        unused.remove(start_edge)
        p1, p2 = start_edge
        owner = edge_owner[start_edge]
        loop = [p1]
        curr_p1, curr_p2, curr_owner = p1, p2, owner

        while curr_p2 != loop[0]:
            loop.append(curr_p2)
            candidates = [
                (nxt_p2, nxt_owner)
                for (nxt_p2, nxt_owner) in out_edges[curr_p2]
                if (curr_p2, nxt_p2) in unused
            ]
            if len(candidates) == 1:
                nxt_p2, nxt_owner = candidates[0]
            else:
                same_cell = [c for c in candidates if c[1] == curr_owner]
                if same_cell:
                    nxt_p2, nxt_owner = same_cell[0]
                else:
                    nxt_p2, nxt_owner = candidates[0]
            unused.remove((curr_p2, nxt_p2))
            curr_p1, curr_p2, curr_owner = curr_p2, nxt_p2, nxt_owner

        simplified = []
        n = len(loop)
        for i in range(n):
            prev_pt = loop[(i - 1) % n]
            curr_pt = loop[i]
            next_pt = loop[(i + 1) % n]
            if (prev_pt[0] == curr_pt[0] == next_pt[0]) or (prev_pt[1] == curr_pt[1] == next_pt[1]):
                continue
            simplified.append(curr_pt)
        raw_loops.append(simplified)

    return raw_loops


def contours_to_svg_path(contours):
    parts = []
    for loop in contours:
        cmds = [f"M{loop[0][0]} {loop[0][1]}"]
        for i in range(1, len(loop)):
            prev_x, prev_y = loop[i - 1]
            curr_x, curr_y = loop[i]
            if curr_y == prev_y:
                cmds.append(f"H{curr_x}")
            elif curr_x == prev_x:
                cmds.append(f"V{curr_y}")
            else:
                raise ValueError(f"Non-orthogonal segment: ({prev_x},{prev_y}) -> ({curr_x},{curr_y})")
        cmds.append("Z")
        parts.append("".join(cmds))
    return "".join(parts)


def verify_and_build_glyph_data():
    glyphs_data = {}
    for letter in sorted(GRID_SPECS.keys()):
        spec = GRID_SPECS[letter]
        rows = spec["rows"]
        assert len(rows) == 7, f"{letter}: must have 7 rows"
        grid_cols = len(rows[0])
        assert grid_cols in (3, 4, 5), f"{letter}: width must be 3, 4, or 5 columns"
        for r_idx, row_str in enumerate(rows):
            assert len(row_str) == grid_cols, f"{letter} row {r_idx}: must have {grid_cols} cols"

        ink_cells = []
        shade_cells = []
        for r in range(7):
            for c in range(grid_cols):
                ch = rows[r][c]
                if ch == "#":
                    ink_cells.append((c, r))
                elif ch == "S":
                    shade_cells.append((c, r))

        # Check 1:1 stroke contrast rule: NO 2x2 solid ink blocks allowed!
        ink_set = set(ink_cells)
        for r in range(6):
            for c in range(grid_cols - 1):
                if (c, r) in ink_set and (c + 1, r) in ink_set and (c, r + 1) in ink_set and (c + 1, r + 1) in ink_set:
                    raise AssertionError(f"Glyph '{letter}' violates 1:1 stroke contrast (2x2 ink block at col {c}, row {r})!")

        total_xheight_cells = grid_cols * 5
        ink_xheight = sum(1 for (c, r) in ink_cells if 1 <= r <= 5)
        counter_xheight = total_xheight_cells - ink_xheight

        for (c, r) in shade_cells:
            assert 3 <= r <= 5, f"Glyph '{letter}' has shade outside rows 3..5 at ({c},{r})"
            assert (c, r) not in ink_set, f"Glyph '{letter}' has shade overlapping ink at ({c},{r})"

        ink_contours = cells_to_contours(ink_cells, unit=6)
        shade_contours = cells_to_contours(shade_cells, unit=6)

        if letter in ORIGINAL_GLYPHS_MJS:
            ink_svg = ORIGINAL_GLYPHS_MJS[letter]["ink"]
            shade_svg = ORIGINAL_GLYPHS_MJS[letter]["shadow"]
        else:
            ink_svg = contours_to_svg_path(ink_contours)
            shade_svg = contours_to_svg_path(shade_contours)

        font_contours = []
        for loop in ink_contours:
            f_loop = [(60 + 20 * x, 20 * (36 - y)) for (x, y) in loop]
            font_contours.append(f_loop)

        lr_mirrored = {(grid_cols - 1 - c, r) for (c, r) in ink_set}
        ink_rows = [r for (_, r) in ink_set]
        r_min, r_max = min(ink_rows), max(ink_rows)
        tb_mirrored = {(c, r_min + r_max - r) for (c, r) in ink_set}
        lr_sym = round(100.0 * len(ink_set & lr_mirrored) / len(ink_set))
        tb_sym = round(100.0 * len(ink_set & tb_mirrored) / len(ink_set))

        total_cells = grid_cols * 7
        advance_width = grid_cols * 120 + 120  # 60u LSB + 120u*cols + 60u RSB

        glyphs_data[letter] = {
            "letter": letter,
            "codepoint": f"U+{ord(letter):04X} / U+{ord(letter.upper()):04X}",
            "origin": spec["origin"],
            "family": spec["family"],
            "rule": spec["rule"],
            "grid_cols": grid_cols,
            "grid_rows": 7,
            "advance_width": advance_width,
            "rows": rows,
            "variants": spec.get("variants", {f"Canonical ({grid_cols}×7)": rows}),
            "ink_count": len(ink_cells),
            "shade_count": len(shade_cells),
            "counter_xheight": counter_xheight,
            "ink_xheight": ink_xheight,
            "total_xheight": total_xheight_cells,
            "coverage_pct": round(100.0 * len(ink_cells) / float(total_cells), 1),
            "contours_count": len(ink_contours),
            "points_count": sum(len(c) for c in ink_contours),
            "lr_symmetry_pct": lr_sym,
            "tb_symmetry_pct": tb_sym,
            "svg_ink": ink_svg,
            "svg_shadow": shade_svg,
            "svg_contours": ink_contours,
            "font_contours": font_contours,
        }

    return glyphs_data


def build_truetype_font(glyphs_data, out_ttf_path):
    letters = sorted(glyphs_data.keys())
    glyph_order = [".notdef", "space"] + letters

    def serialize_glyf_entry(contours_font):
        if not contours_font:
            return b"", (0, 0, 0, 0)
        all_pts = []
        end_pts = []
        for loop in contours_font:
            rev_loop = [loop[0]] + list(reversed(loop[1:]))
            all_pts.extend(rev_loop)
            end_pts.append(len(all_pts) - 1)

        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        xmin, ymin, xmax, ymax = min(xs), min(ys), max(xs), max(ys)

        header = struct.pack(">hhhhh", len(contours_font), xmin, ymin, xmax, ymax)
        end_pts_bytes = struct.pack(f">{len(end_pts)}H", *end_pts)
        ins_len_bytes = struct.pack(">H", 0)
        flags = bytes([0x01] * len(all_pts))

        x_deltas, y_deltas = [], []
        px, py = 0, 0
        for (x, y) in all_pts:
            x_deltas.append(x - px)
            y_deltas.append(y - py)
            px, py = x, y

        x_bytes = struct.pack(f">{len(x_deltas)}h", *x_deltas)
        y_bytes = struct.pack(f">{len(y_deltas)}h", *y_deltas)

        raw = header + end_pts_bytes + ins_len_bytes + flags + x_bytes + y_bytes
        if len(raw) % 2 == 1:
            raw += b"\x00"
        return raw, (xmin, ymin, xmax, ymax)

    glyf_chunks, bboxes, advance_widths, lsbs = [], [], [], []

    for gname in glyph_order:
        if gname == ".notdef":
            chunk, bbox = serialize_glyf_entry(glyphs_data["o"]["font_contours"])
            glyf_chunks.append(chunk)
            bboxes.append(bbox)
            advance_widths.append(600)
            lsbs.append(bbox[0])
        elif gname == "space":
            glyf_chunks.append(b"")
            bboxes.append((0, 0, 0, 0))
            advance_widths.append(480)
            lsbs.append(0)
        else:
            d = glyphs_data[gname]
            chunk, bbox = serialize_glyf_entry(d["font_contours"])
            glyf_chunks.append(chunk)
            bboxes.append(bbox)
            advance_widths.append(d["advance_width"])
            lsbs.append(bbox[0])

    loca_offsets = [0]
    for chunk in glyf_chunks:
        loca_offsets.append(loca_offsets[-1] + len(chunk))
    glyf_table = b"".join(glyf_chunks)
    loca_table = struct.pack(f">{len(loca_offsets)}I", *loca_offsets)

    non_empty_bboxes = [b for b in bboxes if b != (0, 0, 0, 0)]
    g_xmin = min(b[0] for b in non_empty_bboxes)
    g_ymin = min(b[1] for b in non_empty_bboxes)
    g_xmax = max(b[2] for b in non_empty_bboxes)
    g_ymax = max(b[3] for b in non_empty_bboxes)

    head_table = struct.pack(
        ">IIIIHHIIIIhhhhHHhhh",
        0x00010000,
        0x00020100,
        0,
        0x5F0F3CF5,
        0x000B,
        1000,
        0, 0,
        0, 0,
        g_xmin, g_ymin, g_xmax, g_ymax,
        0,
        7,
        2,
        1,
        0,
    )

    hhea_table = struct.pack(
        ">IhhhHhhhhhhhhhhhH",
        0x00010000,
        800,
        -200,
        0,
        max(advance_widths),
        60,
        60,
        g_xmax,
        1,
        0,
        0,
        0, 0, 0, 0,
        0,
        len(glyph_order),
    )

    max_contours = max(len(glyphs_data[l]["font_contours"]) for l in letters)
    max_points = max(glyphs_data[l]["points_count"] for l in letters)
    maxp_table = struct.pack(
        ">IHhhhhhhhhhhhhh",
        0x00010000,
        len(glyph_order),
        max_points,
        max_contours,
        0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0
    )

    hmtx_table = b"".join(struct.pack(">Hh", aw, lsb) for aw, lsb in zip(advance_widths, lsbs))

    end_codes = [0x0020, 0x005A, 0x007A, 0xFFFF]
    start_codes = [0x0020, 0x0041, 0x0061, 0xFFFF]
    id_deltas = [1 - 0x0020, 2 - 0x0041, 2 - 0x0061, 1]
    id_range_offsets = [0, 0, 0, 0]
    fmt4_body = (
        struct.pack(">4H", *end_codes)
        + struct.pack(">H", 0)
        + struct.pack(">4H", *start_codes)
        + struct.pack(">4h", *id_deltas)
        + struct.pack(">4H", *id_range_offsets)
    )
    fmt4_len = 14 + len(fmt4_body)
    fmt4_subtable = struct.pack(">7H", 4, fmt4_len, 0, 8, 8, 2, 0) + fmt4_body

    cmap_table = (
        struct.pack(">HH", 0, 2)
        + struct.pack(">HHI", 0, 3, 20)
        + struct.pack(">HHI", 3, 1, 20)
        + fmt4_subtable
    )

    os2_table = struct.pack(
        ">HhHHHHhhhhhhhhhh10sIIII4sHHHhhhHHIIhhHHH",
        2,
        600,
        400,
        5,
        0,
        600, 600, 0, -120,
        600, 600, 0, 480,
        120, 300,
        0,
        b"\x02\x00\x05\x03\x00\x00\x00\x00\x00\x00",
        0x00000001, 0, 0, 0,
        b"OPCD",
        0x0040,
        0x0020,
        0x007A,
        800,
        -200,
        0,
        800,
        200,
        0x00000001, 0,
        600,
        720,
        0,
        0x0020,
        1,
    )

    name_strings = [
        (1, "OpenCode Complete"),
        (2, "Regular"),
        (3, "OpenCode-Complete-2.100"),
        (4, "OpenCode Complete"),
        (5, "Version 2.100 (26-Glyph Unicase Complete Edition, 5x7 W/M)"),
        (6, "OpenCodeComplete-Regular"),
    ]
    records = []
    str_pool = b""
    for name_id, text in name_strings:
        b_mac = text.encode("ascii")
        records.append((1, 0, 0, name_id, len(b_mac), len(str_pool)))
        str_pool += b_mac
        b_win = text.encode("utf-16-be")
        records.append((3, 1, 0x0409, name_id, len(b_win), len(str_pool)))
        str_pool += b_win

    records.sort(key=lambda r: (r[0], r[1], r[2], r[3]))
    name_header = struct.pack(">HHH", 0, len(records), 6 + 12 * len(records))
    rec_bytes = b"".join(struct.pack(">6H", *r) for r in records)
    name_table = name_header + rec_bytes + str_pool

    post_table = struct.pack(
        ">IIhhIIIII",
        0x00030000,
        0,
        -120,
        60,
        0,
        0, 0, 0, 0
    )

    tables = {
        b"OS/2": os2_table,
        b"cmap": cmap_table,
        b"glyf": glyf_table,
        b"head": head_table,
        b"hhea": hhea_table,
        b"hmtx": hmtx_table,
        b"loca": loca_table,
        b"maxp": maxp_table,
        b"name": name_table,
        b"post": post_table,
    }

    def calc_checksum(data):
        padded = data + b"\x00" * ((4 - len(data) % 4) % 4)
        total = 0
        for (val,) in struct.iter_unpack(">I", padded):
            total = (total + val) & 0xFFFFFFFF
        return total

    num_tables = len(tables)
    sfnt_header = struct.pack(">IHHHH", 0x00010000, num_tables, 128, 3, num_tables * 16 - 128)

    sorted_tags = sorted(tables.keys())
    offset = 12 + 16 * num_tables
    dir_entries, body_chunks = [], []

    for tag in sorted_tags:
        raw = tables[tag]
        csum = calc_checksum(raw)
        length = len(raw)
        padded = raw + b"\x00" * ((4 - length % 4) % 4)
        dir_entries.append(struct.pack(">4sIII", tag, csum, offset, length))
        body_chunks.append(padded)
        offset += len(padded)

    full_font = sfnt_header + b"".join(dir_entries) + b"".join(body_chunks)
    with open(out_ttf_path, "wb") as f:
        f.write(full_font)
    return len(full_font)


def write_mjs_files(glyphs_data):
    letters = sorted(glyphs_data.keys())
    lines = [
        "// Complete 26-letter Unicase Alphabet for OpenCode (Edition 2.100).",
        "// Standard letters use 4x7 modules (24x42 SVG units, 600u advance); wide 3-stem letters (m, w) use 5x7 modules (+1 module width, 30x42 SVG units, 720u advance); narrow serifed stems (i, l) use 3x7 modules (18x42 SVG units, 480u advance).",
        "export const GLYPHS = {",
    ]
    for l in letters:
        d = glyphs_data[l]
        lines.append(
            f"  {l}: {{ cols: {d['grid_cols']}, advanceWidth: {d['advance_width']}, shadow: '{d['svg_shadow']}', ink: '{d['svg_ink']}' }},"
        )
    lines.append("};")
    lines.append("")

    with open(os.path.join(OUT_DIR, "glyphs.mjs"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    font_mjs_content = """import { GLYPHS } from './glyphs.mjs';

export const FONT_FAMILY = 'OpenCode Complete';
export const FONT_FILENAME = 'OpenCode-Complete.otf';
const LETTERS = Object.keys(GLYPHS);
const INVISIBLE = [0, 9, 10, 13, 0x200b, 0x200c, 0x200d, 0x2060, 0xfe0e, 0xfe0f, 0xfeff];

export function createCompleteLogoFont(opentype) {
  const path = data => opentype.Path.fromSVG(data, {
    flipY: true, flipYBase: 36, scale: 20, x: 60, y: 0,
  });
  const glyphs = [
    new opentype.Glyph({ name: '.notdef', advanceWidth: 600, path: path(GLYPHS.o.ink) }),
    new opentype.Glyph({ name: '.null', unicodes: [...INVISIBLE], advanceWidth: 0, path: new opentype.Path() }),
    new opentype.Glyph({ name: 'space', unicodes: [0x20, 0xa0], advanceWidth: 480, path: new opentype.Path() }),
  ];

  for (const letter of LETTERS) {
    const lowerCode = letter.codePointAt(0);
    const upperCode = letter.toUpperCase().codePointAt(0);
    const spec = GLYPHS[letter];
    glyphs.push(new opentype.Glyph({
      name: letter,
      unicode: lowerCode,
      unicodes: [lowerCode, upperCode],
      advanceWidth: spec.advanceWidth || 600,
      path: path(spec.ink),
    }));
  }

  return new opentype.Font({
    familyName: FONT_FAMILY,
    styleName: 'Regular',
    postScriptName: 'OpenCodeComplete-Regular',
    unitsPerEm: 1000,
    ascender: 800,
    descender: -200,
    weightClass: 400,
    version: 'Version 2.100',
    description: 'Complete 26-letter unicase OpenCode modular typeface (with 5x7 wide m/w and 3x7 symmetric i/l).',
    manufacturer: 'OpenType',
    designer: 'OpenCode wordmark + Complete Extension',
    designerURL: 'https://opencode.ai/font',
    glyphs,
  });
}
"""
    with open(os.path.join(OUT_DIR, "font.mjs"), "w", encoding="utf-8") as f:
        f.write(font_mjs_content)


def render_specimen_png(glyphs_data, ttf_path, out_png_path):
    W, H = 1800, 2150
    bg_color = (13, 13, 13)
    card_bg = (20, 20, 20)
    card_border = (42, 42, 42)
    grid_line_color = (38, 38, 38)
    ink_color = (245, 245, 245)
    shade_color = (62, 62, 62)
    orig_badge_color = (59, 130, 246)
    new_badge_color = (16, 185, 129)
    wide_badge_color = (245, 158, 11)
    muted_text = (150, 150, 150)

    img = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    ttf_large = ImageFont.truetype(ttf_path, 56)
    ttf_med = ImageFont.truetype(ttf_path, 35)

    def draw_modular_word(word, x_start, y_start, mod_px):
        cx = x_start
        for ch in word.lower():
            if ch == " ":
                cx += mod_px * 3
                continue
            if ch not in glyphs_data:
                continue
            d = glyphs_data[ch]
            rows = d["rows"]
            gcols = d["grid_cols"]
            for r in range(7):
                for c in range(gcols):
                    cell = rows[r][c]
                    x0 = cx + c * mod_px
                    y0 = y_start + r * mod_px
                    if cell == "S":
                        draw.rectangle([x0, y0, x0 + mod_px - 1, y0 + mod_px - 1], fill=shade_color)
                    elif cell == "#":
                        draw.rectangle([x0, y0, x0 + mod_px - 1, y0 + mod_px - 1], fill=ink_color)
            cx += mod_px * (gcols + 1)

    draw_modular_word("opencode complete", 60, 45, 12)

    cols_per_row = 6
    card_w = 270
    card_h = 310
    gap_x = 18
    gap_y = 18
    start_x = 45
    start_y = 165

    letters = sorted(glyphs_data.keys())
    for idx, letter in enumerate(letters):
        d = glyphs_data[letter]
        col_i = idx % cols_per_row
        row_i = idx // cols_per_row
        cx = start_x + col_i * (card_w + gap_x)
        cy = start_y + row_i * (card_h + gap_y)

        is_orig = letter in ORIGINAL_GLYPHS_MJS
        gcols = d["grid_cols"]
        border_col = orig_badge_color if is_orig else (wide_badge_color if gcols != 4 else card_border)
        draw.rectangle([cx, cy, cx + card_w, cy + card_h], fill=card_bg, outline=border_col, width=2 if (is_orig or gcols != 4) else 1)

        badge_col = orig_badge_color if is_orig else (wide_badge_color if gcols != 4 else new_badge_color)
        draw.rectangle([cx + 14, cy + 14, cx + 24, cy + 24], fill=badge_col)
        draw.text((cx + 32, cy + 12), f"No. {idx+1:03d} · '{letter}' ({gcols}×7)", fill=ink_color)
        tag_label = "ORIGINAL" if is_orig else (f"{gcols}×7 WIDE" if gcols == 5 else (f"{gcols}×7 TRIM" if gcols == 3 else "COMPLETED"))
        draw.text((cx + card_w - 82, cy + 12), tag_label, fill=badge_col)

        mod = 24
        gx = cx + (card_w - gcols * mod) // 2
        gy = cy + 48

        for r in range(7):
            for c in range(gcols):
                x0 = gx + c * mod
                y0 = gy + r * mod
                cell = d["rows"][r][c]
                if cell == "S":
                    draw.rectangle([x0, y0, x0 + mod, y0 + mod], fill=shade_color)
                elif cell == "#":
                    draw.rectangle([x0, y0, x0 + mod, y0 + mod], fill=ink_color)
                draw.rectangle([x0, y0, x0 + mod, y0 + mod], outline=grid_line_color, width=1)

        draw.line([gx - 10, gy + 1 * mod, gx + gcols * mod + 10, gy + 1 * mod], fill=(90, 90, 90), width=1)
        draw.line([gx - 10, gy + 6 * mod, gx + gcols * mod + 10, gy + 6 * mod], fill=(120, 120, 120), width=1)

        fy = gy + 7 * mod + 14
        draw.text(
            (cx + 14, fy),
            f"Ink/shade: {d['ink_count']} / {d['shade_count']}  ({d['coverage_pct']}%)",
            fill=muted_text,
        )
        draw.text(
            (cx + 14, fy + 20),
            f"x-height: {d['ink_xheight']}+{d['counter_xheight']}={d['total_xheight']} · {d['advance_width']}u",
            fill=muted_text,
        )

    footer_y = start_y + 5 * (card_h + gap_y) + 15
    draw.rectangle([45, footer_y, W - 45, H - 30], fill=card_bg, outline=card_border, width=1)
    draw.text((70, footer_y + 14), "LIVE FREETYPE RENDER FROM COMPILED OpenCode-Complete.ttf (WITH 5×7 'w' & 'm' AND 3×7 'i' & 'l'):", fill=new_badge_color)
    draw.text((70, footer_y + 45), "abcdefghijklmnopqrstuvwxyz", font=ttf_large, fill=ink_color)
    draw.text((70, footer_y + 115), "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG", font=ttf_med, fill=muted_text)

    img.save(out_png_path)


if __name__ == "__main__":
    glyphs_data = verify_and_build_glyph_data()
    write_mjs_files(glyphs_data)
    ttf_path = os.path.join(OUT_DIR, "OpenCode-Complete.ttf")
    ttf_size = build_truetype_font(glyphs_data, ttf_path)
    png_path = os.path.join(OUT_DIR, "specimen.png")
    render_specimen_png(glyphs_data, ttf_path, png_path)

    with open(os.path.join(OUT_DIR, "glyphs_analysis.json"), "w", encoding="utf-8") as f:
        json.dump(glyphs_data, f, indent=2)

    print(f"SUCCESS: Built Edition 2.100 (26 glyphs, OpenCode-Complete.ttf {ttf_size} bytes)")
