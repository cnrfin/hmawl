# Bench by the bridge field

`move_bench.py SRC OUT` edits `map{N}-p-other.oqt` in `mapc1..5.arc`: removes the bench (model 136 "bench-L")
at (140.265, 177.24) and turns the one at (137.575, 177.24) to yaw 90 at (137.60, 8.995, 176.60), so its seat
(model +z) faces east, beside the tree at (138.06, 173.90). `oqt_insert.py` and `u8arc.py` are copies from
`tools/logs` (not in this branch).

Findings:
- `mapobj{N}.col` (magic E7E3F1F4 01060000) is a quadtree of 2D collision triangles: node = 6 s16 bbox
  (1/32 units), 4 u32 child offsets (absolute, root at 8), u32 triangle count, u32 vertex count, u32 0, u32
  triangle offset and u32 vertex offset (both relative to the node); triangle = u16 attr (0x0001 / 0x0080) +
  3 u16 indices; vertex = s16 x, 0, s16 z, 0. It holds no polygon near the benches or the tree, so the
  benches have no collision (the tree's comes from the obst placements).
- NPC use of the benches: not found in the placement data; still to be confirmed in game.
