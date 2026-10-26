#!/usr/bin/env python3
"""Query the main.dol disassembly (asm/main/game/*.s) by function.

usage:
  asmq.py [--asm-dir DIR] grep REGEX    matches grouped by enclosing label
  asmq.py [--asm-dir DIR] func NAME     print one label's body
  asmq.py [--asm-dir DIR] callers NAME  labels containing a b/bl to NAME

DIR defaults to asm/main/game in this repo. The .s files use CRLF line
endings; they are read as-is and the CRs are stripped in memory.

Note: the splitter also puts func_ labels on branch targets, so a "function"
here is the code between two labels, not necessarily a real function. Check
for a stwu r1 / mflr prologue before calling something a function start.
Reads only; writes nothing.
"""
import argparse, glob, os, re

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LINE = re.compile(r'^/\* ([0-9A-F]{8}) [0-9A-F]{8}  (?:[0-9A-F]{2} ){4}\*/\t(.*)$')
LABEL = re.compile(r'^([A-Za-z_][\w@$]*):$')

def load(asm_dir):
    funcs, order = {}, []
    paths = sorted(glob.glob(os.path.join(asm_dir, '*.s')))
    if not paths:
        raise SystemExit(f'no .s files in {asm_dir}')
    for path in paths:
        cur = None
        with open(path, encoding='latin-1') as f:
            for raw in f:
                raw = raw.rstrip('\r\n')
                m = LABEL.match(raw)
                if m and not m.group(1).startswith('lbl_'):
                    cur = m.group(1); funcs.setdefault(cur, []); order.append(cur)
                    continue
                if m and cur:
                    funcs[cur].append(('', raw)); continue
                m = LINE.match(raw)
                if m and cur:
                    funcs[cur].append((m.group(1), m.group(2)))
    return funcs, order

def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--asm-dir', default=os.path.join(REPO, 'asm', 'main', 'game'))
    ap.add_argument('cmd', choices=['grep', 'func', 'callers'])
    ap.add_argument('arg')
    a = ap.parse_args()
    funcs, order = load(a.asm_dir)
    if a.cmd == 'grep':
        r = re.compile(a.arg)
        for f in order:
            hits = [(ad, t) for ad, t in funcs[f] if ad and r.search(t)]
            if hits:
                print(f, len(hits), ' | '.join(f'{ad}:{t}' for ad, t in hits[:4]))
    elif a.cmd == 'func':
        if a.arg not in funcs:
            raise SystemExit(f'{a.arg}: no such label')
        for ad, t in funcs[a.arg]:
            print(f'{ad} {t}' if ad else t)
    else:
        r = re.compile(r'\bb(l)?\s+' + re.escape(a.arg) + r'\b')
        for f in order:
            hits = [ad for ad, t in funcs[f] if ad and r.search(t)]
            if hits:
                print(f, ' '.join(hits))

main()
