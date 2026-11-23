"""Generate tileable material samples from raw noise, mineral grains and wear.

No photography, environmental color, lightmaps or view-dependent inputs. R/G are
height derivatives, B is roughness, A is a wear or water-coverage mask.
"""
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import map_coordinates, gaussian_filter
from scipy.spatial import cKDTree
from xml.etree import ElementTree as ET
from mesh import OUT, fmt

TEX=OUT/'Stock'; MATS=OUT/'Materials'


def swatches():
    TEX.mkdir(parents=True,exist_ok=True)
    N=1024; rng=np.random.default_rng(431); y,x=np.mgrid[:N,:N]/N
    def noise(w,h=None):
        h=h or w
        return map_coordinates(rng.random((h,w),dtype=np.float32),[y*h,x*w],order=3,mode='grid-wrap').clip(0,1)
    def sig(a): return np.clip(a,0,1)
    cloud,blotch,grain,fine=noise(4),noise(19),noise(97),rng.random(x.shape,dtype=np.float32)
    dirt=.50*cloud+.29*blotch+.15*grain+.06*fine
    def image(name,base,height,rough,mask,bump):
        rgb=np.clip(base,0,255).astype('uint8'); Image.fromarray(rgb).save(TEX/(name+'.jpg'),quality=92,subsampling=0)
        sx=(np.roll(height,1,1)-np.roll(height,-1,1))*bump; sy=(np.roll(height,1,0)-np.roll(height,-1,0))*bump
        packed=np.stack((.5+.5*np.tanh(sx),.5+.5*np.tanh(sy),sig(rough),sig(mask)),axis=-1)
        Image.fromarray(np.rint(packed*255).astype('uint8')).save(TEX/(name+'-finish.png'))
    def rgb(lum,cast): return lum[:,:,None]*np.array(cast)[None,None,:]
    # Cracks split and meander through patched tarmac. Only rock, tar and old paint
    # change the diffuse map; water coverage lives in the finish map.
    seeds=(np.indices((7,7)).reshape(2,-1).T+.16+.68*rng.random((49,2)))/7
    p=np.stack(((x+.036*(noise(8)-.5)+.011*(noise(42)-.5))%1,(y+.036*(noise(8)-.5)+.011*(noise(42)-.5))%1),axis=-1)
    ds,ix=cKDTree(seeds,boxsize=1).query(p,k=2); seam=sig((ds[:,:,1]-ds[:,:,0])/.0034); apron=sig((ds[:,:,1]-ds[:,:,0])/.011)
    chip=sig((grain*.57+fine*.43-.66)*4); pits=sig((.30-grain*.5-fine*.5)*8)
    # Small exposed stones and eroded, branching hairline fractures break up
    # the broad repairs; avoid a regular cobblestone or smooth mirror finish.
    fines=noise(218); fissure=sig(1-abs(.6*grain+.4*blotch-.51)*59)*sig((cloud-.37)*4)
    grit=97+70*dirt+23*grain+30*fine+52*chip-28*pits+23*fines-43*fissure
    roadbed=(grit+rng.uniform(-21,19,49)[ix[:,:,0]])*(.43+.41*seam+.16*apron)
    # Water lingers in isolated hollows and open seams; the intervening aggregate is dry.
    wet=sig((.52*cloud+.27*blotch+.15*noise(43)+.06*grain+.047*(1-apron)-.47)*4.0)
    image('aggregate',rgb(roadbed,(1,.96,.90)),.67*seam+.28*apron+.30*grain+.15*fine+.23*chip+.09*fines-.34*fissure,.46+.35*dirt+.16*grain,wet,2.05)
    # Roughcast plaster, efflorescence, and runoff. The stains are pigments, not shadows.
    streak=noise(88,4)*.5+noise(220,8)*.2+dirt*.3; flakes=sig((dirt+.30*grain-.71)*8)
    plaster=225-64*streak-38*flakes+12*fine; image('plaster',rgb(plaster,(1,.98,.945)),.30*grain+.24*fine+.12*flakes,.73+.2*blotch,sig((streak-.4)*3),.72)
    # Staggered glazed brickwork, with dirty mortar, chipped corners and kiln variation.
    row=np.floor(y*16).astype(int); bx=x*8+.5*(row%2)+.014*(grain-.5); by=y*16+.028*(grain-.5)
    edge=np.minimum(np.minimum(bx%1,1-bx%1),np.minimum(by%1,1-by%1)*.55)
    brick=sig((edge-.011-.009*grain)*51); kilns=rng.random((16,8))[row%16,np.floor(bx).astype(int)%8]
    tile=(145+50*kilns+41*blotch+14*fine)*brick+(135+30*grain)*(1-brick)
    image('tile',rgb(tile,(1,.975,.925)),.8*brick+.14*grain+.07*fine,.33+.47*(1-brick)+.15*dirt,dirt,1.35)
    # Micro-scratches and chips on rolled-and-painted sheet metal.
    scratch=sig((noise(7,690)-.69)*4)*sig((noise(21)-.5)*6); rust=sig((.38*cloud+.25*blotch+.27*grain+.1*fine-.665)*9)
    metal=233-26*cloud-20*blotch-34*rust-17*scratch+8*fine
    image('enamel',rgb(metal,(1,.985,.955)),.32*rust+.1*scratch+.04*fine,.46+.31*dirt+.15*rust,rust,.95)
    grainwood=noise(12,210)*.46+noise(8,511)*.2+blotch*.34
    image('timber',rgb(157+82*grainwood+12*fine,(1,.89,.76)),.50*grainwood+.09*fine,.56+.27*dirt,dirt,.7)
    warp=np.minimum(np.cos(x*N*np.pi/3),np.sin(y*N*np.pi/3))*.5+.5
    image('weave',rgb(180+29*warp+22*blotch+10*fine,(1,.985,.97)),.12*warp+.12*grain,.72+.22*grain,dirt,.65)
    Image.new('RGB',(8,8),'white').save(TEX/'white.png')
    # A two-sided printer's seal on red lantern paper, unwrapped around the wire frame.
    paper=Image.new('RGB',(512,256),(190,47,29)); pen=ImageDraw.Draw(paper)
    for i in range(24):
        xx=round(i*512/24); pen.line((xx,18,xx,237),fill=(161,46,31),width=1)
    for yy in (21,26,229,234):pen.line((0,yy,512,yy),fill=(95,53,26),width=2)
    for cx in (128,384):
        pen.ellipse((cx-40,84,cx+40,172),outline=(73,37,24),width=5)
        for points in [[(-21,-18),(-9,-18),(-9,15),(-19,22)],[(-2,-23),(-2,0),(18,0),(18,18)],[(2,-16),(20,-16)],[(3,8),(3,25)]]:
            pen.line([(cx+a,128+b) for a,b in points],fill=(57,32,24),width=6)
    stock_dir=OUT/'Signs'; stock_dir.mkdir(parents=True,exist_ok=True); paper.save(stock_dir/'festival.png')


# Stock colors are unlit sRGB swatches; the shader receives their linear reflectance.
# Name: substrate, color, UV repeats/m, metal, roughness scale, chipped enamel, wetness.
stock={
    'Tarmac':('aggregate','796e63',.26,.02,1.,0,.98), 'Stripe':('aggregate','cabe91',.64,.02,1.,0,.48),
    'Sealcoat':('aggregate','756955',.40,.02,.98,0,.83),
    'Curb':('plaster','a89e89',.68,.02,.84,0,.27), 'Walk':('tile','827d72',.31,.03,1.,0,.42),
    'Plaster':('plaster','a18f7b',.43,0,1.,0,0), 'Soot':('plaster','736f70',.41,0,1.,0,0),
    'Coalwash':('plaster','403b39',.54,0,1.08,0,0),
    'Oxide':('plaster','976959',.50,0,1.,0,0), 'Ochre':('plaster','ae915e',.50,0,1.,0,0),
    'Tile':('tile','a49b85',.56,.06,.98,0,0), 'MossTile':('tile','667b72',.54,.05,.98,0,0),
    'Iron':('enamel','42484d',1.35,.63,.83,.8,0), 'Patina':('enamel','747e79',1.15,.55,.92,.80,0),
    'Zinc':('enamel','abb0a8',.97,.54,.78,.60,0), 'Rust':('enamel','89513c',1.45,.57,1.,.75,0),
    'Ruby':('enamel','882e31',.95,.34,.79,.89,0), 'Mustard':('enamel','bb9149',1.04,.29,.85,.90,0),
    'SignRed':('enamel','ad1514',1.22,.04,1.05,.12,0), 'SignChannel':('enamel','602f2e',1.18,.28,.98,.5,0),
    'Celadon':('enamel','909d8c',1.17,.32,.90,.72,0), 'Shutter':('enamel','7b8b88',.87,.49,.91,.85,0),
    'IvoryEnamel':('enamel','c7cbbe',1.22,.09,.99,.17,0),
    'Teal':('enamel','366967',1.12,.4,.75,.73,0), 'Rubber':('weave','34343a',1.7,.06,1.,0,0),
    'Glass':('enamel','394850',.55,.48,.24,0,0), 'Wood':('timber','a68157',.9,0,.91,0,0),
    'Leather':('weave','704137',2.6,.03,.89,0,0), 'Paper':('weave','c9b993',1.8,0,.94,0,0),
    'Foliage':('weave','56873c',2.3,.02,.85,0,0), 'LeafTip':('weave','8a9f49',2.3,.02,.87,0,0),
    'Pottery':('plaster','a96042',1.8,.08,.84,0,0), 'RedSilk':('weave','be3525',3.7,.02,.88,0,0),
    'Velvet':('weave','655445',2.4,.02,.91,0,0), 'Canvas':('weave','afa078',.9,.02,.97,0,0),
}
# Powered tubes/screens and non-luminous printing use the same stock when unpowered.
ink={
 'Billboard':('billboard','ffffff',1.65),'Pharmacy':('pharmacy','efffe7',3.1),
 'Marquee':('marquee','f2ffc2',1.65),'Cinema':('cinema','c3f3ff',1.85),'Menu':('menubox','ffffff',.21),
 'Blade':('street','ffffff',.2),'Parking':('parking','ffffff',0),
 'District':('district','ffffff',0),'Notice':('notices','ffffff',0),
 'CoralTube':(None,'ff5324',5.8),'HoneyTube':(None,'ffbc54',3.2),'MilkTube':(None,'e0ffe8',4.8),
 'AquaTube':(None,'5cfafa',2.9),'VioletTube':(None,'647dfb',2.8),'WindowAmber':(None,'dba15d',.22),
 'PaperGlow':(None,'ffae65',.85),'Lampion':('festival','ffffff',.27),
}
neon={'Noodle':('ffd277',5.6,0), 'ArrowAmber':('ff8834',1.56,1)}

def linear(hexcolor):
    v=np.array(list(bytes.fromhex(hexcolor)))/255
    return tuple(np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4))+(1,)

def write_materials():
    MATS.mkdir(parents=True,exist_ok=True)
    for name in [*stock,*ink,*neon,'Rice']:
        mat=ET.Element('material')
        if name in stock:
            shader='MarketSurface'
            sub,color,scale,metal,rough,wear,wet=stock[name]
            tex={'grain':f'Stock/{sub}.jpg','relief':f'Stock/{sub}-finish.png'}; params={'tint':fmt(linear(color)),'finish':fmt((scale,metal,rough,wet)),'damage':str(float(wear))}
        elif name in ink:
            shader='MarketLamp'
            pic,color,power=ink[name]; tex={'ink':f'Signs/{pic}.png' if pic else 'Stock/white.png'}; params={'stock':fmt(linear(color)),'output_gain':str(float(power)),'power':'1.0'}
        elif name in neon:
            shader='MarketNeon'; tex={}; color,gain,cathode=neon[name]
            params={'gas':fmt(linear(color)),'output_gain':str(gain),'cathode':str(float(cathode)),'power':'1.0'}
        else:
            shader='MarketPaper'; tex={'ink':'Signs/ricepaper.png','fibre':'Stock/weave.jpg'}; params={}
        ET.SubElement(mat,'surfaceshader',name='Shaders/BLGL/'+shader+'.shader')
        for k,v in tex.items(): ET.SubElement(mat,'surfacetexture',name=k,texture='NightMarket/'+v)
        for k,v in params.items(): ET.SubElement(mat,'parameter',name=k,value=v)
        ET.indent(mat); ET.ElementTree(mat).write(MATS/(name+'.xml'),encoding='utf-8')
        for usage,path in tex.items():
            config=ET.Element('texture'); ET.SubElement(config,'srgb',enable='false' if usage=='relief' else 'true')
            ET.SubElement(config,'filter',mode='anisotropic'); dst=(OUT/path).with_suffix('.xml'); dst.parent.mkdir(parents=True,exist_ok=True)
            ET.ElementTree(config).write(dst,encoding='utf-8')

if __name__=='__main__': swatches(); write_materials()
