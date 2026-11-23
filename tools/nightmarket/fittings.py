"""Fabricated shop fittings. Dimensions are local metres; none are camera facing."""
import math
import random
from mesh import add, sub, mul, unit, cross, TAU, interp


def frame(p,c,w,h,thick,depth,mat):
    x,y,z=c
    for side in (-1,1):
        p.box((x+side*(w-thick)/2,y,z),(thick,h,depth),mat,.006)
        p.box((x,y+side*(h-thick)/2,z),(w-2*thick,thick,depth),mat,.006)


def panel(p,c,w,h,art,border='Iron',d=.12):
    x,y,z=c; p.box(c,(w,h,d),border,.022)
    frame(p,(x,y,z-d/2-.012),w-.018,h-.018,.027,.033,'Patina')
    p.print((x,y,z-d/2-.025),w-.079,h-.079,art)
    for i in (-1,1):
        for j in (-1,1): p.rod((x+i*(w/2-.025),y+j*(h/2-.025),z-d*.57),(x+i*(w/2-.025),y+j*(h/2-.025),z-d*.65),.009,'Zinc',6)


def canopy(p,w,d,mat,bulbs,drop=.16,end_brackets=False):
    # Folded corrugated steel with real upper and lower faces and edge teeth.
    steps=round(w/.049)
    for i in range(steps):
        x=-w/2+i*w/steps; xx=x+w/steps; y=.021*(i%2); yy=.021*((i+1)%2)
        face=[(x,y,0),(xx,yy,0),(xx,yy-drop,-d),(x,y-drop,-d)]
        n=unit(cross(sub(face[1],face[0]),sub(face[3],face[0])))
        p.face(face,n,mat); p.face([add(q,(0,-.014,0)) for q in face],mul(n,-1),mat)
        p.face([face[2],face[3],add(face[3],(0,-.014,0)),add(face[2],(0,-.014,0))],(0,0,-1),mat)
    for q in (-.92,-.35,.36,.92):
        x=q*w/2
        if mat=='Zinc':  # Seat the herbalist rafters below the sloping sheet under the balcony.
            p.rod((x,-.082,0),(x,-drop-.082,-d+.026),.042,'Iron',4)
        else: p.box((x,-.105,-d*.5),(.045,.065,d),'Iron')
        if end_brackets:
            if abs(q)<.9: continue   # No wall to anchor to above the open doorway.
            # Use an over-stay on the sign end so the brace clears the lettering.
            anchor,tip=(.31,-drop+.017) if q>0 else (-.49,-drop-.08)
            p.box((x,anchor,.031),(.084,.17,.061),'Rust',.008)
            p.rod((x,anchor,0),(x,tip,-d*.91),.014,'Patina',8)
        else: p.rod((x,-.62,0),(x,-drop-.08,-d*.91),.018,'Patina',8)
    for z in [-.08,-d*.52,-d+.045]: p.box((0,-.045+z/d*drop,z),(w,.035,.04),'Zinc')
    if mat=='Mustard':
        for i in range(9):
            x=(i/8-.5)*w; p.rod((x,-.095,-.005),(x,-drop-.095,-d+.018),.047,'Wood',4)
            p.rod((x,-.43,-.022),(x,-drop-.11,-d*.69),.027,'Wood',4)
    if bulbs:
        for i in range(bulbs):
            x=(i+.5)*w/bulbs-w/2; p.rod((x,-drop-.03,-d+.055),(x,-drop-.083,-d+.055),.014,'Iron',6)
            p.lathe((x,-drop-.11,-d+.055),[(-.021,.01),(-.012,.021),(.01,.023),(.03,.014)],'HoneyTube',10)


def window(p,c,w,h,lit,rail=False):
    x,y,z=c; p.box(c,(w+.15,h+.14,.13),'Soot',.02)
    p.box((x,y,z-.078),(w,h,.045),'WindowAmber' if lit else 'Glass')
    frame(p,(x,y,z-.13),w+.035,h+.035,.043,.09,'Patina')
    for i in (-1,1): p.box((x+i*w/6,y,z-.14),(.022,h,.035),'Iron')
    for frac in (-.20,.28): p.box((x,y+h*frac,z-.144),(w,.021,.04),'Iron')
    p.box((x,y-h*.5-.035,z-.19),(w+.19,.075,.34),'Curb',.013)
    if rail:
        p.box((x,y-h*.45,z-.30),(w+.2,.10,.57),'Zinc',.012)
        for j in range(9):
            xx=x+w*(j/8-.5); p.rod((xx,y-h*.42,z-.54),(xx,y-h*.42+.45,z-.54),.012,'Patina',6)
        for yy in [y-h*.42+.12,y-h*.42+.46]: p.rod((x-w*.54,yy,z-.54),(x+w*.54,yy,z-.54),.021,'Iron',8)


def door(p,c,w,h,shutter=False):
    x,y,z=c; p.box(c,(w+.12,h+.07,.12),'Iron'); p.box((x,y,z-.082),(w,h,.055),'Shutter' if shutter else 'Celadon',.018)
    frame(p,(x,y,z-.135),w+.04,h+.02,.057,.095,'Patina')
    if shutter:
        for i in range(1,round(h/.077)):
            yy=y-h*.5+i*.077; p.box((x,yy,z-.121),(w-.11,.021,.032),'Zinc',.006)
    else:
        for yy,hh in [(y+h*.24,h*.30),(y-h*.24,h*.30)]:
            frame(p,(x,yy,z-.122),w*.76,hh,.025,.026,'Zinc')
            if yy>y:
                for i in range(9): p.box((x,yy+(i-4)*hh*.085,z-.128),(w*.64,.018,.019),'Patina')
        p.box((x+w*.34,y-.08,z-.177),(.035,.16,.075),'Iron',.012)
    p.box((x,y-h/2-.017,z-.18),(w+.16,.04,.4),'Curb',.01)


def louvres(p,c,w,h,n,blade,cover):
    x,y,z=c; pitch=h/n
    p.box(c,(w,h,.018),'Iron',.007)
    # Folded blades: the downward-facing lip shields the dark slot beneath it.
    for i in range(n):
        top=y+h/2-(i+.04)*pitch; lip=top-cover*pitch; front=z-.012-.34*pitch
        a,b=x-w/2+.008,x+w/2-.008
        p.face([(a,top,z-.011),(b,top,z-.011),(b,lip,front),(a,lip,front)],(0,z-.011-front,lip-top),blade)
        p.box((x,lip-.002,front),(b-a,.004,.004),blade)


def dispensary_leaf(p,x,span,head):
    # The face of the leaf is 30 cm behind the masonry, with a stop behind it.
    h=head-.23; mid=.157+h/2; w=span-.14
    p.box((x,mid,.353),(span,h+.09,.048),'Iron')
    p.box((x,mid,.323),(w,h,.046),'Celadon',.013)
    frame(p,(x,mid,.294),w+.09,h+.09,.041,.067,'Patina')
    louvres(p,(x,head-.41,.286),w*.74,.43,7,'Patina',.72)
    p.box((x+w*.37,1.08,.277),(.035,.13,.042),'Iron',.008)
    # A narrow surface-mounted service cabinet beside (not part of) the leaf.
    bx=x+span/2+.22
    p.box((bx,1.30,-.146),(.36,1.09,.205),'IvoryEnamel',.018)
    p.box((bx,1.30,-.255),(.325,1.045,.024),'IvoryEnamel',.011)
    louvres(p,(bx,1.29,-.278),.21,.84,32,'IvoryEnamel',.84)


def fan(p,c,size=1,double=False):
    x,y,z=c; r=.285*size; w=(1.36 if double else .88)*size; h=.74*size; d=.48*size
    p.box(c,(w,h,d),'Celadon',.03*size)
    for dx in ((-.31,.31) if double else (-.073,)):
        xx=x+dx*size; zz=z-d*.5-.01
        p.disc((xx,y,zz),r,.025,'Rubber',sides=28)
        for i in range(5):
            a=i*TAU/5; pts=[(xx+rr*r*math.cos(a+t),y+rr*r*math.sin(a+t),zz-.019) for rr,t in [(.12,0),(.84,.22),(.90,.64),(.28,.53)]]
            p.face(pts,(0,0,-1),'Patina')
        p.disc((xx,y,zz-.03),r*.17,.026,'Iron',sides=14)
        for ring in [.45,.76,1.0]:
            loop=[(xx+r*ring*math.cos(j*TAU/24),y+r*ring*math.sin(j*TAU/24),zz-.046) for j in range(25)]
            p.tube(loop,.006*size,'Zinc',5,False)
        for j in range(4):
            a=j*math.pi/4; dx1,dy=r*math.cos(a),r*math.sin(a)
            p.rod((xx-dx1,y-dy,zz-.047),(xx+dx1,y+dy,zz-.047),.005*size,'Iron',5)
    if not double:
        for j in range(7): p.box((x+w*.355,y+(j-3)*h*.095,z-d/2-.007),(w*.15,.015*size,.016),'Patina')
    for xx in [x-w*.36,x+w*.36]:
        p.box((xx,y-h*.5-.029,z+.018),(.064,.055,d+.12),'Rust'); p.rod((xx,y-h*.5-.20,z+d/2+.04),(xx,y-h*.5-.04,z-d*.35),.013,'Iron')


def plant(p,c,height,seed):
    rg=random.Random(seed); x,y,z=c; r=height*.23
    p.lathe(c,[(0,r*.68),(.24*height,r),(.27*height,r*1.08),(.31*height,r*1.06),(.31*height,r*.88)],'Pottery',16)
    for i in range(18):
        a=i*2.39996+rg.uniform(-.26,.26); width=height*rg.uniform(.025,.058); spread=height*rg.uniform(.17,.53); top=height*rg.uniform(.59,.99)
        base=(x,y+height*.28,z); mid=(x+math.cos(a)*spread*.52,y+top,z+math.sin(a)*spread*.52)
        tip=(x+math.cos(a)*spread,y+top-height*.17,z+math.sin(a)*spread); side=mul((-math.sin(a),0,math.cos(a)),width)
        p.rod(base,mid,height*.006,'Foliage',5)
        rib=add(mid,(0,.018,0)); left,right=add(mid,side),sub(mid,side)
        for tri in [[base,left,rib],[rib,left,tip],[base,rib,right],[right,rib,tip]]:
            n=unit(cross(sub(tri[1],tri[0]),sub(tri[2],tri[0]))); mat='LeafTip' if i%5==0 else 'Foliage'
            p.face(tri,n,mat); p.face(list(reversed(tri)),mul(n,-1),'Foliage')


def fern(p,c,r,seed):
    rg=random.Random(seed)
    for k in range(9):
        a=TAU*k/9+rg.uniform(-.29,.29); span=r*rg.uniform(.83,1.3); high=r*rg.uniform(.78,1.48)
        def stempos(t): return add(c,(math.cos(a)*span*t,high*(1.64*t-1.18*t*t),math.sin(a)*span*t))
        p.tube([stempos(i/8) for i in range(9)],.0024,'LeafTip',5)
        for j in range(1,11):
            t=j/11; base=stempos(t); blade=r*.39*(math.sin(math.pi*t)**.6); fwd=(math.cos(a),0,math.sin(a))
            for side in [-1,1]:
                tip=add(base,(blade*(-math.sin(a)*side+.34*fwd[0]),blade*.32,blade*(math.cos(a)*side+.34*fwd[2])))
                mid=interp(base,tip,.48); mid=add(mid,(0,.010,0)); wing=mul(fwd,blade*.20)
                points=[base,add(mid,wing),tip,sub(mid,wing)]; n=unit(cross(sub(points[1],base),sub(points[3],base)))
                p.face(points,n,'LeafTip' if j>7 else 'Foliage'); p.face(list(reversed(points)),mul(n,-1),'Foliage')


def crate(p,c,w,h,d,mat='Wood'):
    x,y,z=c; p.box(c,(w-.025,h-.015,d-.025),mat,.008)
    for s in [-1,1]:
        for yy in (y-h*.4,y+h*.4): p.box((x,yy,z+s*d*.5),(w,.036,.03),'Patina')
        for xx in (x-w*.40,x+w*.40): p.box((xx,y,z+s*d*.5),(.035,h,.031),mat)
    for j in range(1,4): p.box((x-w*.5+w*j/4,y,z-d*.5-.004),(.009,h*.76,.007),'Iron')


def barrel(p,c,r,h,mat):
    p.lathe(c,[(0,r*.91),(.035*h,r),(.1*h,r),(.13*h,r*.98),(.28*h,r*.99),(.30*h,r*1.035),(.34*h,r),(.68*h,r),(.72*h,r*1.035),(.76*h,r*.99),(.94*h,r),(.975*h,r*1.025),(h,r*.97)],mat,24)
    x,y,z=c; p.rod((x+r*.54,y+h,z),(x+r*.54,y+h+.012,z),r*.12,'Iron',10)


def lampion(p,c,r,h):
    x,y,z=c; profile=[(-.5,.52),(-.415,.75),(-.25,.93),(0,1),(.25,.92),(.415,.75),(.5,.51)]
    p.lathe(c,[(k*h,v*r) for k,v in profile],'Lampion',18,label=True)
    for k in (-1,1):
        yy=y+k*(h*.49); p.rod((x,yy-.008,z),(x,yy+.008,z),r*.57,'Mustard',14)
    for j in range(8):
        a=j*TAU/8; p.tube([(x+r*v*math.cos(a),y+k*h,z+r*v*math.sin(a)) for k,v in profile],r*.019,'Ruby',4)
    p.rod((x,y-.50*h,z),(x,y-.62*h,z),r*.039,'Mustard',6)


def glass(p,points,z,r,mat,bend):
    """Bend a round tube in the sign plane; sink its two insulated ends into the tray."""
    path=[points[0]]
    for a,b,c in zip(points,points[1:],points[2:]):
        cut=min(bend,.42*math.dist(a,b),.42*math.dist(b,c))
        u=add(b,mul(unit(sub(a,b)),cut)); v=add(b,mul(unit(sub(c,b)),cut))
        for j in range(5):
            t=j/4; path.append(interp(interp(u,b,t),interp(b,v,t),t))
    path.append(points[-1]); p.tube([(*q,z) for q in path],r,mat,12)
    for q in (path[0],path[-1]): p.rod((*q,z+.002),(*q,z+.068),r*.80,'Rust',8)


def noodle_neon(p):
    # A shallow folded red enamel tray on two stand-offs, not a printed lightbox.
    w,h=.846,.403; z=-.064
    p.box((0,0,.006),(w,h,.033),'SignRed',.009)
    frame(p,(0,0,.025),w,h,.012,.054,'Ruby')
    for x in (-.31,.31):
        p.box((x,0,.080),(.045,.186,.11),'Iron',.006)
        for y in (-.145,.145): p.disc((x,y,-.014),.008,.007,'Zinc',sides=8)
    # Separate tube runs meet at the corners; the red surface between them only reflects light.
    for s in (-1,1):
        glass(p,[(-.397,s*.183),(.397,s*.183)],z,.009,'Noodle',.01)
        glass(p,[(s*.401,-.181),(s*.401,.181)],z,.009,'Noodle',.01)
    for pts in [
        [(-.248,.085),(-.316,0),(-.255,-.085)], [(-.253,-.003),(-.224,-.003)],
        [(-.197,-.086),(-.154,.047),(-.093,.047)], [(-.164,-.007),(-.113,-.007)], [(-.151,.095),(-.085,.095)],
        [(-.048,.069),(-.014,.069),(-.073,-.09)],
        [(.038,-.09),(.038,.074)], [(.042,.042),(.097,.042)], [(.101,-.044),(.101,-.012)],
        [(.190,-.047),(.252,.074),(.268,.074),(.320,-.047),(.199,-.047)], [(.189,-.100),(.323,-.100)],
    ]: glass(p,pts,z-.006,.019,'Noodle',.014)
    # Cable returns to a junction box on the wall, behind the sign, not across its face.
    p.box((.32,-.08,.094),(.12,.104,.05),'Iron',.009)
    p.tube([(-.30,-.195,.022),(-.29,-.26,.045),(-.20,-.35,.085),(-.09,-.373,.103),(.02,-.353,.109),(.15,-.274,.109),(.30,-.11,.10)],.007,'Rubber',8)


def arrow_neon(p):
    z=-.135; front=-.091; back=-.014; half=.143
    def section(angle):
        return (-.009-.55*(1-math.cos(angle)),.210-.55*math.sin(angle)), (math.cos(angle),-math.sin(angle))
    stem=[((-.009,1.447),(1,0))]+[section(j/20) for j in range(21)]
    end,normal=stem[-1]; neck=add(end,(-.049,-.031)); stem.append((neck,normal))
    left=[sub(q,mul(n,half)) for q,n in stem]; right=[add(q,mul(n,half)) for q,n in stem]
    head=[sub(neck,mul(normal,.452)),(-.694,-.598),add(neck,mul(normal,.452))]
    # Closed channel. Its cross sections follow the same bend as the separate glass bars.
    for loop in [[a,b,c,d] for a,b,c,d in zip(left,left[1:],right[1:],right)]+[head]:
        p.face([(*q,front) for q in loop],(0,0,-1),'SignChannel'); p.face([(*q,back) for q in loop],(0,0,1),'Iron')
    outline=left+head+right[::-1]+[left[0]]
    for a,b in zip(outline,outline[1:]):
        p.face([(*a,front),(*b,front),(*b,back),(*a,back)],(b[1]-a[1],a[0]-b[0],0),'Ruby')
    for y in (.13,.87,1.37):
        p.box((.032,y,.225),(.13,.05,.51),'Rust',.006)
    p.box((.032,1.035,.263),(.09,.76,.044),'Iron',.005)
    for q,n in [((-.009,1.401-i*.066),(1,.04)) for i in range(19)]+[section(i/7) for i in range(1,8)]:
        glass(p,[add(q,mul(n,.10)),sub(q,mul(n,.10))],z,.0073,'ArrowAmber',.012)
    for pts in [[(-.515,.014),(-.652,-.56),(-.085,-.647)], [(-.452,-.072),(-.557,-.486),(-.167,-.556)],
                [(-.396,-.136),(-.462,-.405),(-.236,-.458)], [(-.327,-.207),(-.360,-.338),(-.264,-.361)]]:
        glass(p,pts[::-1],z,.0076,'ArrowAmber',.024)
    # Narrow neighbouring blade: open strokes and dark returns, not a column of dashes.
    p.box((.317,.744,-.052),(.278,1.52,.083),'SignChannel',.009)
    for pts in [[(.428,1.45),(.428,1.212)],[(.205,1.205),(.209,1.32),(.233,1.340),(.391,1.340)],
                [(.199,1.077),(.221,1.127),(.368,1.127),(.414,1.104),(.426,1.00),(.400,.926),(.315,.922)],
                [(.293,.98),(.301,1.069)],[(.198,.801),(.206,.845),(.421,.845),(.421,.721)],
                [(.206,.657),(.417,.657)],[(.420,.588),(.210,.588),(.205,.377),(.428,.377)],[(.278,.485),(.416,.485)],
                [(.202,.279),(.423,.279)],[(.210,.083),(.211,.185),(.429,.185)]]:
        glass(p,pts,z,.0071,'ArrowAmber',.024)


def paper_lightbox(p):
    # One square lantern: every face wraps around the same lamp and meets at a folded corner.
    r=.152; bottom,top=.277,.950
    for x in (-r,r):
        for z in (-r,r):
            p.box((x,top/2,z),(.015,top,.015),'Ruby',.002)
            p.box((x,.012,z),(.039,.024,.04),'Rubber',.004)
    for y in (bottom,top): p.box((0,y,0),(2*r+.018,.022,2*r+.018),'Ruby',.004)
    for y in (.083,.226):
        for s in (-1,1): p.box((0,y,s*r),(.30,.014,.013),'Rust')
    loop=[(-r,-r),(r,-r),(r,r),(-r,r),(-r,-r)]
    for i,((x,z),(xx,zz)) in enumerate(zip(loop,loop[1:])):
        u=i%2*.5
        p.face([(x,top,z),(xx,top,zz),(xx,bottom,zz),(x,bottom,z)],(zz-z,0,x-xx),'Rice',[(u,0),(u+.5,0),(u+.5,1),(u,1)])
    for y in (bottom+.037,top-.037): p.box((0,y,-.014),(.048,.055,.048),'IvoryEnamel',.006)
    p.rod((0,bottom+.059,-.014),(0,top-.059,-.014),.014,'PaperGlow',16)
