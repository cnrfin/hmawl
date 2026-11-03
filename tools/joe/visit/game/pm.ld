ENTRY(pm_hook)
pad_hook_return = 0x80213D00;
scene_hook_return = 0x80177560;
player_hook_return = 0x80043124;
label_hook_return = 0x80043690;
sfx_hook_return = 0x8018B228;
exit_now = 0x800331A8;
exit_wait = 0x800332E8;
exit_frames = 0x8003319C;
nosell_return = 0x80118870;
talk_hook_return = 0x80117B14;
want_hook_return = 0x80148A50;
van_hook_return = 0x80060EFC;
msg_open = 0x801020E4;
zt_hook_return = 0x800313C8;
tilt_return1 = 0x8017B88C;
tilt_return2 = 0x8017B8F8;
face_return = 0x80030A5C;
area_return = 0x80043910;
item_pool_add = 0x8004FDA0;
SECTIONS {
  . = 0x8035EFA0;
  .pm : { *(.text.hook) *(.text*) *(.rodata*) *(.sdata*) *(.data*) *(.sbss*) *(.bss*) }
  /DISCARD/ : { *(.comment) *(.eh_frame*) *(.note*) }
}
