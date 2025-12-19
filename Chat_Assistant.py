import streamlit as st
from groq import Groq
from PIL import Image
import requests
import io
import PyPDF2
import docx


GROQ_API_KEY = "GROQ_API_KEY"
HF_API_KEY = "HF_API_KEY"

HF_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"

groq_client = Groq(api_key=GROQ_API_KEY)
headers = {"Authorization": f"Bearer {HF_API_KEY}"}


st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="wide"
)

st.markdown("## 🤖 AI Assistant")
st.caption("Chat • File Analysis • Image Generation")


with st.sidebar:
    st.markdown("### 🛠 Tools")
    Tool = st.radio("", ["💬 Chat", "🎨 Image Generation"], index=0)
    if st.button("🔄 Reset Chat", use_container_width=True):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()


SYSTEM_PROMPT = "You are a helpful AI assistant."

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

if "last_image" not in st.session_state:
    st.session_state.last_image = None


if Tool == "💬 Chat":
    


    for msg in st.session_state.messages:
        if msg["role"] != "system":
            st.chat_message(msg["role"]).write(msg["content"])


    file_text = ""
    uploaded_image = None

    col_left, col_right = st.columns([6, 1])

    with col_right:
        with st.expander("📎 Upload", expanded=False):

            uploaded_image = st.file_uploader(
                "Image",
                type=["png", "jpg", "jpeg"],
                label_visibility="collapsed"
            )

            uploaded_file = st.file_uploader(
                "Document",
                type=["pdf", "docx", "txt"],
                label_visibility="collapsed"
            )

            if uploaded_image:
                st.image(uploaded_image, width=150)

            if uploaded_file:
                if uploaded_file.type == "application/pdf":
                    reader = PyPDF2.PdfReader(uploaded_file)
                    file_text = "\n".join(
                        page.extract_text() or "" for page in reader.pages
                    )

                elif uploaded_file.type == (
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                ):
                    doc = docx.Document(uploaded_file)
                    file_text = "\n".join(p.text for p in doc.paragraphs)

                elif uploaded_file.type == "text/plain":
                    file_text = uploaded_file.read().decode("utf-8")

 
    user_input = st.chat_input("💬 Type your message...")

    if user_input:
        full_prompt = user_input

        if file_text:
            full_prompt += f"\n\n📄 Attached file content:\n{file_text}"

        if uploaded_image:
            full_prompt += "\n\n🖼 The user uploaded an image."

        st.session_state.messages.append(
            {"role": "user", "content": full_prompt}
        )

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages,
            temperature=0.7,
            max_completion_tokens=2048,
            top_p=1
        )

        ai_reply = response.choices[0].message.content

        st.session_state.messages.append(
            {"role": "assistant", "content": ai_reply}
        )

        st.rerun()


if Tool == "🎨 Image Generation":
    st.markdown("### 🎨 Image Generation")

    prompt = st.text_area(
        "Describe the image you want",
        height=120,
        placeholder="A futuristic city at sunset, cinematic lighting..."
    )

    if st.button("✨ Generate Image"):
        with st.spinner("Generating image..."):
            response = requests.post(
                HF_URL,
                headers=headers,
                json={"inputs": prompt, "options": {"wait_for_model": True}},
                timeout=120
            )

        if "image" in response.headers.get("content-type", ""):
            st.session_state.last_image = response.content
            img = Image.open(io.BytesIO(response.content))
            st.image(img, caption=prompt, use_column_width=True)
        else:
            st.error("❌ Image generation failed")
            st.code(response.text)

    if st.session_state.last_image:
        st.download_button(
            "⬇ Download Image",
            data=st.session_state.last_image,
            file_name="generated_image.png",
            mime="image/png",
            use_container_width=True
        )
