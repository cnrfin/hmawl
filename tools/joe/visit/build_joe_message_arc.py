"""Joe's name in the name plate: the window draws people.mes from Message.arc (loaded at boot), not the loose
people.mes. Entry 35 (character 0x23, Mukumuku's slot) -> "Joe".
usage: build_joe_message_arc.py Message.arc OUT.arc   (input: the $JOE coin build, 3205b29b)"""
import sys, os, hashlib
EV = os.environ.get('EVTOOLS', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'event'))
sys.path[:0] = [EV, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'paths')]
import u8arc
from mesenc import mes_entries, mes_build, enc
src, out = sys.argv[1:3]
d = open(src, 'rb').read(); a = u8arc.read(d); assert u8arc.build(a, {}) == d
k = u8arc.names(a)['people.mes']; e = mes_entries(a['files'][k])
assert e[35] in (enc('Mukumuku'), enc('Joe')), e[35]
e[35] = enc('Joe')
nu = u8arc.build(a, {k: mes_build(e)})
open(out, 'wb').write(nu); print(out, len(d), '->', len(nu), hashlib.sha1(nu).hexdigest()[:8])
