import math
import numpy as np
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='OMCA PF350 ANFD Digital Twin', layout='wide')

# GA-controlled dimensions, mm
VESSEL_ID = 350.0
SHELL_GAP = 5.0
PLATE_GAP = 3.0
AXIAL_STROKE = 65.0

# Photo-extrapolated defaults. Keep editable until vendor drawings are available.
DEFAULTS = dict(shaft_d=42.0, hub_d=108.0, hub_h=72.0, arm_w=42.0,
                arm_t=14.0, scraper_len=92.0, scraper_w=58.0,
                scraper_h=62.0, sweep_d=340.0)

def rot_x(points, deg):
    a=np.deg2rad(deg); R=np.array([[1,0,0],[0,np.cos(a),-np.sin(a)],[0,np.sin(a),np.cos(a)]])
    return points @ R.T

def rot_z(points, deg):
    a=np.deg2rad(deg); R=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
    return points @ R.T

def mesh_box(center, size, color, name, angle=0, opacity=1.0):
    cx,cy,cz=center; lx,ly,lz=size
    p=np.array([[x,y,z] for x in (-lx/2,lx/2) for y in (-ly/2,ly/2) for z in (-lz/2,lz/2)],float)
    p=rot_z(p, angle); p += np.array([cx,cy,cz])
    I=[0,0,0,0,1,1,1,1,2,2,3,3]; J=[1,2,4,3,3,5,4,7,3,6,5,7]; K=[3,4,2,1,5,4,6,5,6,7,7,6]
    return go.Mesh3d(x=p[:,0],y=p[:,1],z=p[:,2],i=I,j=J,k=K,color=color,opacity=opacity,name=name,flatshading=False,hovertemplate=name+'<extra></extra>')

def cylinder(radius, z0, z1, color, name, opacity=1.0, n=80):
    th=np.linspace(0,2*np.pi,n,endpoint=False)
    x=np.r_[radius*np.cos(th),radius*np.cos(th)]
    y=np.r_[radius*np.sin(th),radius*np.sin(th)]
    z=np.r_[np.full(n,z0),np.full(n,z1)]
    i=[];j=[];k=[]
    for q in range(n):
        q2=(q+1)%n; i += [q,q2]; j += [q2,n+q2]; k += [n+q,n+q]
    return go.Mesh3d(x=x,y=y,z=z,i=i,j=j,k=k,color=color,opacity=opacity,name=name,hovertemplate=name+'<extra></extra>')

def ring_surface(r, z0, z1, color, opacity, name, n=100):
    th=np.linspace(0,2*np.pi,n)
    z=np.linspace(z0,z1,2)
    T,Z=np.meshgrid(th,z)
    return go.Surface(x=r*np.cos(T),y=r*np.sin(T),z=Z,showscale=False,opacity=opacity,
                      colorscale=[[0,color],[1,color]],name=name,hoverinfo='skip')

def liquid_disk(radius,z,color='#4aa8ff',opacity=.42,n=80):
    rr=np.linspace(0,radius,22); th=np.linspace(0,2*np.pi,n)
    R,T=np.meshgrid(rr,th)
    return go.Surface(x=R*np.cos(T),y=R*np.sin(T),z=np.full_like(R,z),showscale=False,
                      colorscale=[[0,color],[1,color]],opacity=opacity,name='Liquid surface',hoverinfo='skip')

def powder_surface(radius,z,bed_h,tilt_deg,n=70):
    rr=np.linspace(0,radius,24); th=np.linspace(0,2*np.pi,n); R,T=np.meshgrid(rr,th)
    slope=np.tan(np.deg2rad(min(abs(tilt_deg),28)))
    Z=z+bed_h+slope*R*np.cos(T)
    return go.Surface(x=R*np.cos(T),y=R*np.sin(T),z=Z,showscale=False,
                      colorscale=[[0,'#d8a317'],[1,'#f1c84b']],opacity=.92,name='Powder bed',hoverinfo='skip')

def build_agitator(p, angle, lift):
    traces=[]; z=PLATE_GAP+lift
    traces.append(cylinder(p['shaft_d']/2,z,z+290,'#9aa3aa','Agitator shaft'))
    traces.append(cylinder(p['hub_d']/2,z,z+p['hub_h'],'#aeb7bd','Central hub'))
    rtip=p['sweep_d']/2; rhub=p['hub_d']/2
    arm_len=max(1,rtip-rhub-p['scraper_w']*.45)
    for side in (-1,1):
        c=((rhub+arm_len/2)*side,0,z+p['arm_w']/2)
        traces.append(mesh_box(c,(arm_len,p['arm_t'],p['arm_w']),'#aeb7bd','Radial arm',angle=angle))
        rc=(rtip-p['scraper_w']/2)*side
        traces.append(mesh_box((rc,0,z+p['scraper_h']/2),(p['scraper_w'],p['scraper_len'],p['scraper_h']),
                               '#89949b','Outer mixing blade',angle=angle))
    # Rotate all agitator traces already axis-aligned by rotating coordinate arrays.
    for tr in traces:
        pts=np.c_[np.asarray(tr.x),np.asarray(tr.y),np.asarray(tr.z)]
        pts=rot_z(pts,angle)
        tr.x,tr.y,tr.z=pts[:,0],pts[:,1],pts[:,2]
    return traces

st.title('OMCA PF350 Re-volve Filter Dryer | Provisional 3D Digital Twin')
st.caption('GA-constrained outer geometry + photograph-extrapolated agitator. All values are in mm.')

with st.sidebar:
    st.header('Operating state')
    phase=st.selectbox('Phase',['Filtration / washing','Drying','Powder discharge','Maintenance'])
    phase_tilt={'Filtration / washing':0,'Drying':35,'Powder discharge':60,'Maintenance':0}[phase]
    tilt=st.slider('Vessel tilt (deg)',0,65,phase_tilt)
    angle=st.slider('Agitator angle (deg)',0,359,20)
    lift=st.slider('Agitator lift (mm)',0,int(AXIAL_STROKE),0)
    shell_opacity=st.slider('Shell opacity',0.05,0.80,0.18,0.05)
    section=st.checkbox('Section view',True)
    show_frame=st.checkbox('Show support frame',True)
    show_product=st.checkbox('Show powder / liquid',True)
    powder_kg=st.slider('Powder mass (kg)',0.0,5.0,1.8,0.1)
    bulk_density=st.slider('Bulk density (kg/L)',0.2,1.5,0.75,0.05)
    liquid_l=st.slider('Liquid volume (L)',0.0,25.0,5.0,0.5)
    st.divider(); st.header('Agitator calibration')
    p={}
    p['sweep_d']=st.slider('Blade sweep diameter',330.0,342.0,DEFAULTS['sweep_d'],1.0)
    p['shaft_d']=st.slider('Shaft diameter',30.0,55.0,DEFAULTS['shaft_d'],1.0)
    p['hub_d']=st.slider('Hub diameter',85.0,125.0,DEFAULTS['hub_d'],1.0)
    p['hub_h']=st.slider('Hub height',55.0,90.0,DEFAULTS['hub_h'],1.0)
    p['arm_w']=st.slider('Arm vertical depth',25.0,55.0,DEFAULTS['arm_w'],1.0)
    p['arm_t']=st.slider('Arm tangential thickness',8.0,22.0,DEFAULTS['arm_t'],1.0)
    p['scraper_len']=st.slider('Outer blade tangential length',70.0,115.0,DEFAULTS['scraper_len'],1.0)
    p['scraper_w']=st.slider('Outer blade radial width',42.0,75.0,DEFAULTS['scraper_w'],1.0)
    p['scraper_h']=st.slider('Outer blade height',45.0,85.0,DEFAULTS['scraper_h'],1.0)

radial_gap=(VESSEL_ID-p['sweep_d'])/2
if radial_gap < 4:
    st.warning(f'Radial blade clearance is only {radial_gap:.1f} mm. Keep ≥4 mm until verified.')

fig=go.Figure()
R=VESSEL_ID/2
# chamber height is provisional from photo/GA section, intentionally editable later
H=360
if section:
    th=np.linspace(np.deg2rad(25),np.deg2rad(335),120); z=np.linspace(0,H,2); T,Z=np.meshgrid(th,z)
    fig.add_trace(go.Surface(x=R*np.cos(T),y=R*np.sin(T),z=Z,showscale=False,opacity=shell_opacity,
                             colorscale=[[0,'#a7b0b6'],[1,'#e2e7ea']],name='Vessel shell',hoverinfo='skip'))
else:
    fig.add_trace(ring_surface(R,0,H,'#c9d0d4',shell_opacity,'Vessel shell'))
fig.add_trace(cylinder(R, -10, 0,'#7e8a91','Filter plate',.85))
fig.add_trace(ring_surface(R+12,0,H,'#79848a',.22,'Jacket'))
for tr in build_agitator(p,angle,lift): fig.add_trace(tr)

if show_product:
    area=math.pi*(R/1000)**2
    bed_h=0 if powder_kg==0 else (powder_kg/(bulk_density*1000))/area*1000
    bed_h=min(bed_h,120)
    if powder_kg>0: fig.add_trace(powder_surface(R-8,0,bed_h,tilt))
    if liquid_l>0:
        liq_h=min((liquid_l/1000)/area*1000,320)
        fig.add_trace(liquid_disk(R-7,liq_h))

if show_frame:
    for x in (-285,285):
        fig.add_trace(mesh_box((x,0,120),(45,70,570),'#4c5960','Support leg',angle=-8 if x<0 else 8))
    fig.add_trace(cylinder(42,H,H+130,'#6f7b82','Drive column'))
    fig.add_trace(mesh_box((0,0,H+180),(155,110,100),'#376b91','Drive gearbox'))

# Apply vessel tilt to process assembly, not support-frame/gearbox placeholders.
if tilt:
    assembly_count=4+len(build_agitator(p,angle,lift))+(2 if show_product and powder_kg>0 and liquid_l>0 else 1 if show_product and (powder_kg>0 or liquid_l>0) else 0)
    for tr in fig.data[:assembly_count]:
        x=np.asarray(tr.x); y=np.asarray(tr.y); z=np.asarray(tr.z)
        pts=np.c_[x.ravel(),y.ravel(),z.ravel()]; pts=rot_x(pts,tilt)
        tr.x=pts[:,0].reshape(x.shape); tr.y=pts[:,1].reshape(y.shape); tr.z=pts[:,2].reshape(z.shape)

fig.update_layout(height=760,margin=dict(l=0,r=0,t=20,b=0),showlegend=True,
    scene=dict(aspectmode='data',xaxis_title='X (mm)',yaxis_title='Y (mm)',zaxis_title='Z (mm)',
               camera=dict(eye=dict(x=1.45,y=1.55,z=1.15)),bgcolor='#f4f7f8'))
st.plotly_chart(fig,use_container_width=True,config={'displaylogo':False,'scrollZoom':True})

c1,c2,c3,c4=st.columns(4)
c1.metric('Vessel ID',f'{VESSEL_ID:.0f} mm','GA controlled')
c2.metric('Blade sweep',f"{p['sweep_d']:.0f} mm",'photo extrapolated')
c3.metric('Radial clearance',f'{radial_gap:.1f} mm','target ~5 mm')
c4.metric('Bottom gap',f'{PLATE_GAP:.0f} mm','GA controlled')

with st.expander('Dimension basis and confidence',expanded=True):
    st.markdown(f'''**Rechecked nominal geometry**

- Vessel internal diameter: **350 mm** (GA/reference image basis).
- Blade sweep: **{p['sweep_d']:.0f} mm**, giving **{radial_gap:.1f} mm radial clearance**.
- Filter-plate gap: **3 mm** and axial stroke: **65 mm** (GA-controlled constraints).
- Shaft diameter: **{p['shaft_d']:.0f} mm**, hub diameter: **{p['hub_d']:.0f} mm**, hub height: **{p['hub_h']:.0f} mm** (photo-extrapolated).
- Arm and outer-blade dimensions remain provisional because perspective, residue and hidden undersides prevent exact photogrammetry.

The earlier 12 mm arm thickness and 35–40 mm depth were too narrow as fixed values. The corrected defaults are **14 mm tangential thickness** and **42 mm vertical depth**, with sliders retained so later vendor dimensions can replace estimates without rewriting the model.''')
