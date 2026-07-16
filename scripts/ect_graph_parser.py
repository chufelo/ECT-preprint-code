#!/usr/bin/env python3
"""Parse ECT_preprint.tex into a structural knowledge graph (headings, theorem-like
environments, and the \\ref/\\cref cross-reference web). Output JSON + a summary."""
import re, json, os
from collections import Counter

MAIN = "/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/ECT_preprint.tex"
BASE = os.path.dirname(MAIN)
OUT  = "/tmp/ect_graph.json"

def load(path, seen):
    if path in seen or not os.path.exists(path):
        return ""
    seen.add(path)
    txt = open(path, encoding="utf-8", errors="replace").read()
    def repl(m):
        name = m.group(1).strip()
        if not name.endswith(".tex"):
            name += ".tex"
        p = name if os.path.isabs(name) else os.path.join(BASE, name)
        return load(p, seen)
    return re.sub(r'\\(?:input|include)\{([^}]*)\}', lambda m: repl(m), txt)

def strip_comments(s):
    out = []
    for line in s.split("\n"):
        res = ""
        for i, c in enumerate(line):
            if c == "%" and (i == 0 or line[i-1] != "\\"):
                break
            res += c
        out.append(res)
    return "\n".join(out)

def read_braced(s, start):
    depth = 0
    for i in range(start, len(s)):
        if s[i] == '{':
            depth += 1
        elif s[i] == '}':
            depth -= 1
            if depth == 0:
                return s[start+1:i]
    return s[start+1:]

raw = load(MAIN, set())
text = strip_comments(raw)

LEVELS = {'part':0,'chapter':1,'section':2,'subsection':3,'subsubsection':4}
HEAD = re.compile(r'\\(part|chapter|section|subsection|subsubsection)\*?\s*\{')
LAB  = re.compile(r'\\label\{([^}]+)\}')
REF  = re.compile(r'\\(?:ref|cref|Cref|autoref|nameref|eqref|labelcref|vref)\{([^}]+)\}')
STAT = re.compile(r'Level[~ ]*([ABC]|Open)')
ENVS = ['postulate','theorem','lemma','definition','proposition','corollary','conjecture','assumption']
ENVRE = re.compile(r'\\begin\{(' + '|'.join(ENVS) + r')\*?\}')

heads = []
for m in HEAD.finditer(text):
    title = read_braced(text, m.end()-1)
    t = re.sub(r'\\[a-zA-Z]+\*?', '', title)
    t = re.sub(r'[{}$\\~]', '', t).strip()
    heads.append({"pos": m.start(), "lvl": LEVELS[m.group(1)], "type": m.group(1), "title": t})
for i, h in enumerate(heads):
    h["id"] = "N%d" % i

# body span of each heading = until the next heading of any level
for i, h in enumerate(heads):
    h["body"] = text[h["pos"]: heads[i+1]["pos"] if i+1 < len(heads) else len(text)]

label_def = {}
for h in heads:
    for lm in LAB.finditer(h["body"]):
        label_def.setdefault(lm.group(1), h["id"])

cur_part = None
for h in heads:
    if h["lvl"] == 0:
        cur_part = h["title"]
    h["part"] = cur_part or "(root)"
    sm = STAT.search(h["body"][:500])
    h["status"] = sm.group(1) if sm else ""
    lm = LAB.search(h["body"])
    h["label"] = lm.group(1) if lm else ""
    h["envs"] = Counter(em.group(1) for em in ENVRE.finditer(h["body"]))

# containment edges
contain = []
stack = {}
for h in heads:
    parent = None
    for pl in range(h["lvl"]-1, -1, -1):
        if pl in stack:
            parent = stack[pl]; break
    if parent:
        contain.append([parent, h["id"]])
    stack[h["lvl"]] = h["id"]
    for dl in [d for d in stack if d > h["lvl"]]:
        del stack[dl]

# cross-reference edges
refs = {}
for h in heads:
    for rm in REF.finditer(h["body"]):
        for tgt in rm.group(1).split(','):
            d = label_def.get(tgt.strip())
            if d and d != h["id"]:
                refs[(h["id"], d)] = refs.get((h["id"], d), 0) + 1

nodes = [{"id":h["id"],"title":h["title"][:90],"type":h["type"],"lvl":h["lvl"],
          "part":h["part"],"status":h["status"],"label":h["label"],
          "envs":dict(h["envs"])} for h in heads]
json.dump({"nodes":nodes,"contain":contain,
           "ref":[[a,b,c] for (a,b),c in refs.items()]},
          open(OUT,"w"), ensure_ascii=False)

env_total = Counter()
for h in heads:
    env_total.update(h["envs"])
print("HEADINGS total:", len(heads))
print("by type:", dict(Counter(h["type"] for h in heads)))
print("PARTS:", [h["title"] for h in heads if h["lvl"] == 0])
print("contain edges:", len(contain), "| ref edges:", len(refs))
print("headings with Level status:", sum(1 for h in heads if h["status"]),
      dict(Counter(h["status"] for h in heads if h["status"])))
print("theorem-like envs:", dict(env_total), "| total:", sum(env_total.values()))
print("labels defined:", len(label_def))
print("JSON ->", OUT)


# ---- compact section-level dataset for visualization ----
id2 = {h["id"]: h for h in heads}
parent = {}
for a, b in contain:
    parent[b] = a

def sec_anc(nid):
    cur = nid
    while cur is not None:
        if id2[cur]["lvl"] <= 2:
            return cur
        cur = parent.get(cur)
    return nid

nsub = Counter()
for h in heads:
    if h["lvl"] >= 3:
        nsub[sec_anc(h["id"])] += 1

sec_nodes = [h for h in heads if h["lvl"] <= 2]
agg = {}
for (a, b), c in refs.items():
    sa, sb = sec_anc(a), sec_anc(b)
    if sa != sb:
        agg[(sa, sb)] = agg.get((sa, sb), 0) + c

comp_nodes = [{"id":h["id"],"t":h["title"][:70],"lvl":h["lvl"],"part":h["part"],
               "st":h["status"],"lab":h["label"],"nsub":nsub.get(h["id"],0)}
              for h in sec_nodes]
comp_contain = [[a,b] for a,b in contain
                if id2[a]["lvl"] <= 2 and id2[b]["lvl"] <= 2]
comp_ref = [[a,b,c] for (a,b),c in agg.items() if c >= 2]
json.dump({"nodes":comp_nodes,"contain":comp_contain,"ref":comp_ref},
          open("/tmp/ect_graph_sections.json","w"), ensure_ascii=False)
print("COMPACT nodes:", len(comp_nodes), "| contain:", len(comp_contain),
      "| ref:", len(comp_ref))
