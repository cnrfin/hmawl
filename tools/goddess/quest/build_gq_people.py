#!/usr/bin/env python3
"""The goddess's name plate (gq9): she speaks as character 37 (0x25, people.mes "DUMMY"; her slot), whose entry in
Message.arc people.mes becomes "Goddess" + five red hearts in the same codes the name-plate hearts code (v03 main.dol,
hook 0x80102598) appends for villagers: 02 (space), 12 (red), 80 D6 x5 (hearts), 17 (colour off). That code finds no
villager record for 37 and so draws the name as it is. Her affection is full from the summoning (step 1), so the
hearts are fixed at five for now.
usage: build_gq_people.py Message.arc OUT.arc   (input: the gq text build's Message.arc: people 35 = "Joe")"""
import sys, os, hashlib
EV = os.environ.get('EVTOOLS', '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/event')
sys.path[:0] = [EV, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'paths')]
import u8arc
from mesenc import mes_entries, mes_build, enc
src, out = sys.argv[1:3]
d = open(src, 'rb').read(); a = u8arc.read(d); assert u8arc.build(a, {}) == d
k = u8arc.names(a)['people.mes']; e = mes_entries(a['files'][k])
assert e[35].startswith(enc('Joe').rstrip(b'\0')), 'expected the Joe build'
name = enc('Goddess').rstrip(b'\0') + b'\x02\x12' + b'\x80\xD6' * 5 + b'\x17'
e[37] = name + b'\0' * (4 - len(name) % 4 if len(name) % 4 else 4)
nu = u8arc.build(a, {k: mes_build(e)})
open(out, 'wb').write(nu); print(out, len(d), '->', len(nu), hashlib.sha1(nu).hexdigest()[:8])
