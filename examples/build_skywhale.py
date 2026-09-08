"""Rebuild the original, integer-grid Skywhale scene; no external art required."""
import json
import random
from pathlib import Path

P = ['#101527','#1c2540','#303452','#454261','#65516c','#93657d',
     '#c58b91','#efb59c','#ffdfaf','#fff1ce','#173c50','#205568',
     '#2d7680','#51a49e','#8bc6b1','#c8dfbd','#362e44','#674558',
     '#a65e60','#dc8668','#f6b875','#aa8c79','#657c88','#41566d']
frames=[]
for f in range(4):
    layers=[]
    def layer(name):
        global c
        c=[]; layers.append({'name':name,'commands':c})
    def rect(x,y,w,h,k): c.append(dict(op='rect',x=x,y=y,width=w,height=h,color=k))
    def line(x,y,xx,yy,k): c.append(dict(op='line',x1=x,y1=y,x2=xx,y2=yy,color=k))
    def poly(p,k): c.append(dict(op='polygon',points=p,color=k))
    def ell(x,y,w,h,k): c.append(dict(op='ellipse',x=x,y=y,width=w,height=h,color=k))
    def dot(x,y,k): c.append(dict(op='pixel',x=x,y=y,color=k))
    layer('01 twilight')
    rect(0,0,320,208,1)
    for y,k in [(47,2),(78,3),(110,4),(138,5),(160,6)]: rect(0,y,320,208-y,k)
    # Broken cloud shelves soften the large color-band boundaries.
    for y,k in [(47,2),(78,3),(110,4),(138,5),(160,6)]:
        for x,w,dy in [(0,37,2),(56,53,-2),(141,32,3),(195,42,-3),(274,46,2)]:
            rect(x,y+dy,w,3,k-1 if dy>=0 else k)
    # Distant sun and wind-swept cloud shelves.
    ell(222,27,55,55,6); ell(225,29,50,50,7); ell(229,32,43,43,8)
    for x,y,w in [(210,44,29),(256,65,37),(202,75,36)]: rect(x,y,w,2,3)
    rng=random.Random(42)
    for _ in range(58):
        x,y=rng.randrange(320),rng.randrange(5,85)
        if not 215<x<285: dot(x,y, [4,6,8][rng.randrange(3)])
    for x,y in [(31,25),(188,19),(297,36)]:
        line(x-2,y,x+2,y,6); line(x,y-2,x,y+2,6); dot(x,y,9)
    layer('02 distant cloud ocean')
    for x,y,w,h in [(-25,120,92,20),(230,112,112,21),(5,154,130,22),(191,161,130,25),(-30,189,180,30)]:
        ell(x,y,w,h,4); ell(x+12,y-5,w//2,h,4); rect(x,y+h//2,w,h//2,4)
        ell(x+21,y-8,w//3,12,5)
        line(x+27,y-7,x+21+w//3-8,y-7,6)
        rect(x+9,y+7,w-18,2,5)
        line(x+13,y+h//2,x+w-9,y+h//2,5)
    for x,y,w in [(12,137,39),(267,142,42),(4,176,69),(208,188,53),(144,198,75)]:
        rect(x,y,w,1,7); rect(x+9,y+3,w//2,1,6)
    # Far-away sailing islands give scale.
    for x,y in [(26,99),(282,97)]:
        poly([(x-10,y),(x+12,y),(x+3,y+7),(x-2,y+8)],3)
        line(x,y-15,x,y,5); poly([(x+2,y-15),(x+9,y-3),(x+2,y-3)],6)
    layer('03 whale body')
    # Right-facing whale; tail has a strongly forked silhouette.
    poly([(81,113),(61,106),(48,93),(30,91),(38,102),(51,115),(39,121),(24,120),(35,134),(52,138),(69,126),(90,136)],10)
    poly([(48,98),(58,112),(75,118),(64,120),(48,112),(39,98)],12)
    poly([(31,124),(49,127),(64,120),(54,132),(43,134)],11)
    poly([(69,116),(86,102),(115,91),(158,86),(200,91),(226,101),(242,117),(245,131),(234,147),(208,158),(173,165),(130,162),(101,151),(81,134)],10)
    poly([(75,116),(95,104),(126,96),(162,93),(199,97),(221,106),(235,118),(236,127),(208,130),(176,143),(127,140),(99,132)],12)
    poly([(84,111),(118,96),(159,90),(199,94),(221,104),(228,111),(195,104),(155,100),(120,103)],13)
    poly([(102,105),(133,97),(166,95),(195,99),(167,99),(134,101)],14)
    poly([(92,130),(124,142),(162,148),(201,141),(239,130),(232,145),(204,155),(171,160),(135,157),(109,147)],22)
    poly([(112,141),(146,149),(177,149),(213,140),(235,135),(225,146),(198,155),(169,158),(139,154)],14)
    poly([(125,147),(152,154),(176,155),(200,150),(215,144),(195,153),(172,158),(147,155)],15)
    # Long ventral pleats follow the body rather than a flat texture.
    for offset in range(0,5):
        line(130+offset*10,146+offset//2,148+offset*9,153+offset//3,12)
        line(148+offset*9,153+offset//3,170+offset*8,155-offset,12)
    line(204,134,234,128,10); line(234,128,241,124,10)
    ell(220,117,8,7,10); rect(222,118,3,2,8); dot(223,118,9)
    line(216,114,225,112,14)
    # Sparse connected mottling, concentrated away from the focal eye.
    rng=random.Random(9)
    for _ in range(65):
        x=rng.randrange(102,209); y=rng.randrange(107,134)
        if y<132-abs(x-157)//9: rect(x,y,rng.randrange(2,5),1,11 if y>118 else 13)
    layer('04 near flipper')
    dy=[0,1,2,1][f]
    poly([(150,134),(166,137),(172,149),(166,166+dy),(150,179+dy),(140,181+dy),(147,168),(151,151)],10)
    poly([(154,139),(161,141),(162,155),(152,170+dy),(145,176+dy),(155,156)],12)
    line(157,144,156,156,14)
    layer('05 city terraces')
    poly([(97,99),(117,88),(180,86),(207,96),(197,103),(118,106)],16)
    poly([(99,96),(122,87),(179,84),(206,93),(195,99),(122,101)],21)
    line(107,96,145,98,8); line(145,98,196,95,20)
    for x in range(112,196,9): line(x,99,x,103,17)
    # Buildings with side planes, roof rims, shutters and chimney clusters.
    def house(x,y,w,h):
        rect(x,y,w,h,18); rect(x+w-5,y,5,h,17)
        poly([(x-3,y),(x+w//2,y-10),(x+w+2,y),(x+w-3,y+3),(x,y+3)],10)
        poly([(x-3,y),(x+w//2,y-10),(x+w//2+1,y-7),(x+1,y+1)],13)
        line(x+1,y+4,x+w-7,y+4,19)
        for xx in range(x+3,x+w-5,6):
            for yy in range(y+7,y+h-2,8):
                rect(xx-1,yy-1,4,5,16); rect(xx,yy,2,3,8); dot(xx,yy+2,20)
        rect(x+w-7,y-10,3,7,17); dot(x+w-7,y-10,20)
    house(109,77,21,20); house(132,70,22,26); house(178,73,20,21)
    house(153,78,23,20)
    layer('06 observatory and garden')
    # Hero observatory tower: copper dome, glass lantern, brass telescope.
    rect(159,48,15,33,17); rect(160,48,8,32,19); rect(160,51,2,27,20)
    rect(157,46,19,3,21); line(158,46,175,46,8)
    rect(158,38,17,8,10)
    for xx in [160,165,170]: rect(xx,39,3,6,8); line(xx,44,xx+2,44,20)
    poly([(155,38),(157,33),(161,29),(169,28),(175,32),(178,38)],12)
    poly([(156,37),(159,32),(164,29),(168,29),(163,33),(162,37)],14)
    line(155,38,178,38,10); line(166,27,166,22,20); dot(166,21,9)
    poly([(169,30),(184,23),(187,27),(172,33)],21); line(172,30,184,24,8); line(185,23,187,27,10)
    for yy in [54,65]: rect(165,yy,4,7,16); rect(166,yy+1,2,5,8)
    rect(156,80,21,3,20)
    # A cypress and small rooftop gardens.
    for x,y,h in [(101,82,17),(200,83,16),(181,65,11),(130,85,9)]:
        line(x,y,x,y+h,17)
        poly([(x,y-8),(x-4,y+4),(x-3,y+10),(x+4,y+8),(x+3,y)],10)
        line(x,y-4,x-2,y+6,13)
    # Suspension lanterns under the traveling city.
    for x,y in [(112,113),(188,116),(207,108)]:
        line(x,y-12,x,y,21); rect(x-2,y,5,7,17); rect(x-1,y+1,3,4,20); dot(x,y+2,9)
    layer('07 pennants and travelers')
    for x,y in [(139,54),(191,58)]:
        line(x,y,x,y+10,21)
        poly([(x+1,y),(x+10,y+([0,1,2,1][f])),(x+7,y+4),(x+1,y+3)],19)
        line(x+1,y,x+5,y,8)
    # A tiny passenger standing at the bow railing.
    ell(204,84,3,3,8); rect(204,87,3,5,16); line(204,91,203,94,16); line(206,91,207,94,16)
    line(202,91,214,91,21); line(211,91,211,96,21)
    # Warm floating lanterns, with discrete rise over the loop.
    for i,(x,y) in enumerate([(62,64),(85,43),(244,93),(270,127),(48,157)]):
        yy=y-[0,1,2,1][(f+i)%4]
        rect(x-2,yy-2,5,7,5); rect(x-1,yy-1,3,4,20); dot(x,yy,9); line(x,yy+5,x-1,yy+7,6)
    layer('08 foreground clouds')
    for x,y,w,h in [(-38,186,111,36),(244,180,105,34),(284,166,68,30)]:
        ell(x,y,w,h,1); ell(x+17,y-7,w//2,h,1); rect(x,y+h//2,w,h,1)
        line(x+19,y+4,x+w-17,y+4,3)
    frames.append({'name':f'drift-{f+1}','duration':180,'layers':layers})
scene={'version':1,'canvas':{'width':320,'height':208},'palette':P,'frames':frames,'tags':[{'name':'lantern-drift','from':0,'to':3,'direction':'forward'}]}
Path(__file__).with_name('skywhale.json').write_text(json.dumps(scene,indent=2)+'\n')
