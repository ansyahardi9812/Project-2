import streamlit as st
import requests
import json

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="AI Chatbot Vermithor",
    page_icon="🐣",
    layout="centered"
)

# --- Fungsi untuk Mendapatkan Respons dari API (dengan Streaming) ---
def get_ai_response_stream(messages_payload, model):
    """
    Mengirim request ke OpenRouter API dan menghasilkan (yield) respons secara streaming.
    """
    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
    except FileNotFoundError:
        st.error("File secrets.toml tidak ditemukan. Pastikan Anda sudah membuatnya.")
        return
    except KeyError:
        st.error("OPENROUTER_API_KEY tidak ditemukan di dalam file secrets.toml.")
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://localhost:8501", 
        "X-Title": "Streamlit AI Chatbot"
    }

    data = {
        "model": model,
        "messages": messages_payload,
        "stream": True
    }

    try:
        with requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(data),
            stream=True
        ) as response:
            response.raise_for_status()
            for chunk in response.iter_lines():
                if chunk and chunk.startswith(b'data: '):
                    chunk_data = chunk[len(b'data: '):]
                    if chunk_data.strip() == b'[DONE]':
                        break
                    try:
                        json_data = json.loads(chunk_data)
                        if "choices" in json_data and len(json_data["choices"]) > 0:
                            delta = json_data["choices"][0].get("delta", {})
                            content = delta.get("content")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue
    except requests.exceptions.RequestException as e:
        st.error(f"Error koneksi ke API: {e}")
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")


# --- Tampilan Sidebar ---
with st.sidebar:
    st.title("⚙️ Pengaturan")
    st.markdown("Pilih model AI yang ingin Anda gunakan. Semua model di sini gratis!")

    model_options = {
        "Mistral 7B (Free)": "mistralai/mistral-7b-instruct:free",
        "Llama 3.1 8B (Free)": "meta-llama/llama-3.1-8b-instruct:free",
        "DeepSeek V3 (Free)": "deepseek/deepseek-chat-v3-0324:free",
    }
    
    # KODE YANG HILANG: Menampilkan dropdown
    selected_model_name = st.selectbox(
        "Pilih Model AI:",
        options=list(model_options.keys()),
        index=0,
    )
    selected_model = model_options[selected_model_name]

    # KODE YANG HILANG: Tombol hapus chat
    if st.button("Hapus Riwayat Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("Dibuat dengan [Streamlit](https://streamlit.io) & [OpenRouter](https://openrouter.ai).")
    st.markdown("Dibuat oleh **Ardiansyah98**.")

# --- KODE YANG HILANG: Inisialisasi State Aplikasi ---
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Halo! Saya Vermithor. Ada yang bisa saya bantu hari ini?"
    }]

# --- KODE YANG HILANG: Tampilan Utama Chat ---
st.title("💬 AI Chatbot Vermithor")
st.caption(f"Menggunakan model: {selected_model_name}")

# Menampilkan riwayat chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- KODE YANG HILANG: Menerima Input Pengguna ---
if prompt := st.chat_input("Tulis pesan Anda di sini..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_generator = get_ai_response_stream(st.session_state.messages, selected_model)
        full_response = st.write_stream(response_generator)

    st.session_state.messages.append({"role": "assistant", "content": full_response})