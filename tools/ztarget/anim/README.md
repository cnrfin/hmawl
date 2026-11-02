# Player strafe / walk-back clips (Z targeting): previews

- Player: boy_0.arc (boy_1/boy_2 are the later chapters' models) and one shared boy_0.anm.arc (126 clips,
  55-node skeleton), both inside mainchapterN.arc.clz. Clip 0 idle (59 f), clip 1 his walk (21 f).
- Skeleton: root 0; feet chains from the root 1-3 (his left, +x) / 4-6 (right), which the walk clips place
  directly; pelvis 7; legs 8-12 (left: hip 10, knee 11, ankle 12) / 13-17 (right: 15, 16, 17); spine 18-21;
  arms 22-31 / 33-42; head 43-54. Faces +z.
- skin_weighted.py: the .skn's 2-bone groups use u16 weights (/65536); the 3+ bone groups list u16 vertex
  indices at the field read as 'wt' and u16 weights at 'idx' (the first preview's spikes at the hands
  were those vertices left in the bind pose).
- strafe.py (run from scratchpad goddess/): forward = clip 1; back = clip 1 reversed; strafe = clip 1's
  per-foot forward/back swing turned sideways (x 0.65), feet flat with the walk's lift (x 0.8), knees
  re-solved with 2-bone IK (bending forward), arms calmed 60 % toward idle.
