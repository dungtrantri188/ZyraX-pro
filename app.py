# -*- coding: utf-8 -*-
import os
import sys
import time
import random
import gradio as gr
import requests
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# --- API Keys (embedded directly) ---
# Gemini API Key (hard-coded, be aware of security risk)
API_KEY = "AIzaSyBybfBSDLx39DdnZbHyLbd21tQAdfHtbeE"
# Serper.dev Key for web search (hard-coded, replace with your actual key)
SERPER_API_KEY = "badc5bf766d5e6d1f7779b7acf357e972c488a17"

# --- Configure Google AI ---
genai_configured = False
if not API_KEY:
    print("[ERROR] GOOGLE_API_KEY missing in code.")
else:
    print("[INFO] Configuring Google AI...")
    try:
        genai.configure(api_key=API_KEY)
        genai_configured = True
        print("[OK] Google AI configured successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to configure Google AI: {e}")
        genai_configured = False

# --- Model config ---
MODEL_NAME_CHAT = "gemini-2.5-flash-preview-04-17"
print(f"Using model: {MODEL_NAME_CHAT}")

# --- Helper: Format API errors ---
def format_api_error(e):
    error_message = str(e)
    error_type = type(e).__name__
    print(f"[ERROR] API call failed: {error_type} - {error_message}")
    if isinstance(e, google_exceptions.PermissionDenied):
        if "API key not valid" in error_message or "API_KEY_INVALID" in error_message:
            return "❌ Lỗi: API Key được cấu hình nhưng Google từ chối khi sử dụng (API_KEY_INVALID)."
        else:
            return f"❌ Lỗi: Permission Denied for model {MODEL_NAME_CHAT}."
    elif isinstance(e, google_exceptions.InvalidArgument) and "API key not valid" in error_message:
        return "❌ Lỗi: Invalid API Key."
    elif isinstance(e, google_exceptions.NotFound):
        return f"❌ Lỗi: Model {MODEL_NAME_CHAT} not found."
    elif isinstance(e, google_exceptions.ResourceExhausted):
        return "❌ Lỗi: Quota exceeded."
    elif isinstance(e, google_exceptions.DeadlineExceeded):
        return "❌ Lỗi: Request timeout."
    elif isinstance(e, AttributeError) and "start_chat" in error_message:
        return f"❌ Lỗi: Method start_chat not supported by model {MODEL_NAME_CHAT}."
    else:
        return f"❌ Lỗi gọi AI ({error_type}): {error_message}"

# --- Web search helper using Serper.dev ---
def search_web(query):
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"q": query}
    try:
        resp = requests.post("https://google.serper.dev/search", headers=headers, json=payload, timeout=10)
        data = resp.json()
    except Exception as e:
        print(f"[ERROR] Web search failed: {e}")
        return None

    summaries = []
    for result in data.get("organic", [])[:3]:
        title = result.get("title", "<no title>")
        snippet = result.get("snippet", "<no snippet>")
        link = result.get("link", "<no link>")
        summaries.append(f"- {title} ({link}): {snippet}")
    return "\n".join(summaries)

# --- Large cycling emojis (full list) ---
LARGE_CYCLING_EMOJIS = [
    "😀", "😁", "😂", "🤣", "😃", "😄", "😅", "😆", "😉", "😊",
    "😋", "😎", "😍", "😘", "🥰", "😗", "😙", "😚", "🙂", "🤗",
    "🤩", "🤔", "🤨", "😐", "😑", "😶", "🙄", "😏", "😣", "😥",
    "😮", "🤐", "😯", "😪", "😫", "😴", "😌", "😛", "😜", "😝",
    "🤤", "😒", "😓", "😔", "😕", "🙃", "🤑", "😲", "☹️", "🙁",
    "😖", "😞", "😟", "😤", "😢", "😭", "😦", "😧", "😨", "😩",
    "🤯", "😬", "😰", "😱", "🥵", "🥶", "😳", "🤪", "😵", "🥴",
    "😠", "😡", "🤬", "😷", "🤒", "🤕", "🤢", "🤮", "🤧", "😇",
    "🥳", "🥺", "🤠", "🤡", "🤥", "🤫", "🤭", "🧐", "🤓", "😈",
    "👿", "👹", "👺", "💀", "👻", "👽", "🤖", "💩", "😺", "😸",
    "😹", "😻", "😼", "😽", "🙀", "😿", "😾", "🫶", "👍", "👎",
    "👌", "🤌", "🤏", "✌️", "🤞", "🤟", "🤘", "🤙", "👈", "👉",
    "👆", "🖕", "👇", "☝️", "✋", "🤚", "🖐️", "🖖", "👋", "🙏",
    "🧠", "🫀", "🫁", "🦷", "🦴", "👀", "👁️", "👅", "👄", "👶",
    "🧒", "👦", "👧", "🧑", "👱", "👨", "🧔", "👩", "👠", "👑",
    "💍", "💎", "🐵", "🐶", "🐺", "🐱", "🦁", "🐯", "🦒", "🦊",
    "🦝", "🐮", "🐷", "🐗", "🐭", "🐹", "🐰", "🐸", "🐨", "🐼",
    "🐻", "🐧", "🐦", "🐤", "🦋", "🐛", "🐝", "🐞", "🦂", "🦀",
    "🐍", "🐢", "🐠", "🐳", "🐬", "🐙", "🍎", "🍌", "🍇", "🍓",
    "🍕", "🍔", "🍟", "⚽️", "🏀", "🏈", "⚾️", "🎾", "🏐", "🎱",
    "🎮", "🎰", "🚀", "✈️", "🚗", "🚲", "📱", "💻", "💡", "💰",
    "📈", "📉", "⚙️", "🔧", "🔨", "⚔️", "🛡️", "⏳", "⏰", "🎉",
    "🎁", "🎈", "✉️", "❤️", "💔", "⭐️", "🌟", "⚡️", "💥", "💨",
    "💦", "💧", "🌊", "☀️", "🌙", "☁️", "🔥", "🌈", "⛄️", "❄️"
]

# --- Gradio callback ---
def respond(message, chat_history_state):
    # ensure state is list
    if chat_history_state is None:
        chat_history_state = []

    if not genai_configured:
        err = "❌ Lỗi: Google AI chưa được cấu hình đúng cách."
        chat_history_state.append([message, err])
        return "", chat_history_state, chat_history_state

    # Perform web search when needed
    lower = message.lower()
    if any(tok in lower for tok in ["tìm", "tra cứu", "search", "lookup"]):
        print("[INFO] Performing web search...")
        summary = search_web(message)
        if summary:
            message = f"(Kết quả tìm kiếm web gần nhất):\n{summary}\n\nYêu cầu: {message}"
        else:
            message = f"(Không thể tìm kiếm web do lỗi kỹ thuật.)\n\n{message}"

    # build history for Gemini
    history = []
    for user_msg, model_msg in chat_history_state:
        if user_msg:
            history.append({'role': 'user', 'parts': [user_msg]})
        if model_msg and not model_msg.startswith(("❌", "⚠️")):
            history.append({'role': 'model', 'parts': [model_msg]})

    # append current user message
    chat_history_state.append([message, ""])
    idx = len(chat_history_state) - 1
    full_text = ""
    emoji_idx = 0

    try:
        model = genai.GenerativeModel(MODEL_NAME_CHAT)
        chat = model.start_chat(history=history)
        for chunk in chat.send_message(message, stream=True):
            txt = getattr(chunk, 'text', '') or ''
            for c in txt:
                full_text += c
                # safe emoji selection
                if LARGE_CYCLING_EMOJIS:
                    current_emoji = LARGE_CYCLING_EMOJIS[emoji_idx % len(LARGE_CYCLING_EMOJIS)]
                    emoji_idx += 1
                else:
                    current_emoji = ''
                chat_history_state[idx][1] = full_text + f" {current_emoji}"
                yield "", chat_history_state, chat_history_state
                time.sleep(0.02)
        # finalize
        chat_history_state[idx][1] = full_text
        yield "", chat_history_state, chat_history_state
        print("[OK] Stream complete.")
    except Exception as e:
        err = format_api_error(e)
        chat_history_state[idx][1] = err
        yield "", chat_history_state, chat_history_state

# --- Gradio UI ---
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@800&display=swap');
.gradio-container .chatbot .message.bot { font-family: 'Nunito'; font-weight:800; font-size:1.8em!important; line-height:1.5!important;} 
.gradio-container .chatbot .message.user { font-size:1.8em!important; line-height:1.5!important;} 
"""

with gr.Blocks(theme=gr.themes.Default(), css=custom_css) as demo:
    gr.Markdown("## ZyRa X with Web Search")
    chatbot = gr.Chatbot(type='tuples', height=500)
    state = gr.State([])
    msg = gr.Textbox(placeholder="Nhập câu hỏi...", scale=4)
    send = gr.Button("Gửi")
    clear = gr.Button("🗑️ Xóa")

    msg.submit(respond, [msg, state], [msg, chatbot, state])
    send.click(respond, [msg, state], [msg, chatbot, state])
    clear.click(lambda: ("", [], []), [], [msg, chatbot, state], queue=False)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 7860))
    demo.queue().launch(server_name='0.0.0.0', server_port=port, debug=False)
