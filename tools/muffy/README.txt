Muffy recolour (textures only, not yet built into game files)
-------------------------------------------------------------
Pink cotton-candy hair, black dress, white bodice, white shoe details, sheer tan pantyhose,
soft orange eyes (option A). Original shading kept everywhere.

recoloured/mumu_0_b0_0_body.png   body texture (b0 image 0, 128x256)
recoloured/mumu_0_b0_1_head.png   head texture (b0 image 1, hairline band)
eye_frames_recoloured/            every non-empty eye frame of mumu_0_f0_e.tpl, iris recoloured
                                   (file number = frame index; empty 1x1 frames are left out)
original/                         the untouched textures, for comparison
src/muffycolor.py                 the script that made them

Mouth frames are unchanged. Covers Muffy's first outfit (mumu_0.arc); her chapter 3+ model
(mumu_1.arc) has its own texture and would need the same treatment.
