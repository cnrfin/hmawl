"""Joe's lines in Mukumuku's message file, so the window shows a name and heart like a villager's.
cmd_04(file, msg, speaker) with speaker != -1 maps the file to a character (table 0x80251A38: file 0x15
mukumuku.mes -> character 0x23) and draws that character's name (people.mes entry = character id) and
heart. Joe takes Mukumuku's place: people.mes 35 becomes "Joe"; his lines are appended to mukumuku.mes
from entry 38 (its own 38 stay).
usage: build_joe_mes.py mukumuku.mes people.mes OUTDIR   (vanilla US files)
The event builders import LINES (entry numbers) from here."""
import sys, os, hashlib
EV = os.environ.get('EVTOOLS', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'event'))
sys.path.insert(0, EV)
import mesenc
from mesenc import mes_entries, mes_build
mesenc.P['$'] = 0x80FD
mesenc.TAGS['<price>'] = b'\x2a\x00\x00'
FILE = 0x15
BASE = 38
TEXT = [
    ('sell_intro', "I'm selling $JOE for\n<price>G today.<wait>"),
    ('buy_q', "Wanna buy some?<yesno>"),
    ('poor', "You don't have\nenough G for that,\nkid.<wait>"),
    ('bought', "Pleasure doing\nbusiness. HODL!<wait>"),
    ('sell_q', "Wanna sell some\n$JOE?<yesno>"),
    ('what', "What!? You're selling\nyour $JOE?<wait>"),
    ('offer', "Hm, ok, I'll buy\nyour $JOE bags for\n<price>G. How does that\nsound?<yesno>"),
    ('none', "You don't have any\n$JOE, kid.<wait>"),
    ('later', "Later, kid.<wait>"),
    ('sold', "Done. Don't come\ncrying when it moons.<wait>"),
    ('intro', "Hey, I'm Joe.<wait><page>Ever heard of the\nEthereum blockchain?<wait><page>You can find some\ncrazy stuff on there.<wait>"),
    ('hint', "Come meet me by the\nbench by the bridge<wait><page>if you wanna trade\nsome memecoins.<wait>"),
    ('dig', "Y'know, I've heard\npeople mining $JOE\ncoin around here.<wait><page>That's why I came to\ncheck it out.<wait>"),
    ('winter', "Hey, my yigga.<wait><page>Crypto winter is\ncoming, so I won't be\naround until spring.<wait><page>So figure out what you\nwanna do with your\n$JOE before then.<wait>"),
    ('gift', "Woah, a $JOE for me?\nMy yigga!<wait>"),
    ('gift_again', "You keep a hold of\nthat for now my yigga.<wait><page>$JOE finna boutta.<wait>"),
]
LINES = {k: BASE + i for i, (k, _) in enumerate(TEXT)}

if __name__ == '__main__':
    muku_in, people_in, outdir = sys.argv[1:4]
    os.makedirs(outdir, exist_ok=True)
    m = open(muku_in, 'rb').read(); ents = mes_entries(m); assert mes_build(ents) == m and len(ents) == BASE
    ents += [mesenc.enc(t) for _, t in TEXT]
    open(os.path.join(outdir, 'mukumuku.mes'), 'wb').write(mes_build(ents))
    p = open(people_in, 'rb').read(); pe = mes_entries(p); assert mes_build(pe) == p
    assert pe[35].rstrip(b'\0') == mesenc.enc('Mukumuku').rstrip(b'\0')
    pe[35] = mesenc.enc('Joe')
    open(os.path.join(outdir, 'people.mes'), 'wb').write(mes_build(pe))
    for f in ('mukumuku.mes', 'people.mes'):
        b = open(os.path.join(outdir, f), 'rb').read(); print(f, hex(len(b)), hashlib.sha1(b).hexdigest()[:8])
