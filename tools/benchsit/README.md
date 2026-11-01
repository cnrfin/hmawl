# Bench: sit until evening / morning (bench sit test 1)

- `build_bench_event.py Common.arc debug.mes OUT` (inputs = the Postman build: Common.arc 95208117,
  debug.mes 16e98598; needs scratchpad/event tools via EVTOOLS): appends event 407 (Common.arc entry 107)
  and puts "Sit until the evening?" / "Sit until the morning?" (with Yes/No) in debug.mes entries 9 / 10.
  Out: Common.arc a0d491f5, debug.mes 4dd04c6d.
- Script: hour < 6 -> morning prompt, Yes = cmd_43(6, 0) (today 6:00); hour < 18 -> evening prompt, Yes =
  cmd_43(18, 0); else morning prompt, Yes = cmd_44(29 - hour, 60 - minute) (to tomorrow 6:00). Both time
  commands go through func_80109E00 (the game's event time skip). Fade out 0.5 s before, ~0.5 s dark, fade in.
- pm.c: on the valley, A within 1.6 of the turned bench's seat (137.65, 176.60, from its collision box) while
  facing it (cos > 0.5), player free, not Z -> event_start(EVMGR, 407, 0, 0).
- Untested: whether jumping past midnight this way runs the overnight update like the bed does.
