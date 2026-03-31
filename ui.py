import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000"

if "token" not in st.session_state:
    st.session_state.token = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.set_page_config(page_title="AI Document Assistant", layout="wide")

st.title("📄 AI Document Assistant (RAG)")
st.write("Upload documents and ask questions 🤖")

st.sidebar.header("🔐 Authentication")

auth_option = st.sidebar.radio("Choose Option", ["Login", "Register"])

email = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Password", type="password")

if auth_option == "Login":
    if st.sidebar.button("Login"):
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                data={"username": email, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code == 200:
                st.session_state.token = response.json()["access_token"]
                st.session_state.logged_in = True
                st.success("Login successful ✅")
                st.rerun() 

            elif response.status_code == 401:
                st.error("User not found or wrong password ❌")
                st.info("👉 Please register first")
            else:
                st.error(f"Login failed ❌ ({response.status_code})")
                st.write(response.text)

        except Exception as e:
            st.error(f"Backend not running ❌ Start FastAPI server\n{e}")

if auth_option == "Register":
    if st.sidebar.button("Register"):
        try:
            response = requests.post(
                f"{BASE_URL}/auth/register",
                json={"email": email, "password": password}
            )

            if response.status_code == 200:
                st.success("User registered successfully ✅ Now login")
            else:
                st.error("Registration failed ❌")
                st.write(response.text)

        except Exception as e:
            st.error(f"Backend not running ❌\n{e}")


if st.session_state.logged_in and st.session_state.token:
    st.sidebar.success("Logged in ✅")
    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.logged_in = False
        st.rerun()
else:
    st.sidebar.warning("Not logged in ⚠️")


def get_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

if not st.session_state.logged_in or not st.session_state.token:
    st.warning("🔐 Please login from the sidebar to continue.")
    st.stop()  # ✅ nothing below renders unless logged in


st.header("📤 Upload Document")
st.write("Upload PDF or CSV")

title = st.text_input("Document Title")
company_name = st.text_input("Company Name")
document_type = st.selectbox("Document Type", ["PDF", "CSV", "Invoice", "Report", "Other"])
uploaded_file = st.file_uploader("Upload PDF or CSV", type=["pdf", "csv"])

if st.button("Upload"):
    if not uploaded_file:
        st.error("Please select a file.")
    elif not title or not company_name or not document_type:
        st.error("Please fill in all fields.")
    else:
        try:
            response = requests.post(
                f"{BASE_URL}/documents/upload",
                headers=get_headers(),  # ✅ uses function to always get fresh token
                files={"file": (uploaded_file.name, uploaded_file, uploaded_file.type)},
                data={"title": title, "company_name": company_name, "document_type": document_type}
            )

            if response.status_code == 200:
                st.success("Document uploaded successfully ✅")
            else:
                st.error(f"Upload failed ❌\n{response.text}")

        except Exception as e:
            st.error(f"Error: {e}")

st.header("🔍 Ask Questions")

query = st.text_input("Enter your question")

if st.button("Search"):
    if not query:
        st.warning("Please enter a question.")
    else:
        try:
            response = requests.post(
                f"{BASE_URL}/rag/search",
                params={"query": query},
                headers=get_headers()
            )

            if response.status_code == 200:
                data = response.json()

                # ✅ Answer section - clean card style
                st.markdown("---")
                st.subheader("🤖 Answer")
                st.info(data["answer"])  # ✅ info box looks much cleaner than plain write

                # ✅ Context section - collapsible chunks
                st.markdown("---")
                st.subheader("📄 Source Context")
                st.caption(f"Found {len(data['context'])} relevant chunk(s) from your documents")

                for i, chunk in enumerate(data["context"]):
                    with st.expander(f"📌 Chunk {i+1} — click to expand", expanded=False):
                        # Clean up chunk text
                        cleaned = chunk.strip()
                        st.markdown(
                            f"""
                            <div style="
                                background-color: #1e1e2e;
                                padding: 16px;
                                border-radius: 8px;
                                border-left: 4px solid #7c3aed;
                                font-size: 0.875rem;
                                line-height: 1.6;
                                color: #cdd6f4;
                                white-space: pre-wrap;
                                word-wrap: break-word;
                            ">
                                {cleaned}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        # word count badge
                        word_count = len(cleaned.split())
                        st.caption(f"📝 {word_count} words in this chunk")

            else:
                st.error("Search failed ❌")
                st.write(response.text)

        except Exception as e:
            st.error(f"Error: {e}")# -------------------------


st.header("📑 Get Document by ID")

search_id = st.number_input("Document ID", min_value=1, step=1, key="doc_fetch")

if st.button("Fetch Document"):
    try:
        response = requests.get(
            f"{BASE_URL}/documents/{search_id}",
            headers=get_headers()
        )

        if response.status_code == 200:
            st.success("Document fetched ✅")
            st.json(response.json())
        else:
            st.error("Not found ❌")
            st.write(response.text)

    except Exception as e:
        st.error(f"Error: {e}")