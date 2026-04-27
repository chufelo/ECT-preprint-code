#!/usr/bin/env python3
"""
Update EW node in master derivation map (.dot files) to reflect Hopf-locking
and layered OP-EW programme.
"""
from pathlib import Path

FIG = Path('/Users/chufelo/Documents/Physics/VDT/ECT/LaTex/figures')

# OLD EW node label (HTML escapes preserved verbatim from grep output):
# Main version:
old_main = (
    'EW [label=<<B>Electroweak architecture</B><BR/>'
    '<FONT POINT-SIZE="9">SU(2)&#215;U(1) structural route<BR/>'
    'v&#8322;-matched W&#177;, Z, H scaffold</FONT>>];'
)
new_main = (
    'EW [label=<<B>Electroweak architecture</B><BR/>'
    '<FONT POINT-SIZE="9">Pre-locking SU(2)<SUB>orient</SUB>&#215;U(1)<SUB>&#952;</SUB>'
    ' &#8594; U(1)<SUB>diag</SUB><BR/>'
    'Hopf-fibered S&#179; vacuum (App. Hopf-locking)<BR/>'
    'v&#8322;= &#966;<SUB>0</SUB> exp(&#8722;&#8459;<SUB>EW</SUB>),'
    ' &#8459;<SUB>EW</SUB>&#8776;36.8<BR/>'
    'Layered OP-EW-* programme</FONT>>];'
)

# Pop version (only differs by trailing `, fillcolor="white"` extension)
old_pop = (
    'EW [label=<<B>Electroweak architecture</B><BR/>'
    '<FONT POINT-SIZE="9">SU(2)&#215;U(1) structural route<BR/>'
    'v&#8322;-matched W&#177;, Z, H scaffold</FONT>>, fillcolor="white"];'
)
new_pop = (
    'EW [label=<<B>Electroweak architecture</B><BR/>'
    '<FONT POINT-SIZE="9">Pre-locking SU(2)<SUB>orient</SUB>&#215;U(1)<SUB>&#952;</SUB>'
    ' &#8594; U(1)<SUB>diag</SUB><BR/>'
    'Hopf-fibered S&#179; vacuum (App. Hopf-locking)<BR/>'
    'v&#8322;= &#966;<SUB>0</SUB> exp(&#8722;&#8459;<SUB>EW</SUB>),'
    ' &#8459;<SUB>EW</SUB>&#8776;36.8<BR/>'
    'Layered OP-EW-* programme</FONT>>, fillcolor="white"];'
)

for name, old, new in [
    ('fig_ect_derivation_map.dot', old_main, new_main),
    ('fig_ect_derivation_map_pop.dot', old_pop, new_pop),
]:
    p = FIG / name
    t = p.read_text()
    if old not in t:
        print(f"  FAIL {name}: anchor not found")
        continue
    cnt = t.count(old)
    if cnt != 1:
        print(f"  FAIL {name}: anchor count={cnt}")
        continue
    p.write_text(t.replace(old, new))
    print(f"  OK   {name}: EW node updated")
