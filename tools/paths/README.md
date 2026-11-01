# Villager paths

`PathData.arc` (disc root) holds 55 `path_*.pth` route networks, one per area; `path_WorldMap.pth` is the valley.
Format: see the docstring of `edit_paths.py` (waypoints x/z, two-way links with lengths, named spots that
schedules send villagers to). The route search sizes its buffers from the header's waypoint count, so
waypoints can be added.

`edit_paths.py PathData.arc OUT` (paths test 1):
- New bridge by the dig site (deck x 262.5-266.5, z 182.9-193.0): waypoints 468 (264.5, 182.6) and
  469 (264.5, 193.6), linked 175-468-469-354 and 469-178.
- Bench spot 2 (waypoint 285) moved to the turned bench's seat side (138.30, 176.60); link 285-162 replaced
  by 285-286 so it doesn't cross the bench.

Source SHA-1 `9b114b25`-uploaded disc file = the copy in RAM; output `PathData.arc` SHA-1 `ac7dbc63`
(51,692 -> 51,788 bytes). Works in game: a villager (the caveman) was seen crossing the new bridge.
