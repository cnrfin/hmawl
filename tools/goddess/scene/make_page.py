"""Spring Scene Director page (the first summoning's shot editor): make_page.py three.min.js OUT.html;
make_page.py x --json writes spring_scene.json (the proposal) that build_gq_scene.py reads."""
import json, sys
import os
HERE = os.path.dirname(os.path.abspath(__file__))
T = open(os.path.join(HERE, 'director_template.html')).read()
three = '' if '--json' in sys.argv else open(sys.argv[1]).read()   # three@0.128.0 build/three.min.js (npm)
L = json.load(open(os.path.join(HERE, '..', 'dialogue', 'goddess_lines_batch1.json')))
lines = {k: L[k] for k in ['A%d' % i for i in range(1, 11)]}
def k(yaw, dist, height, aim): return dict(yaw=yaw, dist=dist, height=height, aim=aim)
def shot(name, subject='goddess', look='subject', start=None, end=None, ease='inout', seconds=0, pause=0, lines=(),
         action='stand', actionWhen='start', actionSeconds=3, motion='idle', flash=False, splash=False, note=''):
    return dict(name=name, subject=subject, look=look, start=start, end=end or dict(start), ease=ease, seconds=seconds,
                pause=pause, lines=list(lines), action=action, actionWhen=actionWhen, actionSeconds=actionSeconds,
                motion=motion, flash=flash, splash=splash, note=note)
S = [
 shot('The spring', 'farmer', 'goddess', k(0, 6, 3.5, .3), k(0, 4, 2.6, .3), seconds=3, action='under', flash=True, note='Fade in from the white flash behind the farmer, high up.'),
 shot('Glow', start=k(25, 4.5, .4, .2), end=k(10, 3.5, .6, .2), seconds=2, action='under', note='Low over the water; light gathers.'),
 shot('The rise', start=k(10, 3.2, .5, .6), end=k(0, 3.0, 1.0, 1.4), seconds=4, action='rise', actionSeconds=3.5, splash=True, note='Camera tilts up with her.'),
 shot('Silence', start=k(0, 2.2, 1.5, 1.45), end=k(0, 1.8, 1.5, 1.45), pause=1.0, lines=['A1'], note='Eyes closed. Hold before she speaks.'),
 shot('Eyes open', start=k(0, 1.8, 1.5, 1.45), lines=['A2']),
 shot('Over the shoulder', start=k(160, 1.6, 1.6, 1.0), look='farmer', lines=['A3'], note='Behind her, looking at the farmer.'),
 shot('Medium', start=k(-20, 3.0, 1.3, 1.3), lines=['A4']),
 shot('Lore orbit', start=k(-40, 3.4, 1.2, 1.3), end=k(40, 3.4, 1.6, 1.3), ease='linear', lines=['A5'], motion='explain', note='Slow orbit while she tells the story.'),
 shot('Push-in', start=k(5, 2.4, 1.5, 1.45), end=k(5, 1.9, 1.5, 1.45), lines=['A6']),
 shot('Hero low angle', start=k(15, 2.6, .5, 1.5), lines=['A7'], motion='plead (bow)', note='"I am the Harvest Goddess." Looking up at her.'),
 shot('Two-shot', 'pair', start=k(90, 5.0, 1.6, 1.0), end=k(90, 4.5, 1.6, 1.0), lines=['A8', 'A9'], motion='explain', note='A9 plays only in year 1.'),
 shot('Farewell', start=k(0, 3, 1.4, 1.4), end=k(0, 7, 4.5, .4), lines=['A10'], action='sink', actionWhen='afterLines', actionSeconds=3, splash=True, note='Crane up and back as she sinks.'),
 shot('Quiet', 'farmer', 'goddess', k(0, 5, 3, .2), k(0, 5.5, 3.2, .2), seconds=2, action='under', note='The empty pool; music returns.'),
]
P = dict(settings=dict(letterbox=True, musicFade=True, fov=40, music='Marin Jazz', musicShot=5), shots=S)
if '--json' in sys.argv: json.dump(dict(file='spring_scene', version=1, **P), open(os.path.join(HERE, 'spring_scene.json'), 'w'), indent=1); sys.exit()
out = T.replace('__THREE__', three).replace('__LINES__', json.dumps(lines)).replace('__PROPOSAL__', json.dumps(P, indent=1))
open(sys.argv[2], 'w').write(out); print(len(out))
