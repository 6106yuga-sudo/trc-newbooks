#!/usr/bin/env python3
"""TRC 10/17-style PDF. Default 5 records/page, adaptive rows and pagination on overflow."""
import json,sys,re,datetime,math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.colors import HexColor
W,H=landscape(A4); FONT='HeiseiKakuGo-W5';pdfmetrics.registerFont(UnicodeCIDFont(FONT))
DARK=HexColor('#205b42');GREEN=HexColor('#ddeedc');LIGHT=HexColor('#eff5ef');RULE=HexColor('#afc6b5')
LEFT=30;RIGHT=811.9; START=93;BOTTOM=553; BASE=92; MAX=5

def wrap(s,width,size):
    lines=[]
    for paragraph in str(s).replace('\r','').split('\n'):
        line=''
        for ch in paragraph:
            if line and pdfmetrics.stringWidth(line+ch,FONT,size)>width:
                lines.append(line);line=ch
            else:line+=ch
        lines.append(line)
    return lines

def put(c,lines,x,y,size,lead):
    c.setFont(FONT,size)
    for i,line in enumerate(lines):c.drawString(x,H-y-i*lead,line)

def right(c,s,x,y,size):
    c.setFont(FONT,size);c.drawRightString(x,H-y,s)

def validate(doc):
    if not doc.get('source_verified'):raise ValueError('source_verified=true が必要')
    datetime.date.fromisoformat(doc['date'])
    if not doc.get('items'):raise ValueError('items がありません')
    for i,b in enumerate(doc['items']):
        for k in ('section','category','title','author','publisher','summary','reason','concern'):
            if not isinstance(b.get(k),str) or not b[k].strip():raise ValueError(f'item {i}: {k} が未入力')
        if b['section'] not in ('一般書','児童書・絵本'):raise ValueError('section 不正')
        if b.get('price_yen') is not None and (type(b['price_yen']) is not int or b['price_yen']<0):raise ValueError('price_yen 不正')

def measure(b):
    # Text sizes are fixed. Rows expand only as much as necessary.
    title='『'+b['title']+'』 '+b['author']+' ｜ '+b['publisher']
    lines={'title':wrap(title,552,9),'summary':wrap(b['summary'],330,7.4),
           'reason':wrap(b['reason'],192,7.4),'concern':wrap(b['concern'],119,7.2)}
    header=max(34,14+len(lines['title'])*12+8)
    body=max(58,30+max(len(lines['summary']),len(lines['reason']),len(lines['concern']))*10.5+7)
    return lines, max(BASE,math.ceil(header+body)),header

def paginate(items):
    pages=[]; page=[];used=0
    for b in items:
        lines,height,header=measure(b)
        if height>BOTTOM-START:raise ValueError('1件がページ全体に収まりません。本文の編集が必要です: '+b['title'])
        if page and (len(page)>=MAX or used+height>BOTTOM-START):
            pages.append(page);page=[];used=0
        page.append((b,lines,height,header));used+=height
    if page:pages.append(page)
    return pages

def render(doc,path):
    validate(doc);c=canvas.Canvas(path,pagesize=(W,H));c.setTitle('TRC新刊情報注目図書一覧')
    date=datetime.date.fromisoformat(doc['date']);ds=f'{date.year}年{date.month}月{date.day}日（'+['月','火','水','木','金','土','日'][date.weekday()]+'）'
    items=doc['items'];a=sum(b['section']=='一般書' for b in items);k=len(items)-a
    for section in ('一般書','児童書・絵本'):
        pages=paginate([b for b in items if b['section']==section])
        for pn,page in enumerate(pages,1):
            c.setFillColor(GREEN);c.roundRect(30,H-76,W-60,60,5,stroke=0,fill=1)
            c.setFillColor(DARK);put(c,['TRC新刊情報注目図書一覧  '+section],42,49,13,12)
            right(c,ds,W-42,49,11)
            put(c,['参照元：TRC新刊図書オープンデータ ｜ 大分類：書誌情報より推定 ｜ 価格：税込'],42,68,7.5,10)
            right(c,f'全{len(items)}点(新刊図書{a}点,児童書{k}点)',W-42,68,8)
            y=START
            # Determine category blocks before drawing cells.
            spans=[];pos=y
            for b,lines,height,header in page:
                spans.append((pos,pos+height));pos+=height
            for i,(b,lines,height,header) in enumerate(page):
                t,bt=spans[i]
                if i==0 or page[i-1][0]['category']!=b['category']:
                    j=i+1
                    while j<len(page) and page[j][0]['category']==b['category']:j+=1
                    end=spans[j-1][1]
                    c.setFillColor(LIGHT);c.rect(LEFT,H-end,64,end-t,fill=1,stroke=0)
                    c.setFillColor(DARK);c.setFont(FONT,9)
                    c.drawCentredString(62,H-(t+end)/2,b['category'])
                c.setStrokeColor(DARK);c.setLineWidth(1.1);c.line(LEFT,H-t,RIGHT,H-t)
                c.setStrokeColor(RULE);c.setLineWidth(.5)
                c.line(94,H-(t+header),RIGHT,H-(t+header))
                c.line(671.9,H-t,671.9,H-(t+header))
                c.line(458.1,H-(t+header+7),458.1,H-(bt-9))
                c.line(671.9,H-(t+header+7),671.9,H-(bt-9))
                c.setFillColor(DARK);put(c,lines['title'],106,t+20,9,12)
                price='￥'+format(b['price_yen'],',') if b.get('price_yen') is not None else '価格未確認'
                right(c,price,800,t+20,9)
                for label,x in [('概要',117),('選考理由',468),('懸念事項',682)]:put(c,[label],x,t+header+13,7.8,10)
                for key,x,sz in [('summary',117,7.4),('reason',468,7.4),('concern',682,7.2)]:
                    put(c,lines[key],x,t+header+28,sz,10.5)
            c.setStrokeColor(DARK);c.setLineWidth(1.1);c.line(LEFT,H-spans[-1][1],RIGHT,H-spans[-1][1])
            right(c,f'{pn} / {len(pages)} ページ',W-42,576,8);c.showPage()
    c.save()
if __name__=='__main__':
    if len(sys.argv)!=3:sys.exit('Usage: python scripts/render_trc.py reviewed.json output.pdf')
    with open(sys.argv[1],encoding='utf-8') as f:doc=json.load(f)
    render(doc,sys.argv[2]);print('Created:',sys.argv[2])
