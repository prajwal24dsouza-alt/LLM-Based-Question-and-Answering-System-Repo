import requests
import streamlit as st


API_BASE_URL = st.sidebar.text_input("API Base URL", "http://127.0.0.1:8000")
SESSION_ID = st.sidebar.text_input("Session ID", "streamlit-demo")
TOP_K = st.sidebar.slider("Top K", min_value=1, max_value=10, value=4)


st.title("LLM-Based Question Answering")
st.caption("Upload documents into the backend, then ask questions over the ingested knowledge base.")


if st.button("Ingest Documents From data/"):
    response = requests.post(f"{API_BASE_URL}/ingest", json={"file_paths": None}, timeout=120)
    if response.ok:
        st.success("Ingestion completed successfully.")
        st.json(response.json())
    else:
        st.error(f"Ingestion failed: {response.text}")


question = st.text_area("Ask a question", placeholder="What topics are covered in the documents?")

if st.button("Get Answer") and question.strip():
    response = requests.post(
        f"{API_BASE_URL}/query",
        json={
            "query": question,
            "top_k": TOP_K,
            "session_id": SESSION_ID,
            "include_sources": True,
        },
        timeout=120,
    )
    if response.ok:
        payload = response.json()
        st.subheader("Answer")
        st.write(payload["answer"])
        st.subheader("Metrics")
        st.json(payload["metrics"])
        st.subheader("Sources")
        st.json(payload.get("sources", []))
    else:
        st.error(f"Query failed: {response.text}")
