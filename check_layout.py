#!/usr/bin/env python3
"""Validate page size, footer and maximum five entries. Accept variable row heights."""
import fitz,sys,re
p=fitz.open(sys.argv[1]);assert len(p)>0
for n,page in enumerate(p,1):
 assert abs(page.rect.width-841.89)<.5 and abs(page.rect.height-595.28)<.5
 text=page.get_text()
 assert re.search(r'\d+\s*/\s*\d+\s*ページ',text),('missing footer',n)
 # Main row top/bottom rules are dark, full-width, thin horizontal strokes.
 rules=[d['rect'].y0 for d in page.get_drawings() if d['type']=='s' and d['rect'].width>750 and d['rect'].height<1]
 assert len(rules)>=2 and len(rules)-1<=5,(n,rules)
 assert abs(rules[0]-93)<1 and rules[-1]<=554,(n,rules)
 print('page',n,'rows',len(rules)-1,'OK')
