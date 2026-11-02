R_800438FC = 0x800438FC;
R_8004390C = 0x8004390C;
R_80043964 = 0x80043964;
R_8004397C = 0x8004397C;
R_8004BEF8 = 0x8004BEF8;
R_8004D7B0 = 0x8004D7B0;
R_8004E3B8 = 0x8004E3B8;
R_8004E5B8 = 0x8004E5B8;
R_80082F98 = 0x80082F98;
R_8010259C = 0x8010259C;
SECTIONS {
  .hearts 0x80003E00 : { *(.hearts) }   /* 684 bytes free to 0x800040AC */
  .hud    0x800048E0 : { *(.hud) }      /* 460 to 0x80004AAC */
  .hud2   0x800035B0 : { *(.hud2) }     /* 252 to 0x800036AC */
  .hud3   0x800040E0 : { *(.hud3) }     /* 204 to 0x800041AC */
  .dog    0x800036F8 : { *(.dog) }      /* 180 to 0x800037AC */
  .axgive 0x800037E0 : { *(.axgive) }   /* 204 to 0x800038AC */
  .ax     0x800038E0 : { *(.ax) }       /* 204 to 0x800039AC */
  .name   0x800041E0 : { *(.name) }     /* 204 to 0x800042AC */
  .name2  0x800042E0 : { *(.name2) }    /* 204 to 0x800043AC */
  .namedata 0x80004AE0 : { *(.namedata) } /* 204 to 0x80004BAC */
}
