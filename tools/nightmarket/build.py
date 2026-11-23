"""Build the Lantern Market set in its own street coordinate system (metres).

Run `python3 tools/nightmarket/build.py`. Only the Python standard library is needed.
Regenerate the separate material stock with surfaces.py.
"""
import math
import random
from contextlib import contextmanager
from mesh import OUT, Part, ET, attr, add, sub, mul, unit, cross, fmt, TAU, interp
from fittings import frame, panel, canopy, door, dispensary_leaf, window, fan, plant, crate, barrel, lampion, fern
from fittings import noodle_neon, arrow_neon, paper_lightbox

root=ET.Element('node'); attr(root,'Name','Foundry lane'); rg=random.Random(771)
practicals=ET.SubElement(root,'node'); attr(practicals,'Name','Night practicals')
counts=[0,0,0]

@contextmanager
def part(name,at,angle=0):
    p=Part(name,at,angle); yield p; p.write(root)
    counts[0]+=1; counts[1]+=sum(map(len,p.indices.values()))//3


def light(name,at,color,power,radius,shadow=False,aim=None):
    n=ET.SubElement(practicals,'node'); attr(n,'Name',name); attr(n,'Position',' '.join(map(str,at)))
    l=ET.SubElement(n,'component',type='Light')
    for k,v in [('Light Type','Spot' if aim else 'Point'),('Color',color+' 1'),('Brightness Multiplier',power),('Range',radius),('Cast Shadows',str(shadow).lower())]: attr(l,k,v)
    if aim:
        x,y,z=unit(sub(aim[:3],at)); attr(n,'Rotation',fmt(unit((1+z,-y,x,0))))
        attr(l,'Spot FOV',aim[3]); attr(l,'Inner Cone Angle',aim[3]*.19)
    counts[2]+=1
    return l


def road():
    with part('Street and worn parking bays',(0,0,0)) as p:
        p.box((0,-.125,8),(21,.25,42),'Tarmac')
        # The loading bays are square to the cross street, not to the newer shop fronts.
        # Paint survives in broken islands, including in the middle of a stripe.
        paint=random.Random(81); a=math.radians(-31); ca,sa=math.cos(a),math.sin(a)
        def stripe(x,z,length,along):
            n=round(length/.059); half=.032
            for j in range(n):
                if paint.random()<.12: continue
                v=j*length/n; end=(j+1)*length/n-paint.uniform(0,.003)
                edge=[-half*paint.uniform(.48,1.13),half*paint.uniform(.50,1.10)]
                for side in (0,1):
                    if paint.random()<.17: continue
                    lo=edge[0] if side==0 else paint.uniform(-.002,.003)
                    hi=edge[1] if side==1 else paint.uniform(-.003,.002)
                    q=[]
                    for u,w in [(lo,v),(hi,v+.001),(hi*.86,end),(lo*.93,end-.001)]:
                        xx,zz=(x+u,z+w) if along else (x+w,z+u)
                        q.append((-.38+ca*xx+sa*zz,.0012,1.52-sa*xx+ca*zz))
                    p.face(q,(0,1,0),'Stripe')
        for x in (-1.22,0): stripe(x,-1.43,2.14,True)
        for z in (.69,1.24): stripe(-1.77,z,1.9,False)
        # Small scraps, not camera-facing sprites.
        for i in range(68):
            x=rg.uniform(-4.4,.2); z=rg.uniform(-2,15); sz=rg.uniform(.012,.045)
            p.face([(x,.003,z),(x+sz*.7,.004,z-sz*.24),(x+sz,.005,z+sz*.4),(x+sz*.33,.004,z+sz*.6)],(0,1,0),rg.choice(['Paper','Wood','Rubber']))
    for name,x,v0,v1,direction in [('West',-4.46,-6.5,15.4,-1),('East',-.12,2.96,15.2,1)]:
        with part(name+' sidewalk',(x,0,v0)) as p:
            L=v1-v0; inset=.13 if direction==1 else 0
            p.box((1.4*direction,.056,(L+inset)/2),(2.63,.112,L-inset),'Walk')
            def stone(a,b,normal):
                # A section of trapezoidal curb, with sloped face and a narrow joint.
                section=[(-.03,.005),(.028,.014),(.101,.115),(.22,.12),(.22,.005)]
                loops=[[add(q,(normal[0]*r,y,normal[1]*r)) for r,y in section] for q in (a,b)]
                for j,n in enumerate([(0,-1,0),(-normal[0],.65,-normal[1]),(0,1,0),(normal[0],0,normal[1]),(0,-1,0)]):
                    k=(j+1)%5; p.face([loops[0][j],loops[1][j],loops[1][k],loops[0][k]],n,'Curb')
                p.face(loops[0],sub(a,b),'Curb'); p.face(loops[1],sub(b,a),'Curb')
            n=round(L/.64)
            for i in range(n): stone((0,0,i*L/n+.005),(0,0,(i+1)*L/n-.005),(direction,0))
            if direction==1:
                for i in range(5): stone((i*.56+.01,0,-.02),(i*.56+.55,0,-.02),(0,1))
    with part('Storm drains',(-4.27,0,0)) as p:
        for z in [-.35,3.9,6.9,10.5]:
            p.box((0,.002,z),(.17,.008,.65),'Iron',.003)
            for i in range(13): p.box((0,.011,z+(i-6)*.045),(.14,.012,.019),'Patina')


def cut_shopfront(p,width,height,color,workshop):
    # A masonry opening in plan and elevation. +Z runs into the building.
    x,span,head,depth=(-.10,1.16,2.23,2.72) if workshop else (2.15,.99,2.12,.40)
    pier=.22 if workshop else depth
    facing='Oxide' if workshop else 'Tile'
    lining='Coalwash' if workshop else 'Plaster'
    p.box((0,(height+head)/2,1.55),(width,height-head,3.10),color,.018)
    p.box((0,(head+2.655)/2,-.021),(width-.02,2.655-head,.065),facing)
    for lo,hi in [(-width/2,x-span/2),(x+span/2,width/2)]:
        cx=(lo+hi)/2; w=hi-lo
        p.box((cx,head/2,pier/2),(w,head,pier),color)
        p.box((cx,(head+.105)/2,-.021),(w,head-.105,.065),facing)
        p.box((cx,.23,-.065),(w,.12,.16),'Soot',.012)
    p.box((0,head/2,(3.10+depth)/2),(width,head,3.10-depth),lining)
    p.box((x,.135,(pier-.10)/2),(span,.034,pier+.10),'Curb',.008)
    if not workshop:
        for s in (-1,1):
            p.box((x+s*(span/2-.011),head/2,(depth-.05)/2),(.022,head,depth+.05),'IvoryEnamel')
        dispensary_leaf(p,x,span,head)
        return

    # The entrance opens out into a room behind the two piers.
    for s in (-1,1):
        p.box((s*(width/2-.07),head/2,(pier+depth)/2),(.14,head,depth-pier),lining)
        p.box((x+s*(span/2+.025),head/2,-.048),(.062,head,.13),'Rust',.008)
    p.box((x,head+.016,-.057),(span+.12,.078,.15),'Rust',.009)
    p.box((0,head-.014,depth/2),(width-.25,.028,depth),lining)
    p.box((0,.071,(pier+depth)/2),(width-.26,.142,depth-pier),'Soot')
    p.box((0,.173,(.93+depth)/2),(width-.27,.065,depth-.93),lining,.012)
    # Worn wainscot outside; a pipe and a shelf are visible deeper inside on approach.
    p.box((.89,1.10,-.077),(.49,1.36,.079),'Oxide',.018)
    for y in (.42,1.78): p.box((.89,y,-.115),(.53,.052,.078),'Rust',.007)
    p.tube([(-.99,.22,depth-.12),(-.99,1.78,depth-.12),(-.91,1.86,depth-.12),(.62,1.86,depth-.12)],.027,'Iron')
    p.box((1.17,.86,1.73),(.35,.044,.85),'Wood',.008)


def sidewall(name,u,v,width,height,side,color):
    with part(name,(u,0,v),side) as p:
        open_front=name=='Tea rooms'
        cut_bay={'Herbalist block':1,'Machine shop':0}.get(name)
        if open_front:
            p.box((0,(height+2.58)/2,1.55),(width,height-2.58,3.1),color,.035)
            for x in [-width/2+.09,width/2-.09]: p.box((x,1.29,1.55),(.18,2.58,3.1),'Oxide')
            p.box((0,1.29,2.97),(width,2.58,.26),'MossTile')
            p.box((0,.075,1.41),(width,.15,2.92),'Walk')
            p.box((0,2.39,-.06),(width,.37,.21),'Shutter',.02)
            for i in range(5): p.box((0,2.24+i*.071,-.178),(width-.17,.023,.028),'Zinc')
            for x in [-1.71,1.37]: p.box((x,1.23,-.07),(.082,2.46,.21),'Rust',.01)
        elif cut_bay is not None:
            cut_shopfront(p,width,height,color,name=='Machine shop')
        else:
            p.box((0,height/2,1.55),(width,height,3.1),color,.035)
            p.box((0,1.38,-.021),(width-.02,2.55,.065),'MossTile' if side<0 else 'Tile')
        for y in [.23,3.42,6.82,9.82]:
            if y<height and (y>1 or (not open_front and cut_bay is None)):p.box((0,y,-.065),(width+.08,.12,.16),'Soot',.015)
        for x in [-width/2+.10,width/2-.105]: p.box((x,height*.5,-.09),(.20,height,.20),'Soot',.019)
        for j in range(max(1,int(width/2.3))):
            x=-width/2+(j+.5)*width/max(1,int(width/2.3))
            if not open_front and j!=cut_bay: door(p,(x,1.23,-.12),min(1.64,width*.65),2.18,j%2==0)
            for fl,y in enumerate([4.65,7.99,10.9]):
                if fl==0 and name=='Machine shop': y=4.93  # The sill sits on the landing.
                if y+.65<height: window(p,(x,y,-.10),1.27,1.56,(j+fl)%5==0,fl==0 and cut_bay is None)
        for i in range(2):
            x=width/2-.27-i*.13; r=.047 if i==0 else .024
            p.tube([(x,.15,-.26),(x,2.92,-.26),(x-.11,3.05,-.26),(x-.11,height-.27,-.26)],r,'Rust' if i==0 else 'Patina')
            for y in (.55,2.34,3.77,6.1): p.rod((x,y,-.26),(x,y+.035,-.26),r*1.24,'Zinc')


def architecture():
    for row in [('Herbalist block',-5.54,3.08,6.85,10.4,90,'Ochre'),('Machine shop',-5.58,8.0,2.95,10.8,90,'Oxide'),('Boiler house',-5.69,12.2,5.45,12.1,90,'Soot'),('West return',-5.62,-3.86,7.0,8.9,90,'Plaster'),('Tea rooms',1.14,6.9,7.04,10.8,-90,'Ochre'),('East tenements',1.23,12.7,4.60,12.5,-90,'Plaster')]: sidewall(*row)
    with part('Covered passage and tenement',(-2.19,0,14.6),17) as p:
        opening=3.20; H=2.55
        p.box((0,(H+13)/2,1.46),(10.4,13-H,3.0),'Soot',.03)
        for side in (-1,1):
            p.box((side*(opening/2+1.82),H/2,1.46),(3.64,H,3.0),'Oxide',.03)
            p.box((side*(opening/2+.09),1.32,-.10),(.20,2.64,.30),'Plaster',.02)
        for y in (2.57,4.51,6.43,9.0): p.box((0,y,-.13),(10.55,.16,.32),'Patina',.024)
        for x in (-3.55,-1.78,-.03,1.74,3.54):
            for row,y in enumerate((5.35,7.77,10.31)):
                window(p,(x,y,-.1),1.13,1.41,(row==1 and x in [-.03,1.74]) or (row==2 and x==-3.55),row!=0)
        for i,x in enumerate([-3.91,-2.38,-.91,.87,2.71]):
            p.rod((x,2.7,-.27),(x,12.1,-.27),.047 if i%2 else .085,'Patina',12)
            for y in (3.67,5.9,8.4): p.rod((x,y,-.27),(x,y+.072,-.27),.062 if i%2 else .104,'Zinc',12)
        for j in range(3): window(p,(-2.87+j*.66,3.73,-.20),.51,.75,False)
        # Apartment trim, different blinds, and rain leaders give the rear wall scale.
        for j,x in enumerate([-3.55,-1.78,-.03,1.74,3.54]):
            for y in (5.35,7.77):
                for dx in [-.64,.64]: p.box((x+dx,y,-.21),(.058,1.52,.089),'Plaster',.008)
            for k in range([9,4,14,2,7][j]): p.box((x,8.39-k*.079,-.251),(1.01,.037,.031),'Canvas',.003)
            p.tube([(x-.77,8.63,-.16),(x-.77,6.72,-.17),(x-.6,6.56,-.24),(x-.60,5.47,-.24)],.019,'Iron',8)
        for x in (-1.40,1.40):
            p.box((x,2.47,1.32),(.087,.14,2.7),'Iron')
            for z in (-.28,.72,1.68):
                p.box((x,2.38,z),(.10,.062,.75),'Patina',.013)
                p.rod((x,2.342,z-.31),(x,2.342,z+.31),.022,'CoralTube')
            for y in (.32,.84,1.58,2.07): p.box((x*1.125,y,.11),(.11,.098,.7),'Curb',.012)
        for z in (-.36,.52,1.48,2.55):
            p.box((0,2.51,z),(3.56,.22,.19),'Rust',.022)
            p.box((0,2.40,z-.068),(3.46,.032,.18),'Patina',.009)
        # A pair of steel service mains runs across the facade, turning back into the boiler house.
        for y,r,mat in [(4.61,.12,'Celadon'),(4.37,.053,'Patina')]:
            p.tube([(-4.55,y+.87,.03),(-4.55,y+.19,-.37),(-4.48,y+.06,-.41),(-4.33,y,-.42),(3.92,y,-.42),(4.08,y+.055,-.38),(4.14,y+.18,-.26),(4.14,y+.75,-.10)],r,mat,16)
            for x in (-3.91,-2.24,-.78,.87,2.73,3.82):
                p.rod((x-.021,y,-.42),(x+.021,y,-.42),r*1.21,'Zinc',16)
                p.box((x,y,-.21),(.05,.34,.34),'Rust',.012)
        p.box((0,2.425,-.59),(.55,.31,.094),'Iron',.025)
        # Blue enamel seven-segment wayfinding numerals: the hardware is still there with power off.
        for x,digit in [(-.106,7),(.086,8)]:
            seg=[(-.052,.084,.051,.084),(.054,.078,.054,.006),(.054,-.006,.054,-.079),(-.052,-.085,.051,-.085),(-.056,-.079,-.056,-.006),(-.056,.006,-.056,.078),(-.051,0,.051,0)]
            for k in ((0,1,2) if digit==7 else range(7)):
                x0,y0,x1,y1=seg[k]; p.rod((x+x0,2.425+y0,-.644),(x+x1,2.425+y1,-.644),.014,'VioletTube',6)
    with part('Far service court',(-1.9,0,21.2),10) as p:
        p.box((0,3.3,.48),(10,6.6,.95),'Oxide'); p.box((0,1.15,-.08),(5.4,2.3,.12),'MossTile')
        door(p,(1.74,1.19,-.16),1.7,2.3,True); window(p,(-1.25,2.55,-.18),1.45,.68,False)
        for i in range(14):plant(p,(-2.7+i*.35,.01,-.51-(i%4)*.12),rg.uniform(.48,1.82),100+i)
    with part('Court service canopy',(-1.9,2.88,21.0),10) as p:
        canopy(p,3.75,.91,'Teal',4)
        for x in (-1.24,.72): p.rod((x,-.12,-.35),(x+.42,-.12,-.35),.015,'MilkTube',10)
    # Distinct masses continue on the far sides and above the camera frustum.
    for j in range(3): sidewall('Court rear wing '+str(j),-5.1-j*.7,17.5+j*3.0,3.5,9+j,90,'Plaster')
    sidewall('Stationers across the entry',2.18,-1.26,9.14,8.1,-90,'Oxide')
    sidewall('Cross street at the entrance',-1.84,-8.43,10.38,7.4,180,'Plaster')


def shops():
    for name,u,y,v,a,w,d,mat,bulbs in [
        ('Herbalist zinc awning',-5.47,3.17,4.23,90,5.38,1.16,'Zinc',9),('Repair shop red canopy',-5.5,2.36,8.11,90,2.47,.95,'Ruby',0),
        ('Tea room ochre awning',1.08,2.84,6.15,-90,4.80,1.12,'Mustard',8)]:
        with part(name,(u,y,v),a) as p: canopy(p,w,d,mat,bulbs,.23,end_brackets=name=='Repair shop red canopy')
    for name,at,angle,w,h,art,case in [
        ('Tinned tea advertisement',(-5.18,3.76,3.74),90,3.75,1.07,'Billboard','Ruby'),
        ('Mint counter sign',(-5.32,2.40,5.06),90,.98,.54,'Pharmacy','Celadon'),
        ('Projecting mint sign',(-5.03,2.52,6.18),16,.43,.23,'Pharmacy','Patina'),
        ('Coffee blade',(-4.92,4.15,6.17),23,.57,1.87,'Menu','Rust'),
        ('Cinema CRT',(-2.03,3.67,14.01),16,1.36,1.68,'Cinema','Teal'),
        ('Foreground lightbox',(-4.46,3.39,2.96),6,.76,.51,'Pharmacy','Mustard'),
        ('Right hanging menu',(.53,3.58,4.95),4,.55,1.18,'Menu','Rust')]:
        with part(name,at,angle) as p:
            panel(p,(0,0,0),w,h,art,case,.16 if w<2 else .22)
            if name=='Coffee blade':
                # The blade hangs from a wall cantilever, independent of the balcony.
                p.box((-.675,1.13,0),(.10,.31,.14),'Rust',.008)
                p.box((-.218,1.045,0),(.934,.047,.061),'Iron',.006)
                p.rod((-.68,1.257,0),(-.16,1.063,0),.017,'Rust')
                for x in (-.20,.20): p.rod((x,h/2,0),(x,1.025,0),.014,'Iron')
            else:
                for x in [-w*.35,w*.35]: p.rod((x,h*.33,.06),(x,h*.56,.46),.024,'Iron')
    with part('Circular tea house marquee',(.43,2.05,3.36),22) as p:
        p.disc((0,0,0),.241,.11,'Ruby',sides=64); p.disc((0,0,-.057),.207,.009,'Mustard','Marquee',64)
        for j in range(8):
            a=TAU*(j+.5)/8; x,y=.224*math.cos(a),.224*math.sin(a)
            p.rod((x,y,-.055),(x,y,-.060),.005,'Patina',7)
        p.rod((.17,.10,.07),(.56,.23,.38),.021,'Iron')
        p.tube([(.21,-.085,.02),(.28,-.14,.02),(.29,-.20,.035),(.23,-.23,.045),(.20,-.20,.05)],.009,'Iron')
    with part('No parking post',(-4.13,.24,2.72),11) as p:
        p.rod((0,-.24,0),(0,1.93,0),.027,'Patina',14); p.disc((0,1.65,-.034),.222,.042,'Rust','Parking',54)
        for y in [.06,1.54,1.79]:p.rod((0,y,0),(0,y+.021,0),.034,'Zinc',12)
    with part('Red workshop facade',(-4.72,0,9.92),15) as p:
        # The right-hand corner meets the return at (-4.09, 10.09) in the lane plan.
        p.box((-.155,2.04,.47),(1.61,4.08,.94),'Oxide',.025); p.box((-.16,.14,-.10),(1.74,.26,.31),'Soot',.022)
        p.box((-.08,.96,-.042),(1.38,1.39,.083),'Rust',.023)
        for j in range(13): p.box((-.08,.32+j*.032,-.106),(1.22,.014,.017),'Iron',.003)
        for x,y,w,h in [(-.41,1.12,.46,.57),(.17,.92,.30,.42),(.44,1.37,.14,.22),(-.03,1.43,.20,.15),(.39,.84,.12,.16)]:
            p.print((x,y,-.089),w,h,'Notice')
        p.tube([(-.65,1.72,-.11),(-.58,1.31,-.16),(-.48,1.20,-.17),(-.34,1.18,-.17),(-.18,1.24,-.17),(.04,1.49,-.13),(.05,1.72,-.12)],.009,'Rubber',8)
        for x in [-.81,.60]: p.rod((x,.19,-.13),(x,4.25,-.13),.048,'Rust',12)
        p.tube([(.40,3.85,-.23),(.40,2.62,-.23),(.55,2.31,-.23),(.55,1.82,-.23)],.041,'Iron')
    with part('Noodle shop neon',(-5.00,1.905,9.70),15) as p:
        p.roll=-2.0  # The right mounting foot sits slightly lower on the wall.
        noodle_neon(p)
    with part('Bent arrow neon',(-4.53,3.17,9.57),18) as p: arrow_neon(p)
    with part('Paper lightbox',(-5.22,.12,6.965),74) as p:
        paper_lightbox(p)
        # Three short samples of the interior vertical burner. The paper transmits their light.
        for i,dy in enumerate((.443,.616,.789)):
            light(f'Paper burner {i+1}',add(p.at,(.0135,dy,-.004)),'1 .70 .25',.53,.405)
    with part('Outside fluorescent fittings',(-5.40,2.10,5.21),90) as p:
        p.rod((-.53,0,0),(.51,0,0),.019,'MilkTube',14)
        p.box((0,.035,.04),(1.18,.062,.13),'Patina',.018)
        for dx in (-.55,.53): p.box((dx,.014,.046),(.049,.062,.105),'IvoryEnamel',.009)
    with part('Turquoise barber pole',(.85,2.46,6.18),-90) as p:
        for y,r,h,m in [(-.35,.11,.11,'Patina'),(-.21,.09,.43,'AquaTube'),(.1,.112,.12,'Zinc'),(.21,.104,.12,'MilkTube')]:
            p.rod((0,y,0),(0,y+h,0),r,m,24)


def repair_return():
    # +X follows the wall from the noodle shop past the booth into the end building.
    corner=(-4.09,0,10.09); angle=96.5; a=math.radians(angle)
    def on_wall(x,y,z):
        return add(corner,(x*math.cos(a)-z*math.sin(a),y,x*math.sin(a)+z*math.cos(a)))

    with part('Boiler house return',corner,angle) as p:
        # The projecting front condenser rack ends against the first pier upstairs.
        p.box((2.34,6.88,.91),(3.67,8.34,1.82),'Plaster',.012)
        p.box((.253,3.39,.90),(.506,1.36,1.80),'Plaster',.008)
        for x in (.59,2.27,3.66): p.box((x,6.90,-.035),(.14,8.38,.088),'Soot',.009)
        for y in (4.31,6.43,8.68,10.87):
            p.box((2.31,y,-.037),(3.52,.14,.12),'Plaster',.009)
            p.box((2.31,y+.084,-.057),(3.56,.041,.15),'Patina',.004)
        for x,w in ((1.39,1.24),(2.96,1.03)):
            for y in (5.39,7.58,9.83):
                p.box((x,y,-.012),(w,1.58,.026),'Glass')
                frame(p,(x,y,-.043),w+.056,1.64,.055,.085,'Celadon')
                p.box((x,y,-.039),(.033,1.54,.044),'Patina')
                p.box((x,y+.24,-.045),(w,.033,.055),'Patina')
                p.box((x,y-.84,-.059),(w+.16,.068,.15),'Plaster',.006)
        # Top-hinged vent awnings stand proud of the upstairs sashes.
        for x,w in ((1.38,1.09),(2.96,.93)):
            for side in (-1,1):
                end=x+side*w/2
                p.tube([(end,8.44,.01),(end,8.30,-.105),(end,7.69,-.47)],.014,'Rust',8)
                p.rod((end+side*.07,7.63,-.06),(end,7.69,-.47),.012,'Iron',8)
            for j in range(9):
                t=j/9; y=8.28-.61*t; z=-.12-.36*t
                p.box((x,y,z),(w,.045,.044),'Celadon',.004)
        for x,r in ((3.62,.084),(3.40,.029)):
            p.rod((x,.18,-.116),(x,11.05,-.116),r,'Patina',14)
            for y in (.47,2.92,4.38,6.57,8.86):
                p.rod((x,y,-.116),(x,y+.065,-.116),r+.015,'Zinc',14)
        for x in (.96,2.29): fan(p,(x,3.22,-.213),.82)
        # Old tubular sign arms, socketed into the masonry above the condensing units.
        for x,y,reach in ((.21,3.67,1.26),(1.63,3.72,.91)):
            p.box((x,y,-.019),(.095,.18,.05),'Rust',.006)
            p.rod((x,y,-.037),(x,y,-reach),.021,'Rust',12)
            p.rod((x,y,-.047),(x,y,-.33),.032,'Patina',12)

    with part('Recessed lamp repair booth',corner,angle) as p:
        # Two solid piers, a recessed tiled back, a continuous lintel and a sill.
        for x,w in ((.50,1.0),(3.86,.64)): p.box((x,1.355,.84),(w,2.71,1.68),'Plaster',.013)
        p.box((2.27,1.355,1.03),(2.54,2.71,1.30),'Tile',.008)
        p.box((2.27,2.56,.19),(2.54,.30,.38),'Soot'); p.box((2.27,.085,.12),(2.62,.17,.58),'Curb',.01)
        door(p,(2.78,1.26,.328),.87,2.14,True)
        for x in (1.01,3.52): p.box((x,1.29,-.021),(.064,2.43,.066),'Patina',.006)
        for x,y,w,h,z in ((.43,1.46,.50,.78,-.008),(.78,1.07,.23,.39,-.009),(1.50,1.30,.65,.9,.37),(1.91,1.82,.26,.35,.37)):
            p.print((x,y,z),w,h,'Notice')
        crate(p,(1.75,.33,.08),.55,.32,.38,'Wood')

    with part('Passage canvas awning',corner,angle) as p:
        # Canvas falls away from the wall and sags between its three brackets.
        def roof(t,v):
            sag=.045*math.sin(2*math.pi*t)**2 + .044*math.sin(math.pi*v)
            return (.18+3.12*t,2.77-.40*v-.033*t-sag,-.018-1.14*v)
        for i in range(16):
            t,u=i/16,(i+1)/16
            for j in range(4):
                v,w=j/4,(j+1)/4; q=[roof(t,v),roof(u,v),roof(u,w),roof(t,w)]
                n=unit(cross(sub(q[1],q[0]),sub(q[3],q[0])))
                p.face(q,n,'Canvas'); p.face([add(k,(0,-.010,0)) for k in q],mul(n,-1),'Canvas')
            b,c=roof(t,1),roof(u,1); h=(0,-.139,0)
            p.face([b,c,add(c,h),add(b,h)],(0,0,-1),'Canvas')
            p.face([add(k,(0,0,.008)) for k in (b,c,add(c,h),add(b,h))],(0,0,1),'Canvas')
        for t in (0,.5,1):
            x=roof(t,0)[0]
            p.tube([add(roof(t,j/4),(0,-.022,0)) for j in range(5)],.014,'Iron',10)
            anchor=2.27 if t==0 else 2.45  # Middle and far stays bolt to the lintel, not the recessed door.
            p.box((x,(anchor+2.77)/2,-.004),(.061,2.84-anchor,.074),'Rust',.005)
            p.rod((x,anchor,-.039),add(roof(t,.84),(0,-.023,0)),.013,'Patina',10)
        p.rod((.18,2.75,-.02),(3.30,2.72,-.02),.036,'Iron',10)
        p.box((1.31,2.635,-.154),(2.15,.076,.31),'Celadon',.009)
        for x in (.29,2.33): p.box((x,2.599,-.19),(.066,.081,.21),'IvoryEnamel',.01)
        for z,glass in ((-.148,'AquaTube'),(-.242,'MilkTube')): p.rod((.30,2.582,z),(2.32,2.582,z),.018,glass,12)
        # A small enamel trade plate hangs from the wall end of the first rafter.
        p.box((.18,2.22,-.38),(.05,.20,.51),'Mustard',.019)
        p.face([(.153,2.287,-.17),(.153,2.287,-.59),(.153,2.153,-.59),(.153,2.153,-.17)],(-1,0,0),'District',[(0,0),(1,0),(1,1),(0,1)])
        for v in (.18,.45):
            x,y,z=roof(0,v); p.rod((x,2.318,z),(x,y-.02,z),.007,'Rust',8)
    light('Lamp repair fluorescent',on_wall(.85,2.55,-.23),'.51 .94 .84',2.4,2.65)
    light('Repair reflector spill',on_wall(1.94,2.54,-.24),'.53 .93 .82',2.2,3.1,aim=(*on_wall(2.0,1.25,.35),128))
    # Cool sky through the opening between the roofs; light the side of the wing, not the end facade.
    light('Boiler roof skylight',on_wall(.83,9.15,-1.75),'.43 .61 .84',108,6.9,aim=(*on_wall(1.30,6.23,0),100))

    with part('District hanging sign',on_wall(.62,5.43,-.324),angle-90) as p:
        panel(p,(0,0,0),.50,1.29,'Blade','Mustard',.105)
        p.face([(.211,.605,.054),(-.211,.605,.054),(-.211,-.605,.054),(.211,-.605,.054)],(0,0,1),'Blade',[(0,0),(1,0),(1,1),(0,1)])
        p.box((-.319,.65,0),(.045,.46,.12),'Iron',.005)
        p.rod((-.322,.729,0),(.224,.729,0),.024,'Rust',10)
        for x in (-.194,.193): p.rod((x,.644,0),(x,.73,0),.012,'Iron',8)
        p.rod((-.32,-.46,0),(-.242,-.46,0),.018,'Rust',8)


def utilities():
    banks=[(-5.25,2.55,5.90,90,.81,False),(-5.29,3.0,7.87,90,1.,False),(-5.33,3.04,8.78,90,.9,False),(-4.63,4.78,10.17,19,1.15,False),(-4.63,5.67,10.17,19,1.17,False),(-4.63,6.59,10.17,19,1.16,False),(-3.57,3.43,13.72,17,1.02,True),(-3.54,4.21,13.72,17,.99,True),(.91,4.02,8.4,-90,.9,False)]
    for i,(x,y,z,a,scale,dbl) in enumerate(banks):
        with part(f'Condenser {i+1:02d}',(x,y,z),a) as p: fan(p,(0,0,0),scale,dbl)
    with part('Industrial service risers',(.84,0,4.35),-90) as p:
        for j in range(3):
            x=(j-1)*.16; r=[.09,.04,.062][j]; p.tube([(x,.12,-.12),(x,2.73,-.12),(x+.1,2.87,-.12),(x+.1,4.73,-.12)],r,'Patina' if j!=1 else 'Rust',14)
            for y in [.32,1.87,2.52,3.9]:p.rod((x,y,-.12),(x,y+.047,-.12),r*1.18,'Zinc',12)
    with part('Overhead supply and comms', (0,0,0)) as p:
        for i in range(3):
            y=4.81+i*.142; a=(-5.55,y+.78,6.26+i*.32); b=(1.18,y-.39,6.30+i*.51)
            p.tube([add(interp(a,b,j/20),(0,-(.31+.08*i)*math.sin(math.pi*j/20),0)) for j in range(21)],.006 if i%2 else .010,'Rubber',7)
        for j in range(5):
            y=4.05+j*.086; p.tube([(-5.60,y,8.91),(-5.39,y,8.91),(-5.35,y,8.96),(-5.32,y,10.39),(-4.95,y+.24,10.8),(-4.93,y+.29,13.0),(-3.87,y+.30,13.77)],.020+j*.002,'Patina',8)
    with part('Festival lantern string',(0,0,0)) as p:
        # The wire leaves its wall anchor beneath the deck, then follows the original free span.
        def cable(t):return (-5.58+6.59*t,4.18-1.04*t-.43*math.sin(math.pi*t)-.28*max(0,1-t/.20),8.05-1.66*t)
        p.tube([cable(j/36) for j in range(37)],.012,'Rubber',8)
        for j in range(25):
            x,y,z=cable(.03+j*.039); r=.084+rg.uniform(-.009,.012)
            p.rod((x,y,z),(x,y-.09,z),.005,'Iron',6); lampion(p,(x,y-.09-r,z),r,2.12*r)


def streetlife():
    with part('Chesterfield settee',(-4.95,.118,3.84),77) as p:
        p.box((0,.205,.02),(1.71,.25,.67),'Leather',.075); p.box((0,.43,.28),(1.68,.46,.18),'Leather',.07)
        for x in [-.78,.78]:
            p.box((x,.36,-.005),(.19,.39,.70),'Leather',.08); p.rod((x,.52,-.30),(x,.52,.31),.098,'Leather',20)
            for z in [-.23,.24]:p.box((x,.085,z),(.073,.17,.073),'Wood',.01)
        for j in range(3):
            xx=(j-1)*.454; p.box((xx,.353,-.061),(.449,.135,.48),'Leather',.053)
            for y in [.42,.54]:p.rod((xx,y,.19),(xx,y,.175),.013,'Mustard')
        for xx in [-.64,-.46,-.28,-.10,.08,.26,.44,.62]:p.rod((xx,.201,-.324),(xx,.201,-.335),.008,'Mustard',6)
        # A resting robot assembled in a distinct, reclining pose.
        p.box((.15,.48,.02),(.40,.22,.30),'Velvet',.075); p.box((.46,.59,.012),(.23,.19,.19),'Teal',.038)
        panel(p,(.46,.60,-.085),.205,.154,'Cinema','Iron',.027)
        for j in [-1,1]:
            z=.059*j; knee=(-.145,.75+.087*j,z); ankle=(-.46-.075*j,.46,z-.10)
            p.rod((.005,.48,z),knee,.044,'Ruby',14); p.rod(knee,ankle,.037,'Ruby',14)
            p.rod(add(knee,(0,0,-.042)),add(knee,(0,0,.042)),.044,'Patina',14)
            p.box(add(ankle,(-.042,-.011,-.013)),(.148,.059,.07),'Rubber',.021)
            p.tube([(.31,.54,z*1.6),(.23,.46,z*2.5),(.05,.49,z*2.53)],.026,'Patina',9)
    with part('Herbalist plant rack',(-5.3,.12,3.86),90) as p:
        for y in [1.23,1.99]:
            p.box((-.1,y,-.05),(1.72,.048,.32),'Wood',.01)
            for j in [-.68,.59]: p.rod((j,y-.17,.08),(j,y-.03,-.17),.012,'Iron')
        for i,(x,y,h) in enumerate([(-.71,1.25,.37),(-.26,1.25,.51),(.33,1.25,.58),(-.51,2.02,.38),(-.17,2.02,.51),(.24,2.02,.42)]):plant(p,(x,y,-.06),h,35+i)
        for j,(x,y,r) in enumerate([(-.52,1.27,.23),(.29,1.26,.29),(-.14,2.06,.27),(.40,2.08,.23)]): fern(p,(x,y+.07,-.10),r,j+414)
        for x in [-.82,.61]:
            p.box((x,.69,.07),(.49,1.14,.30),'Rust',.02)
            for k in range(4):
                yy=.29+k*.26; p.box((x,yy,-.09),(.44,.224,.028),'Velvet',.009)
                p.box((x,yy+.035,-.113),(.099,.016,.041),'Iron',.005)
                if k%2==0:p.print((x-.10,yy-.016,-.106),.091,.047,'District')
    with part('Kegs and delivery crates',(-5.28,.119,6.05),90) as p:
        for i in range(5): crate(p,(-.73+(i%3)*.44,.165+(i//3)*.33,-.05*(i%2)),.43,.33,.38,['Wood','Mustard','Patina'][i%3])
    with part('Lacquer drums',(-3.8,.02,10.66),15) as p:
        for x,z in [(-.22,0),(.16,.03),(-.06,.37)]: barrel(p,(x,0,z),.174,.47,'Mustard')
        barrel(p,(-.19,.47,0),.167,.32,'Rust')
    with part('Bent tea house handrail',(.02,.117,3.27)) as p:
        foot=[(.04,0,2.12),(.06,0,.19),(.15,0,.06),(.29,0,0),(1.27,0,0)]
        for y in [.61,1.20]:p.tube([add(c,(0,y,0)) for c in foot],.042 if y>1 else .030,'Iron',14)
        for x,z in [(.04,2.12),(.06,.19),(1.27,0)]:
            p.tube([(x,0,z),(x,1.14,z),(x+.016,1.185,z),(x+.045,1.20,z)],.045,'Iron',14)
            p.rod((x,0,z),(x,.035,z),.081,'Patina',16)
        panel(p,(.82,1.10,-.021),.39,.19,'District','Mustard',.032)
    with part('Folding repair trestle',(-.29,.004,2.92),-52) as p:
        for j in [-1,0,1]:
            z=j*.076; y=.29+j*.021; x0=-.288+.023*(j%2); x1=.224+.019*j
            top=[(x0,y-.011,z-.035),(x1,y-.011,z-.035),(x1-.012,y+.008,z+.031),(x0+.019,y+.008,z+.035)]
            p.face(top,(0,1,-.27),'Wood'); p.face([add(v,(0,-.021,0)) for v in top],(0,-1,.27),'Wood')
            for i in range(4):
                a,b=top[i],top[(i+1)%4]; p.face([a,add(a,(0,-.021,0)),add(b,(0,-.021,0)),b],(b[2]-a[2],0,a[0]-b[0]),'Wood')
        for x in [-.14,.14]:
            for side in [-1,1]: p.rod((x,.011,side*.15),(x,.258,-side*.047),.023,'Patina',4)
            p.rod((x-.033,.20,0),(x+.034,.20,0),.028,'Rust',14)
            p.rod((x-.036,.20,0),(x+.038,.20,0),.009,'Zinc',8)
        p.box((0,.069,-.118),(.38,.052,.022),'Wood',.004)
    with part('Discarded drink tins',(-.78,.002,4.53),-12) as p:
        p.rod((-.16,.098,0),(.16,.098,0),.097,'Rust',24)
        for x in [-.15,.15]:p.rod((x-.008,.098,0),(x+.008,.098,0),.099,'Patina',24)
    with part('Glass bottle',(-3.58,.004,2.55),33) as p:
        for a,b,r in [(-.123,.027,.039),(.026,.061,.029),(.058,.118,.014)]:p.rod((a,.039,0),(b,.039,0),r,'Glass',16)
        p.rod((-.06,.039,0),(-.004,.039,0),.0395,'Ruby',16)
    with part('Electric delivery moped',(-.41,.12,11.2),-34) as p:
        for x in [-.47,.47]:p.disc((x,.224,0),.218,.09,'Rubber',sides=32); p.disc((x,.224,-.056),.117,.023,'Patina',sides=24)
        p.box((-.14,.44,0),(.64,.28,.27),'Teal',.078); p.box((-.17,.635,0),(.51,.105,.29),'Rubber',.048)
        p.tube([(.08,.39,0),(.38,.45,0),(.46,.88,0),(.38,.96,0)],.066,'Teal',12); p.rod((.38,.96,-.22),(.38,.96,.22),.022,'Patina')
        p.box((-.40,.74,0),(.34,.23,.30),'Mustard',.025)


def market_details():
    with part('Entrance sign mast',(-1.71,0,.935),12) as p:
        p.rod((0,.016,0),(0,3.54,0),.055,'Iron',20); p.box((0,.019,0),(.168,.038,.17),'Patina',.008)
        for y in [.19,1.61,2.81]:p.rod((0,y,0),(0,y+.032,0),.060,'Patina',18)
        panel(p,(-.233,1.45,.024),.38,1.48,'Blade','Teal',.105)
        p.rod((-.21,.93,-.042),(-.21,2.03,-.042),.009,'AquaTube',8)
        p.rod((-.018,3.44,0),(-2.1,3.44,.10),.039,'Iron',12)
        p.box((-.13,1.22,-.065),(.232,.94,.062),'Teal',.017)
        p.tube([(-.066,1.67,-.101),(-.087,1.51,-.101),(-.071,1.38,-.101),(-.038,1.27,-.101),(-.046,1.13,-.101),(-.095,.97,-.101)],.013,'AquaTube',8)
        p.rod((-.023,.81,-.101),(-.023,1.65,-.101),.006,'MilkTube',6)
    with part('Loading plates',(-4.46,0,5.98)) as p:
        for j in range(2):
            z=j*.55; a=[(.29,.012,z),(.29,.012,z+.543),(-.17,.136,z+.543),(-.17,.136,z)]
            p.face(a,(.27,1,0),'Patina'); p.face([a[0],a[1],add(a[1],(0,-.012,0)),add(a[0],(0,-.012,0))],(1,0,0),'Rust')
            for k in range(6):
                x=.22-k*.065; yy=.012+(.29-x)*.27; p.rod((x,yy,z+.027),(x,yy,z+.505),.004,'Zinc',5)
    with part('Tea room counter and crockery',(1.14,.15,6.90),-90) as p:
        p.box((-.14,.64,.62),(5.64,.115,.78),'Wood',.028)
        for j in range(8):
            xx=-2.60+j*.70; p.box((xx,.31,.65),(.57,.58,.60),'Teal' if j%3 else 'Rust',.012)
            p.box((xx,.34,.327),(.51,.47,.035),'Celadon',.009); p.box((xx+.16,.48,.299),(.044,.036,.039),'Patina',.006)
        for j,x in enumerate([-2.37,-2.16,-1.77,-.88,-.51,-.31,.71,.93,1.7,2.23]):
            for k in range(2+j%4):
                p.lathe((x,.701+k*.025,.57+.12*(j%2)),[(0,.056),(.011,.06),(.048,.089),(.064,.101),(.070,.098),(.052,.085),(.017,.046)],'Tile',18)
        for y in [.91,1.41,1.90]:
            p.box((.04,y,2.48),(6.5,.042,.49),'Wood',.01)
            for j in range(16):
                x=-2.86+j*.37+.046*(j%2); h=.115+.039*((j+round(y*5))%4); r=.053+.011*(j%3)
                p.lathe((x,y+.024,2.42),[(0,r*.80),(.018,r),(h*.72,r),(h*.83,r*.62),(h,r*.55)],['Pottery','Celadon','Glass','Rust'][j%4],14)
        for x in [-1.88,0.82]:p.rod((x,2.06,2.22),(x+.81,2.06,2.22),.014,'HoneyTube',10)
    with part('Service sacks',(.11,.117,9.39),17) as p:
        for i,(x,z,r) in enumerate([(-.13,-.10,.21),(.21,.06,.24),(-.05,.34,.23),(.42,.25,.15)]):
            p.lathe((x,0,z),[(0,.72*r),(.06,1.0*r),(.15,1.1*r),(.25,.90*r),(.37,.35*r),(.39,.18*r),(.43,.24*r)],'Rubber',14,(1,.83))
            p.rod((x,.381,z),(x,.392,z),.05,'Rust')
    # One landing on the machine-shop bay. Its near end returns to masonry beyond both signs.
    with part('Upper storefront catwalk',(-5.58,4.03,6.80),90) as p:
        p.box((1.02,0,-.30),(2.04,.12,.65),'Iron',.012)
        for x in (.14,1.88):
            p.box((x,-.24,-.012),(.082,.40,.043),'Rust',.005)
            p.rod((x,-.405,-.026),(x,-.061,-.56),.024,'Iron',10)
        # Four metal guard panels below an open handrail; all are lit surfaces.
        front=-.59; posts=[.04+i*.49 for i in range(5)]
        for x in posts: p.box((x,.566,front),(.037,1.02,.041),'Rust',.003)
        for i,(a,b) in enumerate(zip(posts,posts[1:])):
            x=(a+b)/2
            p.box((x,.428,front+.016),(b-a-.029,.647,.017),'IvoryEnamel',.003)
            p.rod((x,.27,front+.011),(x,.27,front-.067),.012,'Iron')
            p.rod((x,.232,front-.063),(x,.28,front-.063),.022,'Rust')
            p.lathe((x,.210,front-.063),[(-.035,.012),(-.025,.023),(.011,.024),(.029,.015)],'HoneyTube',12)
            light(f'Balcony bulb {i+1}',add(p.at,(.70,.205,x)),'1 .34 .075',.52,.84)
        for x in (posts[0],posts[-1]):
            p.box((x,.428,front/2),(.018,.647,-front-.035),'Patina',.003)
        for y,r in ((.10,.017),(.755,.020),(1.08,.025)):
            # A single bent rail, fixed into the wall at both ends; no overhang past the posts.
            a,b=posts[0],posts[-1]
            p.tube([(a,y,.015),(a,y,front+.038),(a+.014,y,front+.012),(a+.041,y,front),
                    (b-.041,y,front),(b-.014,y,front+.012),(b,y,front+.038),(b,y,.015)],r,'Iron',12)
    with part('Cinema grille and orange conduit',(-2.03,3.67,14.01),16) as p:
        for i in range(23):
            x=-.594+i*.054; p.rod((x,-.771,-.129),(x,.771,-.129),.0035,'Iron',5)
        for x in [-.61,.63]:p.tube([(x,-.78,-.13),(x,-.90,-.13),(x-.18,-1.08,-.09),(x-.34,-1.08,.02)],.011,'Rust',8)
    with part('Grimy delivery drums',(-5.22,.12,2.60),90) as p:
        for x,z,r,h in [(-.15,-.12,.17,.61),(.19,.03,.16,.48),(-.09,.17,.14,.37)]:
            barrel(p,(x,0,z),r,h,'Patina'); barrel(p,(x,h+.003,z),r*.96,.25,'Rust')
    with part('Boiler flue and service tower',(-4.70,4.02,10.49),19) as p:
        p.box((-.11,2.85,.57),(1.17,5.7,1.12),'Soot',.025)
        for y in [.39,1.31,2.22,3.13,4.04]: p.box((-.11,y,-.06),(1.19,.072,.15),'Rust',.012)
        for x in [-.61,.41]:p.rod((x,.045,-.16),(x,4.83,-.16),.040,'Patina',14)
        for k in range(14):p.rod((.12,.36+k*.31,-.145),(.40,.36+k*.31,-.145),.012,'Zinc',7)
    with part('Dispensary wirework',(-5.32,.12,3.85),90) as p:
        # Backing mesh for the plant shelves, cut to the frame at the edges.
        w,h,left=1.80,1.42,-.99; frame(p,(left+w/2,1.56,.089),w+.065,h+.065,.034,.047,'Rust')
        for slope in (-1,1):
            for k in range(-13,34):
                b=k*.106; x0=max(0,min(-b/slope,(h-b)/slope)); x1=min(w,max(-b/slope,(h-b)/slope))
                if x1>x0+.01: p.rod((x0+left,.85+b+slope*x0,.08),(x1+left,.85+b+slope*x1,.08),.0033,'Zinc',5)
        for j,x in enumerate([.59,.81,1.05]):
            p.box((x,2.37,.06),(.18,.26,.10),'Rust' if j==1 else 'Patina',.016)
            p.disc((x,2.395,-.012),.060,.036,'Iron',sides=16); p.disc((x,2.395,-.034),.049,.015,'Celadon',sides=16)
            drop=.74+j*.038
            p.tube([(x,2.25,.039),(x,2.13,.036),((x+drop)/2,2.09,.044),(drop,2.04,.044),(drop,.26,.044)],.011,'Patina',8)
    with part('Patched water main trench',(0,0,0)) as p:
        # Raised, irregular edges along an old utility cut. Not a reflection layer.
        for x,z,w,d in [(-2.51,.64,.41,.63),(-2.34,1.46,.47,.24),(-2.19,2.09,.42,.31),(-1.9,3.20,.38,.49),(-1.74,3.98,.39,.25),(-1.45,5.11,.32,.61)]:
            h=rg.uniform(.0025,.0045); perimeter=[]
            for k in range(18):
                a=TAU*k/18; ca,sa=math.cos(a),math.sin(a); s=rg.uniform(.91,1.04)
                dx=math.copysign(abs(ca)**.56,ca)*w*s; dz=math.copysign(abs(sa)**.56,sa)*d*s
                perimeter.append((x+dx+.19*dz,h*rg.uniform(.65,1),z+dz))
            for j,b in enumerate(perimeter):
                c=perimeter[(j+1)%len(perimeter)]; p.face([(x,h+.001,z),b,c],(0,1,0),'Sealcoat')
                p.face([b,c,(c[0],0,c[2]),(b[0],0,b[2])],(b[0]-x,.2,b[2]-z),'Tarmac')


def lighting():
    # Practical source positions are just outside their real housings.
    softbox=light('Herbalist softbox',(-5.04,2.33,4.98),'.72 1 .76',4.4,5.9,True)
    # At this range the offset is ~3 mm: keep the panel from shadowing itself.
    attr(softbox,'Normal Offset',.00025)
    for args in [
        ('Herbalist tube',(-5.12,1.77,5.45),'.62 1 .85',2.3,3.1),
        ('Light from the dispensary window',(-5.01,1.82,5.10),'.87 .85 .52',5.6,9.9,True,(-2.89,.03,1.79,86)),
        ('Tea advert',(-5.04,3.75,3.82),'1 .34 .07',4.2,3.8,False,(-4.35,3.30,3.77,118)),('Menu bulb',(-4.36,2.76,3.19),'1 .66 .28',2.7,3.4),
        ('Workshop neon',(-4.88,1.82,8.99),'1 .012 .004',6.5,5.5,True),('Workshop canopy spill',(-5.30,2.06,8.44),'1 .017 .007',6.3,4.1,False,(-4.77,.12,7.92,89)),
        ('Mast opal strip',(-1.91,1.14,.91),'.22 .35 .72',.57,3.1,False,(-.70,.19,2.04,107)),
        ('Noodle enamel bounce',(-5.11,1.92,9.48),'1 .016 .003',.80,1.3),
        ('Noodle sign spill',(-4.46,1.78,9.22),'1 .019 .008',16.8,14.2,True,(-2.33,.03,2.66,83)),
        ('Arrow transformers',(-4.45,3.77,9.06),'1 .12 .018',.90,2.5),
        ('Round tea sign',(.27,2.02,3.13),'1 .32 .065',1.25,2.4,False,(.03,1.45,2.76,137)),('Cyan barber pole',(.62,2.46,6.25),'.028 .64 .82',.76,2.36),
        ('Cinema spill',(-2.14,3.56,13.72),'.15 .44 .95',1.85,4.8),('Passage sodium',(-.81,2.16,14.42),'1 .24 .055',5.1,4.8),
        ('Court utility grille',(-1.90,2.43,17.88),'.38 .69 .70',4.0,4.6),('Tea bar shelf',(2.55,1.9,7.9),'1 .37 .09',1.62,3.1),
        ('Moonlit roof opening',(-3.32,8.12,11.15),'.40 .60 .85',18,11.7,False,(-2.65,5.34,14.43,111)),
        ('Upper landing sconce',(-.31,6.94,13.87),'1 .39 .13',1.65,3.8),
        ('Passage exit',(-2.19,2.31,19.45),'.63 .79 .41',4.8,4.2),('Roof clerestory',(-5.28,5.10,7.54),'1 .37 .075',2.2,3.0),
        ('Sign behind camera',(-2.9,2.24,-1.7),'.56 .17 .29',1.8,6),('Tea room interior',(.96,1.56,8.01),'1 .28 .09',2.36,4.4)]: light(*args)
    for i in range(4): light(f'Awning tungsten {i}',(.04,2.56,4.36+i*1.04),'1 .45 .13',.63,2.5)
    for i in range(4): light(f'Festival bulb {i}',(-4.53+i*1.3,3.72-i*.23,7.87-i*.36),'1 .14 .021',.34,1.7)


if __name__=='__main__':
    road(); architecture(); shops(); repair_return(); utilities(); streetlife(); market_details(); lighting()
    ET.indent(root); ET.ElementTree(root).write(OUT/'Market.xml',encoding='utf-8',xml_declaration=True)
    print('%d solid assemblies, %d triangles, %d practical lights'%tuple(counts))
