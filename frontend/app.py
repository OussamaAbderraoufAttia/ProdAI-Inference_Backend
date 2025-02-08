import streamlit as st
import networkx as nx
from pyvis.network import Network
import json
import requests

def create_reasoning_graph(reasoning_data):
    """Create graph from reasoning chain data"""
    steps = reasoning_data.get("steps", [])
    
    if not steps:
        st.error("No reasoning steps available.")
        return None

    G = nx.DiGraph()
    
    for step in steps:
        obs_id = f"Obs_{step['step_id']}"
        G.add_node(obs_id, 
                   title=step['observation'],
                   label="Observation",
                   color='#90CAF9',  # Light blue
                   size=25)
        
        thought_id = f"Think_{step['step_id']}"
        G.add_node(thought_id, 
                   title=step['thought'],
                   label="Thought",
                   color='#A5D6A7',  # Light green
                   size=25)
        
        G.add_edge(obs_id, thought_id, 
                   color='#90A4AE',  # Gray
                   arrows='to')
        
        if step.get('action'):
            action_id = f"Act_{step['step_id']}"
            G.add_node(action_id, 
                       title=step['action'],
                       label="Action",
                       color='#FFCC80',  # Light orange
                       size=25)
            G.add_edge(thought_id, action_id, 
                       color='#90A4AE',
                       arrows='to')
            
            if step.get('result'):
                result_id = f"Result_{step['step_id']}"
                G.add_node(result_id, 
                           title=step['result'],
                           label="Result",
                           color='#EF9A9A',  # Light red
                           size=25)
                G.add_edge(action_id, result_id, 
                           color='#90A4AE',
                           arrows='to')

    return G

def fetch_data_from_flask(message):
    """Fetch data from Flask backend"""
    url = "http://127.0.0.1:5000/chat"
    payload = json.dumps({"message": message})
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from backend: {str(e)}")
        return None

def create_network_visualization(G):
    """Create and configure network visualization"""
    net = Network(height="600px", width="100%", directed=True, bgcolor='#ffffff', font_color='#000000')
    
    for node, node_attrs in G.nodes(data=True):
        net.add_node(node,
                     title=node_attrs.get('title', ''),
                     label=node_attrs.get('label', ''),
                     color=node_attrs.get('color', '#97C2FC'),
                     size=node_attrs.get('size', 25))
    
    for edge in G.edges(data=True):
        net.add_edge(edge[0], edge[1],
                     color=edge[2].get('color', '#97C2FC'),
                     arrows=edge[2].get('arrows', 'to'))
    
    net.set_options("""
    var options = {
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -50,
                "centralGravity": 0.01,
                "springLength": 200,
                "springConstant": 0.08
            },
            "maxVelocity": 50,
            "solver": "forceAtlas2Based",
            "timestep": 0.35,
            "stabilization": {"iterations": 150}
        }
    }
    """)
    
    return net

# Streamlit UI Layout
st.set_page_config(layout="wide", page_title="ProdAI")

st.title("🧠 ProdAI")

# User Input Section
with st.container():
    user_query = st.text_area("Enter your query:", height=100)
    if st.button("Analyze"):
        if user_query.strip():
            with st.spinner("Analyzing..."):
                response_data = fetch_data_from_flask(user_query)
                
                if response_data and response_data.get("response"):
                    st.session_state.response_data = response_data["response"]
                    st.session_state.has_response = True
                else:
                    st.error("Failed to get response from backend.")
        else:
            st.warning("Please enter a query.")

# Display Results
if hasattr(st.session_state, 'has_response') and st.session_state.has_response:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📊 Reasoning Process")
        
        reasoning_data = st.session_state.response_data.get("reasoning_chain")
        if reasoning_data:
            G = create_reasoning_graph(reasoning_data)
            if G:
                net = create_network_visualization(G)
                
                net.save_graph("reasoning_graph.html")
                with open("reasoning_graph.html", "r", encoding="utf-8") as f:
                    graph_html = f.read()
                st.components.v1.html(graph_html, height=600, scrolling=True)
                
                with st.expander("View Detailed Reasoning Steps"):
                    for step in reasoning_data["steps"]:
                        st.markdown(f"""
                        **Observation:** {step['observation']}  
                        **Thought:** {step['thought']}  
                        **Action:** {step.get('action', 'N/A')}  
                        **Result:** {step.get('result', 'N/A')}  
                        ---  
                        """)

    with col2:
        st.subheader("📑 Final Plan")
        
        plan_markdown = st.session_state.response_data.get("plan_markdown")
        if plan_markdown:
            st.markdown(plan_markdown)
            
        with st.expander("📈 View Raw Plan Details"):
            raw_plan = st.session_state.response_data.get("raw_plan")
            if raw_plan:
                st.json(raw_plan)

# Sidebar
with st.sidebar:
    st.subheader("📋 Session Information")
    if hasattr(st.session_state, 'response_data'):
        st.info(f"Conversation ID: {st.session_state.response_data.get('conversation_id', 'N/A')}")
        st.info(f"Last Updated: {st.session_state.response_data.get('raw_plan', {}).get('timeline', 'N/A')}")
    
    st.subheader("⚙️ Display Settings")
    if st.checkbox("Show Raw JSON", value=False):
        st.json(getattr(st.session_state, 'response_data', {}))
