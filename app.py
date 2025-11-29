import streamlit as st
from typing import List, Dict
import numpy as np

from backend.ingest import build_documents
from backend.retrieval import (
    build_index,
    retrieve_top_k,
    load_existing_index,
    clear_index,
)
from backend.llm import ask_llm_hr


# =========================
# PAGE CONFIGURATION
# =========================
st.set_page_config(
    page_title="AskHR – AI HR Assistant",
    page_icon="👩‍💼",
    layout="wide",
)

st.title("👩‍💼 AskHR – AI HR Assistant")
st.markdown(
    "Upload your HR policy documents and let employees ask questions about "
    "**leave, WFH, notice period, benefits, and company rules** in natural language."
)


# =========================
# SESSION STATE INIT
# =========================
if "docs" not in st.session_state:
    st.session_state.docs: List[Dict] = load_existing_index()  # Load stored chunks

if "emb_matrix" not in st.session_state:
    st.session_state.emb_matrix = np.zeros((0, 1))  # Not used in offline mode

if "messages" not in st.session_state:
    st.session_state.messages: List[Dict] = []


# =========================
# MODE SWITCH (HR / Employee)
# =========================
mode = st.sidebar.radio(
    "Select Mode:",
    ["Employee", "HR"],
    index=1,               # Default is HR mode during development
    horizontal=True
)


# =========================
# HR MODE: Upload, Build, Clear
# =========================
if mode == "HR":

    st.sidebar.header("📄 Upload HR Documents")
    uploaded_files = st.sidebar.file_uploader(
        "Upload HR policy files (PDF or TXT)",
        type=["pdf", "txt"],
        accept_multiple_files=True,
    )

    build_index_button = st.sidebar.button("🔧 Build / Refresh HR Knowledge Base")

    # Knowledge base status
    if st.session_state.docs:
        st.sidebar.success(
            f"Loaded {len(st.session_state.docs)} text chunks from HR policies."
        )
    else:
        st.sidebar.info("No HR policy data loaded yet.")

    # Clear knowledge base
    clear_kb_button = st.sidebar.button("🗑 Clear HR Knowledge Base")
    if clear_kb_button:
        clear_index()
        st.session_state.docs = []
        st.session_state.messages = []
        st.session_state.emb_matrix = np.zeros((0, 1))
        st.sidebar.success("Cleared stored HR knowledge base.")
        st.rerun()

    # Build KB (only in HR mode)
    if build_index_button:
        if uploaded_files:
            with st.spinner("Processing HR documents and building knowledge base..."):
                docs = build_documents(uploaded_files)
                emb_matrix, docs = build_index(docs)
                st.session_state.docs = docs
                st.session_state.emb_matrix = emb_matrix
                st.session_state.messages = []

            st.sidebar.success(
                f"Indexed {len(st.session_state.docs)} text chunks from your HR documents!"
            )
            st.rerun()
        else:
            st.sidebar.warning("Please upload at least one HR document first.")


# =========================
# MAIN CHAT AREA
# =========================

st.subheader("💬 Ask HR a Question")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# No knowledge base → show instructions
if not st.session_state.docs:
    st.info(
        "To get started:\n\n"
        "**If you are HR:**\n"
        "1. Switch to **HR Mode** using the sidebar\n"
        "2. Upload HR policy documents\n"
        "3. Click **Build / Refresh HR Knowledge Base**\n\n"
        "**If you are an employee:**\n"
        "• Ask questions like:\n"
        "- How many casual leaves are allowed?\n"
        "- What is the notice period after confirmation?\n"
        "- How many WFH days per month?\n"
    )

else:
    # Chat input (visible in both Employee & HR mode)
    user_query = st.chat_input("Ask something about HR policies...")

    if user_query:
        # User message
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Assistant response
        with st.chat_message("assistant"):
            with st.spinner("Checking HR policies..."):
                top_chunks = retrieve_top_k(
                    user_query,
                    st.session_state.emb_matrix,
                    st.session_state.docs,
                    k=4,
                )

                if not top_chunks:
                    answer = (
                        "I couldn't find relevant information in the HR policies. "
                        "Please contact the HR team."
                    )
                else:
                    answer = ask_llm_hr(user_query, top_chunks)

                st.markdown(answer)

                # Show supporting policy chunks
                if top_chunks:
                    with st.expander("🔍 Show supporting policy snippets"):
                        for c in top_chunks:
                            st.markdown(
                                f"**Source:** {c.get('source')} (chunk {c.get('chunk_id')})"
                            )
                            st.markdown(f"> {c['text'][:800]}...\n")

        # Save assistant message
        st.session_state.messages.append({"role": "assistant", "content": answer})
