"""Real-world OpenStreetMap mode; search algorithms live in road_search.py."""
import random
import streamlit as st
import folium
from streamlit_folium import st_folium
from road_search import METHODS, search

@st.cache_resource(show_spinner='Downloading OpenStreetMap roads…')
def load_roads(place, radius):
    import osmnx as ox
    center = ox.geocode(place + ', India')
    G = ox.graph_from_point(center, dist=radius, network_type='walk', simplify=True)
    return G, center

def run():
    import osmnx as ox
    st.subheader('🌍 Real Map · India')
    st.caption('Search a place, click two points, and run the five hand-written algorithms on OpenStreetMap roads. Requires internet for new areas.')
    a, b, c = st.columns([3,1,1])
    with a: place = st.text_input('Search a city / landmark in India', 'Hazratganj, Lucknow')
    with b: radius = st.selectbox('Area radius', [400, 600, 900, 1200], index=1, format_func=lambda v: f'{v} m')
    with c: algorithm = st.selectbox('Algorithm', METHODS, key='real_algorithm')
    safety = st.slider('Hazard avoidance priority',0,100,75,5,key='real_safety')/100
    try:
        G, center = load_roads(place.strip(), radius)
    except Exception as exc:
        st.error(f'Could not load map. Check internet / place name, or try a smaller area. Details: {exc}')
        return
    if G.number_of_nodes() > 3500:
        st.warning('This area is large; choose a smaller radius for responsive searches.')
    st.info('Click the map to set **START**, then click again to set **DESTINATION**. Use the buttons below to reset or swap.')
    if st.button('🔁 Reset start and destination'):
        st.session_state.real_clicks = []
        st.session_state.real_last_click = None
    if st.session_state.get('real_place_key') != (place, radius):
        st.session_state.real_place_key = (place, radius)
        st.session_state.real_clicks = []
        st.session_state.real_last_click = None
        st.session_state.real_closed = []
        st.session_state.real_hazards = {}
    clicks = st.session_state.get('real_clicks', [])
    start = ox.distance.nearest_nodes(G, clicks[0][1], clicks[0][0]) if clicks else None
    goal = ox.distance.nearest_nodes(G, clicks[1][1], clicks[1][0]) if len(clicks)>1 else None
    # Road closures are directed edges; closing both directions simulates a full road closure.
    edge_pairs = list({tuple(sorted((str(u),str(v)))) for u,v in G.edges()})
    # Work with actual node IDs, not the display representation.
    roads = list({frozenset((u,v)) for u,v in G.edges() if u != v})
    st.caption(f'{G.number_of_nodes()} intersections · {G.number_of_edges()} directed road segments')
    x,y = st.columns(2)
    with x:
        if st.button('🚧 Close 3 random roads'):
            st.session_state.real_closed = random.sample(roads, min(3,len(roads)))
        if st.button('🧹 Clear road closures'):
            st.session_state.real_closed = []
    with y:
        if st.button('🔥 Add 5 random hazardous roads'):
            chosen = random.sample(roads, min(5,len(roads)))
            st.session_state.real_hazards = {tuple(pair): 7 for pair in chosen}
        if st.button('🧼 Clear hazards'):
            st.session_state.real_hazards = {}
    # Editable multiple road selections with short stable labels.
    road_lookup = {f'{i+1}: {str(sorted(map(str,pair))[0])[:8]} ↔ {str(sorted(map(str,pair))[1])[:8]}':pair for i,pair in enumerate(roads)}
    selected = st.multiselect('⛔ Manually close multiple roads (intersection IDs)', list(road_lookup), max_selections=20)
    closures = set(st.session_state.get('real_closed',[])) | {road_lookup[s] for s in selected}
    closed = {(u,v) for pair in closures for u in pair for v in pair if u!=v}
    hazards = {}
    for pair, penalty in st.session_state.get('real_hazards',{}).items():
        u,v = pair
        hazards[(u,v)] = hazards[(v,u)] = penalty
    results = {m:search(G,start,goal,m,closed,hazards,safety) for m in METHODS} if start is not None and goal is not None else {}
    path, visited, cost, ms, scores = results.get(algorithm,([],[],0.,0.,{}))
    m = folium.Map(
    location=center,
    zoom_start=15,
    tiles="OpenStreetMap",
    control_scale=True
)
    for u,v,data in G.edges(data=True):
        p1,p2 = G.nodes[u],G.nodes[v]
        pair = frozenset((u,v))
        color = '#f87171' if pair in closures else '#f59e0b' if (u,v) in hazards else '#3e5873'
        folium.PolyLine([(p1['y'],p1['x']),(p2['y'],p2['x'])],color=color,weight=3 if pair in closures else 2,opacity=.8).add_to(m)
    if path:
        coords = [(G.nodes[n]['y'],G.nodes[n]['x']) for n in path]
        folium.PolyLine(coords,color='#39f7b1',weight=6,opacity=.95,tooltip=f'{algorithm} route').add_to(m)
    for node,color,title in ((start,'#22d3ee','START'),(goal,'#a78bfa','DESTINATION')):
        if node is not None:
            n = G.nodes[node]
            folium.CircleMarker([n['y'],n['x']],radius=9,color=color,fill=True,fill_opacity=1,tooltip=title).add_to(m)
    event = st_folium(m,height=560,width=None,key='real_map',returned_objects=['last_clicked'])
    clicked = event.get('last_clicked') if event else None
    pos = (clicked['lat'],clicked['lng']) if clicked else None
    if pos and pos != st.session_state.get('real_last_click'):
        st.session_state.real_last_click = pos
        st.session_state.real_clicks = (clicks+[pos])[-2:] if len(clicks)<2 else [pos]
        st.rerun()
    if start is not None and goal is not None:
        cols = st.columns(4)
        cols[0].metric('Selected algorithm',algorithm)
        cols[1].metric('Weighted cost',f'{cost:.0f} m' if path else 'No route')
        cols[2].metric('Nodes explored',len(visited))
        cols[3].metric('Execution',f'{ms:.2f} ms')
        if not path:
            st.error('NO REACHABLE ROUTE. Try removing road closures or changing endpoints.')
        st.subheader('📊 All-algorithm comparison')
        st.dataframe([{'Algorithm':name,'Route nodes':len(r)-1 if r else None,'Weighted cost (m)':round(c,1) if r else None,'Visited':len(v),'Runtime (ms)':round(t,3)} for name,(r,v,c,t,_) in results.items()],hide_index=True,use_container_width=True)
        st.caption('Road hazards are simulated, not live. Straight road segments are displayed between graph intersections; routes follow the OSM walking network.')
    else:
        st.warning('Click two map locations to calculate routes.')
