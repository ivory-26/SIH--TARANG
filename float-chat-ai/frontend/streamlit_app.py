import streamlit as st
import json
import os
import time
import plotly.graph_objects as go

BASE_DIR = os.path.dirname(__file__)
SAMPLE_PATH = os.path.join(BASE_DIR, "static", "sample_data.json")

def load_samples():
    try:
        with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"responses": {}, "samples": []}

SAMPLE = load_samples()

st.set_page_config(page_title="Float-Chat-AI (Static)", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = "local_session"
if "user_name" not in st.session_state:
    st.session_state.user_name = "Guest"

def simulate_query(text: str):
    """Return a canned response from SAMPLE based on naive keyword matching."""
    time.sleep(0.5)  # mimic latency
    key = None
    t = text.lower()
    if "temperature" in t and "1000" in t:
        key = "avg_temp"
    elif "salinity" in t:
        key = "salinity_profile"
    elif "maximum" in t or "max" in t:
        key = "max_temp"
    else:
        # try exact sample matching
        for s in SAMPLE.get("samples", []):
            if s.lower() in t:
                # pick first matching response key
                key = list(SAMPLE.get("responses", {}).keys())[0] if SAMPLE.get("responses") else None
                break

    if key and key in SAMPLE.get("responses", {}):
        return SAMPLE["responses"][key]

    return {"text": "No canned response found. Try a sample query from the sidebar.", "data": None}


with st.sidebar:
    st.title("Float-Chat-AI (Static)")
    st.text_input("User / session id", value=st.session_state.session_id, key="_sidebar_session")
    if st.button("Start / Update Session"):
        st.session_state.session_id = st.session_state.get("_sidebar_session") or st.session_state.session_id
    st.markdown("---")
    st.subheader("Sample queries")
    for s in SAMPLE.get("samples", []):
        if st.button(s, key=f"sample_{s}"):
            st.session_state._prefill = s
    st.markdown("---")
    st.write("History (local):")
    for h in reversed(st.session_state.history[-20:]):
        st.write(f"- {h['query']} — {h.get('result_text','')[:80]}")

left, right = st.columns([1, 2])

with right:
    st.header("Conversation")
    for m in st.session_state.messages:
        role = m.get("role", "assistant")
        if role == "user":
            st.markdown(f"**You:** {m['content']}")
        else:
            st.markdown(f"**Assistant:** {m['content']}")
            if m.get("data"):
                st.json(m.get("data"))
            if m.get("plot"):
                p = m.get("plot")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=p.get("x"), y=p.get("y"), mode="lines+markers"))
                if p.get("reverse_y"):
                    fig.update_yaxes(autorange="reversed")
                fig.update_xaxes(title=p.get("x_label"))
                fig.update_yaxes(title=p.get("y_label"))
                st.plotly_chart(fig, use_container_width=True)

with left:
    st.header("Ask a question")
    with st.form("query_form", clear_on_submit=False):
        query = st.text_area("Enter query", value=st.session_state.get("_prefill", ""), height=100, key="_query")
        submitted = st.form_submit_button("Send")
        if submitted and query.strip():
            st.session_state.messages.append({"role": "user", "content": query})
            resp = simulate_query(query)
            assistant_text = resp.get("text", "")
            st.session_state.messages.append({"role": "assistant", "content": assistant_text, "data": resp.get("data"), "plot": resp.get("plot")})
            st.session_state.history.append({"query": query, "result_text": assistant_text, "timestamp": int(time.time())})
            # clear prefill after use
            st.session_state._prefill = ""

    st.markdown("---")
    if st.session_state.history:
        last = st.session_state.history[-1]
        st.download_button("Download last result (JSON)", data=json.dumps(last, indent=2), file_name="result.json", mime="application/json")


st.markdown("---")
st.caption("This is a static Streamlit prototype that uses local canned responses and sample data. Replace simulate_query() with real API calls to integrate with the backend.")
