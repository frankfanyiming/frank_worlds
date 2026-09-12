"""Reference-led Agasa household assemblies. Coordinates are Godot Y-up metres.

The building and spiral remain in build-agasa-reference.py. These assemblies
define a legible kitchen / paired bedroom / conversation area, with working
clearances; decorative pieces never add invisible collision boxes.
"""
import math, random
import reference_geometry as g
from reference_geometry import box, cyl, rod, line, ring, ell, mat, mesh
from math import sin, cos, pi, tau

def palette():
    return dict(white=mat('Agasa fitted ivory enamel','e8e5d6',.56),
        trim=mat('Agasa fitted warm aluminum','aeb8b5',.38,.42),
        walnut=mat('Agasa fitted walnut edges','87725b',.7),
        oak=mat('Agasa fitted honey oak','b69a70',.68),
        seam=mat('Agasa fitted recessed seams','657773',.8),
        blue=mat('Agasa fitted muted blue fabric','829aab',.93),
        linen=mat('Agasa fitted linen bedding','dfd9be',.93),
        pillow=mat('Agasa fitted cotton pillow','f0ecdf',.96),
        lavender=mat('Agasa fitted lavender sofa','9c97ac',.91),
        piping=mat('Agasa fitted upholstery piping','b8b1c4',.88),
        glass=mat('Agasa fitted coffee table Glass','b6ceca',.18,0,.45),
        water=mat('Agasa fitted basin shaded enamel','91aca6',.45),
        charcoal=mat('Agasa fitted charcoal equipment','435050',.55),
        paper=mat('Agasa fitted warm paper','e5dec7',.93),
        tea=mat('Agasa fitted amber tea','82704d',.32),
        burgundy=mat('Agasa fitted woven rug','b49187',.95),
        rugedge=mat('Agasa fitted rug edge','d1b9a0',.95),
        books=[mat('Agasa fitted book cover '+str(i),h,.88) for i,h in enumerate(['879892','a89b81','a58478','82919e','b2a48e','777d86'])])

def rounded_outline(x,y,z,w,d,r=.06):
    out=[]
    for cx,cz,a0 in [(x+w/2-r,z+d/2-r,0),(x-w/2+r,z+d/2-r,pi/2),(x-w/2+r,z-d/2+r,pi),(x+w/2-r,z-d/2+r,3*pi/2)]:
        for j in range(7):
            a=a0+j*pi/12;out.append((cx+r*cos(a),y,cz+r*sin(a)))
    return out

def cup(p,m,scale=1):
    x,y,z=p;s=scale
    ring('Hollow ceramic cup', (x,z), .066*s,.082*s,y,y+.13*s,m['white'],segments=24)
    cyl('Tea inside cup',(x,y+.096*s,z),.063*s,.008*s,m['tea'],24)
    cyl('Cup foot',(x,y+.012*s,z),.051*s,.026*s,m['white'],24)
    line('Cup curved handle',[(x+.074*s,y+.108*s,z),(x+.127*s,y+.112*s,z),(x+.151*s,y+.076*s,z),(x+.123*s,y+.033*s,z),(x+.075*s,y+.033*s,z)],.011*s,m['white'])
    cyl('Cup saucer',(x,y-.007*s,z),.115*s,.018*s,m['white'],28)

def book(p,size,m,cover=None,angle=0):
    x,y,z=p;w,h,d=size;cover=cover or random.choice(m['books'])
    box('Book paper block',(x,y,z),(max(.022,w-.012),h-.016,d-.020),m['paper'],.002,angle=angle)
    for yy in [y-h/2,y+h/2]:box('Book cloth cover',(x,yy,z),(w,.012,d),cover,.003,angle=angle)

def kitchen(m):
    g.GROUP='AgasaReference_Kitchen'
    c=(-1.15,.05);a0=math.radians(121);a1=math.radians(419)
    # The front opening is 62 degrees, more than 1.3 m clear at the inner lip.
    ring('Round fitted kitchen cabinet',c,1.27,1.91,.075,.94,m['white'],a0,a1,64,True)
    ring('Recessed kitchen toe kick',c,1.32,1.85,.075,.19,m['seam'],a0,a1,64)
    ring('Rounded counter lower reveal',c,1.245,1.955,.94,.985,m['trim'],a0,a1,64)
    ring('Thick ivory countertop',c,1.215,1.990,.985,1.055,m['white'],a0,a1,72)
    # Radial doors are individual fronts rather than marks painted on a cylinder.
    for j in range(22):
        aa=a0+(a1-a0)*(j+.04)/22;bb=a0+(a1-a0)*(j+.96)/22;mid=(aa+bb)/2
        ring('Individual curved cupboard front',c,1.909,1.933,.225,.879,m['white'],aa,bb,3)
        r=1.945
        line('Curved cupboard pull',[(c[0]+r*cos(mid+t),.78,c[1]+r*sin(mid+t))for t in [-.045,0,.045]],.012,m['trim'])
    # Central cooking cylinder and suspended hood match the room reference.
    cyl('Kitchen central appliance plinth',(c[0],.58,c[1]),.48,1.02,m['white'],48,True)
    cyl('Kitchen appliance top',(c[0],1.12,c[1]),.60,.075,m['trim'],48)
    cyl('Extractor rounded hood',(c[0],2.26,c[1]),.78,.32,m['white'],48)
    ring('Extractor metal lower lip',c,.51,.80,2.08,2.13,m['trim'],segments=48)
    cyl('Extractor chimney',(c[0],4.22,c[1]),.25,3.65,m['white'],36)
    for j in range(30):
        a=tau*j/30;rod('Extractor ventilation slot',(c[0]+.784*cos(a),2.185,c[1]+.784*sin(a)),(c[0]+.784*cos(a),2.27,c[1]+.784*sin(a)),.006,m['seam'])
    ring('Kitchen utensil rail',c,.613,.636,1.63,1.655,m['trim'],segments=48)
    for a in [0,.78,2.34,3.14,3.93,5.49]:
        x,z=c[0]+.65*cos(a),c[1]+.65*sin(a)
        rod('Utensil hanging stem',(x,1.64,z),(x,1.35,z),.012,m['charcoal'])
        pan=ell('Utensil rounded pan',(x,1.24,z),(.125,.13,.022),m['trim']);pan.rotation_euler.z=-a
        ell('Utensil recessed pan bowl',(x+.015*cos(a),1.24,z+.015*sin(a)),(.099,.101,.012),m['seam']).rotation_euler.z=-a
    # Stove and sink remain on opposite counter sides, their controls face the aisle.
    box('Inset two-burner cooker',(c[0]-.1,1.06,c[1]-1.62),(.89,.031,.45),m['charcoal'],.015)
    for x in [c[0]-.33,c[0]+.12]:
        ring('Burner concentric ring',(x,c[1]-1.63),.09,.116,1.079,1.09,m['trim'],segments=20)
        for aa in [0,pi/2]:
            rod('Burner pan support',(x-.14*cos(aa),1.10,c[1]-1.63-.14*sin(aa)),(x+.14*cos(aa),1.10,c[1]-1.63+.14*sin(aa)),.012,m['charcoal'])
    box('Recessed sink rim',(c[0]-1.65,1.065,c[1]-.03),(.46,.025,.74),m['trim'],.07)
    box('Sink visible inner basin',(c[0]-1.65,1.074,c[1]-.03),(.37,.015,.62),m['water'],.10)
    line('Kitchen gooseneck faucet',[(c[0]-1.88,1.08,c[1]-.03),(c[0]-1.88,1.42,c[1]-.03),(c[0]-1.73,1.51,c[1]-.03),(c[0]-1.61,1.45,c[1]-.03),(c[0]-1.61,1.37,c[1]-.03)],.018,m['trim'])
    rod('Faucet lever',(c[0]-1.88,1.13,c[1]+.13),(c[0]-1.88,1.28,c[1]+.13),.016,m['trim'])
    box('Wooden chopping board',(c[0]+1.50,1.083,c[1]-.45),(.46,.028,.28),m['oak'],.04)
    for xx in [-.12,.0,.12]:ell('Cut vegetables',(c[0]+1.50+xx,1.125,c[1]-.45),(.054,.024,.071),m['books'][0])
    for a in [math.radians(24),math.radians(47),math.radians(141),math.radians(165)]:
        x,z=c[0]+2.40*cos(a),c[1]+2.40*sin(a)
        cyl('Bar stool pedestal',(x,.39,z),.043,.57,m['trim'],20)
        cyl('Bar stool bell foot',(x,.115,z),.285,.065,m['trim'],28)
        ring('Bar stool footrest',(x,z),.191,.214,.30,.323,m['trim'],segments=28)
        cyl('Bar stool cushion',(x,.706,z),.305,.135,m['lavender'],32,True)
        ring('Bar stool cushion seam',(x,z),.308,.313,.729,.741,m['piping'],segments=32)
        # A low curved seat back, oriented away from the counter.
        ring('Bar stool low curved back',(x,z),.274,.318,.737,.956,m['lavender'],a-.99,a+.99,14)
    # Haibara's extra step is tucked beside the left counter, not in the entry gap.
    box('Small cooks step',(-3.45,.12,1.06),(.54,.22,.37),m['oak'],.025)
    for x in [-3.64,-3.26]:box('Small step side support',(x,.16,1.06),(.065,.27,.37),m['walnut'],.014)
    return c

def bedroom(m):
    g.GROUP='AgasaReference_Bedroom'
    # Two parallel beds now face the entry, heads together against the fitted shelf.
    for n,x in enumerate([-6.14,-4.64]):
        z=.10
        box('Paired bed joinery frame',(x,.29,z),(1.27,.24,2.30),m['walnut'],.035,True)
        for xx in [x-.54,x+.54]:
            for zz in [-.94,1.16]:box('Bed distinct corner leg',(xx,.18,zz),(.105,.36,.105),m['oak'],.018)
        box('Bed rounded mattress',(x,.507,z),(1.20,.24,2.22),m['pillow'],.083)
        line('Mattress sewn edge',rounded_outline(x,.54,z,1.20,2.22,.08),.007,m['linen'],closed=True)
        box('Bed folded duvet',(x,.66,.41),(1.215,.14,1.61),m['linen'] if n==0 else m['blue'],.066)
        line('Duvet tailored seam',rounded_outline(x,.709,.41,1.15,1.55,.06),.005,m['pillow'],closed=True)
        for dz in [-.15,.24,.64,.99]:
            line('Gentle duvet fold',[(x-.52,.742,dz),(x-.24,.745,dz+.012),(x+.05,.743,dz),(x+.45,.742,dz-.009)],.003,m['linen'] if n==0 else m['blue'])
        box('Bed plump sleeping pillow',(x,.718,-.73),(.87,.16,.39),m['pillow'],.075)
        box('Bed separate headboard',(x,.77,-1.09),(1.32,1.08,.10),m['oak'],.035)
        box('Bed headboard inset panel',(x,.84,-1.028),(1.11,.67,.018),m['white'],.025)
        box('Bed matching footboard',(x,.36,1.28),(1.32,.62,.09),m['oak'],.025)
        for xx in [x-.49,x+.49]:box('Footboard inset stile',(xx,.42,1.34),(.04,.36,.017),m['walnut'],.005)
    # Shared bedside unit and a book-lined head wall, as in the reference sheet.
    box('Shared bedside cabinet',(-5.39,.34,-1.00),(.27,.64,.49),m['oak'],.017)
    for yy in [.22,.45]:
        box('Bedside shallow drawer',(-5.39,yy,-.741),(.22,.18,.025),m['white'],.01)
        rod('Bedside drawer pull',(-5.46,yy,-.72),(-5.32,yy,-.72),.010,m['trim'])
    for x in [-6.22,-4.73]:
        box('Bedroom fitted cupboard back',(x,.59,-1.67),(1.44,1.05,.055),m['walnut'],.01)
        for xx in [x-.71,x+.71]:box('Bedroom cupboard upright',(xx,.59,-1.47),(.055,1.09,.44),m['oak'],.007)
        for yy in [.12,.59,1.14]:box('Bedroom fitted shelf',(x,yy,-1.47),(1.47,.055,.45),m['oak'],.008)
        for i in range(11):
            xx=x-.59+i*.111;h=.25+random.random()*.12
            box('Bedroom reference upright book',(xx,.62+h/2,-1.40),(.075,h,.27),random.choice(m['books']),.003)
            box('Book spine paper band',(xx,.69,-1.248),(.051,.05,.008),m['paper'],.001)
    # Television and stereo are recognisable objects with screens, controls and vents.
    x=-5.79;z=-1.49
    box('Bedroom CRT case',(x,1.51,z),(.77,.67,.52),m['white'],.061)
    box('Bedroom CRT bevel frame',(x,1.52,z+.279),(.67,.54,.044),m['charcoal'],.04)
    box('Bedroom convex CRT screen',(x-.035,1.55,z+.307),(.50,.37,.014),m['water'],.033)
    for yy in [1.38,1.49]:cyl('TV tuning knob',(x+.273,yy,z+.320),.032,.034,m['trim'],20).rotation_euler.x=pi/2
    for j in range(8):box('TV speaker grille',(x+.262,1.67+j*.017,z+.317),(.11,.006,.011),m['trim'],.001)
    for xx in [-6.49,-4.47]:
        box('Bookshelf stereo speaker',(xx,1.37,-1.46),(.30,.41,.29),m['walnut'],.013)
        for yy,r in [(1.29,.082),(1.47,.047)]:cyl('Speaker round driver',(xx,yy,-1.306),r,.017,m['charcoal'],24).rotation_euler.x=pi/2
    box('Bedroom stereo receiver',(-4.94,1.275,-1.43),(.63,.24,.32),m['trim'],.012)
    box('Stereo display',(-4.99,1.29,-1.259),(.30,.065,.012),m['charcoal'],.006)
    for xx in [-4.76,-4.70]:cyl('Stereo control', (xx,1.28,-1.242),.026,.017,m['white'],16).rotation_euler.x=pi/2
    # Rolling computer table at the bedside remains behind the bed foot line.
    box('Bedside rolling computer shelf',(-7.13,.76,.02),(.45,.063,.69),m['white'],.017)
    for z in [-.22,.26]:rod('Computer trolley frame',(-7.13,.12,z),(-7.13,.76,z),.018,m['trim'])
    box('Trolley portable computer',(-7.13,1.005,.02),(.36,.42,.32),m['white'],.025)
    box('Trolley monitor screen',(-6.937,1.02,.02),(.014,.30,.245),m['water'],.015)
    box('Trolley keyboard',(-6.985,.807,.05),(.25,.022,.38),m['trim'],.008)

def living(m):
    g.GROUP='AgasaReference_Living'
    box('Living defined woven carpet',(4.15,.077,.52),(3.94,.023,3.65),m['burgundy'],.035)
    line('Carpet inset woven border',rounded_outline(4.15,.094,.52,3.66,3.37,.04),.025,m['rugedge'],closed=True)
    for z,back in [(-.90,-1),(2.05,1)]:
        box('Conversation sofa frame',(4.15,.30,z),(2.89,.34,.91),m['walnut'],.056,True)
        for x in [2.93,5.36]:
            for zz in [z-.32,z+.32]:box('Sofa individual timber foot',(x,.13,zz),(.12,.21,.12),m['oak'],.018)
        box('Sofa upholstered curved back',(4.15,.87,z+back*.39),(2.93,.91,.25),m['lavender'],.11)
        for j in [-1,0,1]:
            x=4.15+j*.88
            box('Separate sofa seat cushion',(x,.576,z),(.855,.23,.75),m['lavender'],.081)
            line('Sofa seat welt seam',rounded_outline(x,.66,z,.822,.71,.07),.008,m['piping'],closed=True)
            o=box('Soft sofa back cushion',(x,.962,z+back*.26),(.85,.59,.20),m['lavender'],.078);o.rotation_euler.x=back*.06
            for xx in [x-.30,x+.30]:rod('Back cushion stitched edge',(xx,.757,z+back*.137),(xx,1.18,z+back*.137),.006,m['piping'])
        for x in [2.76,5.54]:
            box('Sofa padded armrest',(x,.687,z),(.24,.46,.91),m['lavender'],.08)
            line('Armrest upper welt',[(x-.09,.86,z-.36),(x,.883,z-.39),(x+.09,.86,z-.36),(x+.09,.86,z+.34)],.007,m['piping'])
    box('Coffee table framed top',(4.15,.56,.53),(1.68,.10,.85),m['oak'],.056,True)
    box('Coffee table inset',(4.15,.619,.53),(1.43,.012,.62),m['glass'],.028)
    box('Coffee table lower magazine shelf',(4.15,.235,.53),(1.39,.045,.65),m['walnut'],.022)
    for x in [3.48,4.82]:
        for z in [.24,.82]:box('Coffee table tapered leg',(x,.29,z),(.092,.50,.092),m['walnut'],.015)
    cup((3.72,.648,.62),m,.94);cup((4.48,.648,.37),m,.94)
    box('Coffee table wood serving tray',(4.16,.64,.61),(.42,.025,.29),m['walnut'],.025)
    for z in [.45,.78]:box('Serving tray raised rail',(4.16,.666,z),(.43,.041,.018),m['oak'],.007)
    for x in [4.00,4.16,4.32]:cyl('Biscuits on tray',(x,.670,.60),.050,.018,m['linen'],16)
    book((4.09,.278,.53),(.74,.035,.47),m,m['books'][3]);book((4.20,.315,.52),(.70,.035,.43),m,m['books'][1])
    box('Coffee table television remote',(4.63,.649,.72),(.18,.025,.07),m['charcoal'],.014)
    for i in range(4):ell('Remote control small button',(4.57+i*.039,.666,.72),(.010,.004,.012),m['white'])

def bookcases(m):
    g.GROUP='AgasaReference_Books'
    for i in range(30):
        a=tau*i/30
        if abs(math.atan2(sin(a-pi/2),cos(a-pi/2)))<.32 or abs(math.atan2(sin(a-3*pi/2),cos(a-3*pi/2)))<.40:continue
        x,z=7.52*cos(a),5.63*sin(a);t=(-sin(a),cos(a));inside=(-cos(a),-sin(a));rot=-a+pi/2
        def p(u,y,v):return (x+t[0]*u+inside[0]*v,y,z+t[1]*u+inside[1]*v)
        box('Open wall bookcase back',p(0,.59,-.15),(1.22,1.02,.035),m['walnut'],.008,angle=rot)
        for u in [-.59,.59]:box('Open wall bookcase stile',p(u,.58,0),(.047,1.06,.36),m['oak'],.007,angle=rot)
        for y in [.105,.535,1.10]:box('Open wall bookcase shelf',p(0,y,.01),(1.25,.045,.40),m['oak'],.008,angle=rot)
        for row in range(2):
            for j in range(12):
                h=.24+random.random()*.115;u=(j-5.5)*.090;low=.13 if row==0 else .562
                box('Book inside fitted shelf',p(u,low+h/2,.038),(.067,h,.27),random.choice(m['books']),.003,angle=rot)
                box('Book spine label',p(u,low+.074,.181),(.046,.041,.006),m['paper'],.001,angle=rot)
        if i%5==0:
            # Small orderly piles occupy only selected cabinet tops.
            for j in range(3):book(p(.12,1.147+j*.033,0),(.49,.025,.27),m,m['books'][j],rot)
