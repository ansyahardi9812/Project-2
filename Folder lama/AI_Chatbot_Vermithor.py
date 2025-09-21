import streamlit as st
import requests
import json

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="AI Chatbot Vermithor",
    page_icon="💬",
    layout="centered"
)

# --- Fungsi untuk Mendapatkan Respons dari API (dengan Streaming) ---
def get_ai_response_stream(messages_payload, model):
    """
    Mengirim request ke OpenRouter API dan menghasilkan (yield) respons secara streaming.
    """
    # Mengambil API key dari Streamlit Secrets
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
        "HTTP-Referer": "https://localhost:8501", # Diperlukan oleh OpenRouter untuk project local
        "X-Title": "Streamlit AI Chatbot" # Nama project (opsional)
    }

    data = {
        "model": model,
        "messages": messages_payload,
        "stream": True # Aktifkan mode streaming
    }

    try:
        with requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(data),
            stream=True
        ) as response:
            response.raise_for_status()  # Cek jika ada error HTTP
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
                        continue # Abaikan chunk yang tidak valid
    except requests.exceptions.RequestException as e:
        st.error(f"Error koneksi ke API: {e}")
    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")


# --- Tampilan Sidebar ---
with st.sidebar:
    st.title("⚙️ Pengaturan")
    st.markdown("Pilih model AI yang ingin Anda gunakan. Semua model di sini gratis!")

    model_options = {
        "Mistral 7B (Free)": "mistralai/mistral-7b-instruct: