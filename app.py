"""SafeRoute AI: compact interactive Streamlit pathfinding lab."""
import random
import time
import streamlit as st
import plotly.graph_objects as go
from algorithms import METHODS, search
from graph import cells, edges, name, edge_name

st.set_page_config(page_title='SafeRoute AI · Mission Control', page_icon='🧭', layout='wide')
st.markdown('''<style>
.stApp{background:linear-gradient(145deg,#080e1d,#111b31 60%,#0a1222);color:#e6efff}
.block-container{padding-top:1.4rem;max-width:1550px}
h1,h2,h3{color:#e8faff!important}
[data-testid="stMetric"]{background:#17243b;border:1px solid #304765;padding:15px;border-radius:15px}
[data-testid="stSidebar"]{background:#0c172a}
div.stButton>button{border-radius:11px;border:1px solid #347f9b}
</style>''', unsafe_allow_html=True)

st.title('🧭 SafeRoute AI  /  Mission Control')
st.caption('INTERACTIVE EVACUATION LAB  ·  FIVE HAND-CODED SEARCH ALGORITHMS  ·  LIVE EMERGENCY REROUTING')

with st.sidebar:
    mode = st.radio('🗺️ Map mode', ['Interactive Grid', 'Real Map · India'], horizontal=False)
if mode == 'Real Map · India':
    from realmap import run
    run()
    st.stop()

with st.sidebar:
    st.header('⚙️ Mission setup')
    size = st.slider('Grid dimensions',5,12,8)
    points = cells(size,size)
    labels = {name(p):p for p in points}
    names = list(labels)
    start_name = st.selectbox('🚩 Starting point',names,index=0)
    goal_name = st.selectbox('🏁 Evacuation destination',names,index=len(names)-1)
    start,goal = labels[start_name],labels[goal_name]
    algorithm = st.selectbox('🧠 Active algorithm',METHODS)
    safety = st.slider('🛡️ Safety priority',0,100,75,5,help='0 = shortest distance; 100 = full hazard avoidance') / 100
    st.divider()
    st.subheader('🚨 Emergency simulator')
    density = st.slider('Random maze density (%)',0,45,22,1)
    if st.button('🎲 Generate random maze',use_container_width=True):
        candidates = [n for n in names if n not in (start_name,goal_name)]
        st.session_state.maze = random.sample(candidates,round(len(candidates)*density/100))
        st.session_state.blocked_picker = []
    if st.button('🧹 Reset emergency',use_container_width=True):
        st.session_state.maze = []
        st.session_state.blocked_picker = []
        st.session_state.road_picker = []
        st.session_state.fire_picker = []
        st.session_state.flood_picker = []
        st.session_state.crowd_picker = []
    valid = [n for n in names if n not in (start_name,goal_name)]
    manual = st.multiselect('⛔ Block multiple cells',valid,key='blocked_picker')
    maze = set(st.session_state.get('maze',[])) & set(valid)
    blocked = {labels[n] for n in set(manual)|maze}
    edge_lookup = {edge_name(e):e for e in edges(size,size)}
    closed_names = st.multiselect('🚧 Close individual roads',list(edge_lookup),key='road_picker')
    closed = [edge_lookup[n] for n in closed_names]
    available = [n for n in names if labels[n] not in blocked]
    fire = st.multiselect('🔥 Fire zones',available,key='fire_picker')
    flood = st.multiselect('🌊 Flood zones',available,key='flood_picker')
    crowd = st.multiselect('👥 Crowded zones',available,key='crowd_picker')
    hazards = {}
    for chosen,penalty in ((fire,12),(flood,8),(crowd,4)):
        for n in chosen:
            hazards[labels[n]] = hazards.get(labels[n],0) + penalty
    st.caption('Fire +12 · Flood +8 · Crowd +4. Overlapping hazards add up.')
    st.divider()
    st.subheader('🎞️ Playback')
    animate = st.toggle('Animate exploration',value=False)
    speed = st.slider('Frame delay (ms)',10,250,55,5,disabled=not animate)
    show_explored = st.checkbox('Highlight visited cells',value=True)
    show_scores = st.checkbox('Show heuristic values',value=False)

results = {m:search((size,size),start,goal,blocked,closed,hazards,m,safety) for m in METHODS}
path,explored,cost,elapsed,scores = results[algorithm]
base = search((size,size),start,goal,(),(),{},'A*',safety)[0]
rerouted = path != base
m1,m2,m3,m4,m5 = st.columns(5)
m1.metric('Algorithm',algorithm)
m2.metric('Route length',len(path)-1 if path else 'No route')
m3.metric('Safety cost',f'{cost:.1f}' if path else '—')
m4.metric('Nodes explored',len(explored))
m5.metric('Rerouting','ACTIVE' if rerouted else 'NORMAL')

closed_set = {frozenset(e) for e in closed}
def figure(revealed):
    seen = set(revealed) if show_explored else set()
    fig = go.Figure()
    for u,v in edges(size,size):
        if u in blocked or v in blocked:
            continue
        shut = frozenset((u,v)) in closed_set
        fig.add_trace(go.Scatter(x=[u[1],v[1]],y=[-u[0],-v[0]],mode='lines',
            line=dict(color='#f87171' if shut else '#354763',width=3 if shut else 2,dash='dash' if shut else 'solid'),hoverinfo='skip',showlegend=False))
    palette = []
    for p in points:
        palette.append('#26d9e8' if p==start else '#a78bfa' if p==goal else '#ef476f' if p in blocked else '#f5a623' if p in hazards else '#4e8cbe' if p in seen else '#23344f')
    txt = [name(p) for p in points]
    if show_scores:
        txt = [f'{name(p)}<br>h={abs(p[0]-goal[0])+abs(p[1]-goal[1])}<br>g={scores[p]:.0f}<br>f={scores[p]+abs(p[0]-goal[0])+abs(p[1]-goal[1]):.0f}' if p in scores else name(p) for p in points]
    fig.add_trace(go.Scatter(x=[p[1] for p in points],y=[-p[0] for p in points],mode='markers+text',
        text=txt,textposition='middle center',textfont=dict(color='white',size=9 if show_scores else 11),
        marker=dict(size=max(27,56-size) if not show_scores else max(40,68-size),color=palette,line=dict(color='#69819f',width=1)),
        customdata=[name(p) for p in points],hovertemplate='%{customdata}<extra></extra>',showlegend=False))
    # Reveal final route only after the goal has been explored.
    if path and (not animate or goal in seen or (not show_explored and len(revealed)==len(explored))):
        fig.add_trace(go.Scatter(x=[p[1] for p in path],y=[-p[0] for p in path],mode='lines+markers',
            line=dict(color='#42f5a1',width=6),marker=dict(color='#baffdc',size=9),hoverinfo='skip',showlegend=False))
    fig.update_layout(height=590,margin=dict(l=10,r=10,t=10,b=10),paper_bgcolor='#111c30',plot_bgcolor='#111c30',
        xaxis=dict(visible=False,range=[-.7,size-.3],scaleanchor='y'),yaxis=dict(visible=False,range=[-size+.3,.7]),dragmode='pan')
    return fig

left,right = st.columns([3,1],gap='large')
with left:
    st.subheader('🗺️ Live route map')
    map_slot = st.empty()
    if animate:
        for i in range(1,len(explored)+1):
            map_slot.plotly_chart(figure(explored[:i]),use_container_width=True,config={'displayModeBar':False},key=f'frame_{i}')
            time.sleep(speed/1000)
        if not explored:
            map_slot.plotly_chart(figure([]),use_container_width=True)
    else:
        map_slot.plotly_chart(figure(explored),use_container_width=True,config={'scrollZoom':True})
    st.caption('🩵 Start  ·  🟣 Exit  ·  🩷 Blocked  ·  🟠 Hazard  ·  🟢 Final route  ·  Red dashed = closed road')
with right:
    st.subheader('📡 Mission status')
    if path:
        st.success('Safe route available')
        st.write(' → '.join(map(name,path)))
    else:
        st.error('No route available — remove a blockage or road closure.')
    st.write(f'**Road closures:** {len(closed)}')
    st.write(f'**Blocked cells:** {len(blocked)}')
    st.write(f'**Hazardous cells:** {len(hazards)}')
    st.write(f'**Search runtime:** {elapsed:.4f} ms')
    st.info('Every sidebar change triggers a fresh search. A* uses f(n)=g(n)+h(n), with Manhattan h(n). The g values displayed are discovered costs, not always final optimal values for Greedy/BFS/DFS.')

st.subheader('📊 Live algorithm benchmark')
rows = [{'Algorithm':m,'Steps':len(p)-1 if p else None,'Safety cost':round(c,2) if p else None,
         'Visited':len(seen),'Time (ms)':round(ms,4),'Status':'Found' if p else 'No route'}
        for m,(p,seen,c,ms,_) in results.items()]
st.dataframe(rows,use_container_width=True,hide_index=True)
chart_a,chart_b = st.columns(2)
for col,metric,title,color in ((chart_a,'Visited','Explored nodes','#38bdf8'),(chart_b,'Safety cost','Weighted route cost','#34d399')):
    fig = go.Figure(go.Bar(x=[r['Algorithm'] for r in rows],y=[r[metric] for r in rows],marker_color=color))
    fig.update_layout(title=title,height=290,paper_bgcolor='#111c30',plot_bgcolor='#111c30',font_color='#d8e7fa',margin=dict(l=20,r=15,t=45,b=20))
    col.plotly_chart(fig,use_container_width=True)
st.caption('BFS minimizes hops; DFS does not guarantee optimality; Greedy uses only h; Dijkstra and A* minimize the weighted cost. Timings vary by machine and are illustrative on small grids.')
