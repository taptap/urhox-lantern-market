"""Solid modelling tools in metres. Each Part is an independently movable UrhoX mesh.

Work in a shop's local frame: +X along the counter, +Y up, -Z out into the street.
Unless a face carries printed artwork its UVs are measured in metres, not camera space.
"""
import math
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET
from mdl import write_model

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'assets/NightMarket'
TAU = math.tau


def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def mul(a,s): return tuple(x*s for x in a)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def norm(a): return math.sqrt(dot(a,a))
def unit(a): return mul(a,1/(norm(a) or 1))
def cross(a,b): return a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]
def interp(a,b,t): return add(a,mul(sub(b,a),t))
def fmt(seq): return ' '.join(f'{x:.6g}' for x in seq)
def attr(node,key,val): ET.SubElement(node,'attribute',name=key,value=str(val))


class Part:
    def __init__(self, name, at, angle=0):
        self.name, self.at, self.angle = name, at, angle
        self.roll = 0
        self.vertices, self.indices = [], defaultdict(list)

    def face(self, p, outward, mat, uv=None, normals=None):
        n = unit(outward)
        if not uv:
            axis = max(range(3),key=lambda j:abs(n[j]))
            uv = [[(z,-y),(x,z),(x,-y)][axis] for x,y,z in p]
        # Outward normals and winding agree even for mirrored shop fronts.
        e1,e2 = sub(p[1],p[0]),sub(p[-1],p[0]); du,dv = sub(uv[1],uv[0]),sub(uv[-1],uv[0])
        det = du[0]*dv[1]-du[1]*dv[0]
        if abs(det)>1e-10:
            t = unit(mul(sub(mul(e1,dv[1]),mul(e2,du[1])),1/det))
            b = mul(sub(mul(e2,du[0]),mul(e1,dv[0])),1/det)
        else:
            t = unit(cross(n,(0,1,0) if abs(n[1])<.9 else (0,0,1))); b=cross(t,n)
        hand = 1 if dot(cross(t,n),b)>=0 else -1
        start = len(self.vertices)
        for i,(pos,st) in enumerate(zip(p,uv)):
            ns = normals[i] if normals else n
            ts = unit(sub(t,mul(ns,dot(ns,t)))) if normals else t
            self.vertices.append((*pos,*ns,*st,*ts,hand))
        fwd = dot(cross(e1,e2),n)>=0
        for i in range(1,len(p)-1):
            self.indices[mat].extend((start,start+i,start+i+1) if fwd else (start,start+i+1,start+i))

    def box(self, c, size, mat, bevel=0):
        h=mul(size,.5); bevel=min(bevel,min(h)*.85); inner=[a-bevel for a in h]
        def pt(signs,axes):
            return tuple(c[i]+k*(h[i] if i in axes else inner[i]) for i,k in enumerate(signs))
        signs=[(1 if s&1 else -1,1 if s&2 else -1,1 if s&4 else -1) for s in range(8)]
        for axis in range(3):
            for sign in [-1,1]:
                corners=[s for s in signs if s[axis]==sign]; corners[2],corners[3]=corners[3],corners[2]
                self.face([pt(s,(axis,)) for s in corners],tuple(sign if i==axis else 0 for i in range(3)),mat)
        if not bevel: return
        for a,b in [(0,1),(1,2),(2,0)]:
            for k in [-1,1]:
                for j in [-1,1]:
                    s,q=[s for s in signs if s[a]==k and s[b]==j]
                    self.face([pt(s,(a,)),pt(s,(b,)),pt(q,(b,)),pt(q,(a,))],tuple(k if i==a else j if i==b else 0 for i in range(3)),mat)
        for s in signs: self.face([pt(s,(a,)) for a in range(3)],s,mat)

    def tube(self, path, radius, mat, sides=8, caps=True):
        """Sweep circular sections along pipes, wire, stitching or bent handrails."""
        rings=[]; normals=[]; lengths=[0]; side=None
        for i,p in enumerate(path):
            axis=unit(sub(path[min(i+1,len(path)-1)],path[max(0,i-1)]))
            if side is None: side=unit(cross(axis,(0,1,0) if abs(axis[1])<.85 else (1,0,0)))
            side=unit(sub(side,mul(axis,dot(side,axis)))); up=cross(axis,side)
            ns=[add(mul(side,math.cos(j*TAU/sides)),mul(up,math.sin(j*TAU/sides))) for j in range(sides)]
            rings.append([add(p,mul(n,radius)) for n in ns]); normals.append(ns)
            if i: lengths.append(lengths[-1]+norm(sub(p,path[i-1])))
        for i in range(1,len(path)):
            for j in range(sides):
                k=(j+1)%sides; ij=[(i-1,j),(i-1,k),(i,k),(i,j)]; ns=[normals[a][b] for a,b in ij]
                uv=[(x*TAU*radius/sides,y) for x,y in [(j,lengths[i-1]),(j+1,lengths[i-1]),(j+1,lengths[i]),(j,lengths[i])]]
                self.face([rings[a][b] for a,b in ij],add(ns[0],ns[1]),mat,uv,ns)
        if caps:
            self.face(rings[0],sub(path[0],path[1]),mat)
            self.face(rings[-1],sub(path[-1],path[-2]),mat)

    def rod(self,a,b,r,mat,sides=10): self.tube([a,b],r,mat,sides)

    def lathe(self,c,profile,mat,sides=28,stretch=(1,1),label=False):
        """Turn a closed profile (height, radius) around Y. Physical or label UV."""
        rings=[]; normals=[]; length=profile[-1][0]-profile[0][0]
        for i,(y,r) in enumerate(profile):
            ya,ra=profile[max(0,i-1)]; yb,rb=profile[min(len(profile)-1,i+1)]
            ns=[]; ring=[]
            for j in range(sides):
                a=TAU*j/sides; x,z=math.sin(a),-math.cos(a)
                ns.append(unit(((yb-ya)*x/stretch[0],ra-rb,(yb-ya)*z/stretch[1])))
                ring.append(add(c,(r*x*stretch[0],y,r*z*stretch[1])))
            rings.append(ring); normals.append(ns)
        for i in range(1,len(rings)):
            for j in range(sides):
                k=(j+1)%sides; ij=[(i-1,j),(i-1,k),(i,k),(i,j)]
                a,b=(j/sides,(j+1)/sides) if label else (j/sides*TAU*profile[i][1],(j+1)/sides*TAU*profile[i][1]); v,w=profile[i-1][0],profile[i][0]
                if label: a+=.25; b+=.25; v=(v-profile[0][0])/length; w=(w-profile[0][0])/length
                ns=[normals[m][n] for m,n in ij]
                self.face([rings[m][n] for m,n in ij],add(ns[0],ns[1]),mat,[(a,1-v),(b,1-v),(b,1-w),(a,1-w)],ns)
        self.face(rings[0],(0,-1,0),mat); self.face(rings[-1],(0,1,0),mat)

    def disc(self,c,r,depth,mat,printmat=None,sides=48):
        """Circular metal housing, with a separate flush, undistorted printed face."""
        self.rod(add(c,(0,0,depth/2)),add(c,(0,0,-depth/2)),r,mat,sides)
        if printmat:
            circle=[(math.cos(TAU*i/sides),math.sin(TAU*i/sides)) for i in range(sides)]
            self.face([add(c,(r*.97*x,r*.97*y,-depth/2-.001)) for x,y in circle],(0,0,-1),printmat,[((1+x)/2,(1-y)/2) for x,y in circle])

    def print(self,c,w,h,mat):
        self.face([add(c,(x*w/2,y*h/2,0)) for x,y in [(-1,1),(1,1),(1,-1),(-1,-1)]],(0,0,-1),mat,[(0,0),(1,0),(1,1),(0,1)])

    def write(self,root):
        node=ET.SubElement(root,'node'); attr(node,'Name',self.name); attr(node,'Position',fmt(self.at))
        a=-math.radians(self.angle)/2; b=math.radians(self.roll)/2
        ca,sa,cb,sb=math.cos(a),math.sin(a),math.cos(b),math.sin(b)
        attr(node,'Rotation',fmt((ca*cb,sa*sb,sa*cb,ca*sb) if self.roll else (ca,0,sa,0)))
        idx=[]; groups=[]
        for ids in self.indices.values():
            groups.append((len(idx),len(ids),(0,0,0))); idx.extend(ids)
        write_model(OUT/'Meshes'/f'{self.name}.mdl',self.vertices,idx,groups)
        comp=ET.SubElement(node,'component',type='StaticModel'); attr(comp,'Model',f'Model;NightMarket/Meshes/{self.name}.mdl'); attr(comp,'Cast Shadows','true')
        attr(comp,'Material','Material;'+ ';'.join('NightMarket/Materials/'+name+'.xml' for name in self.indices))
