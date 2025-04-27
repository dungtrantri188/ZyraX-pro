# -*- coding: utf-8 -*-
import os
import time
import random
import gradio as gr
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# --- PHẦN API KEY VÀ CẤU HÌNH GENAI (Giữ nguyên) ---
API_KEY = "AIzaSyAzz9aSguVHcu-Ef_6HeQifwjXIeNURUhM" # Thay bằng key của bạn nếu cần

genai_configured = False
if not API_KEY:
    print("[ERROR] API Key bị thiếu.")
else:
    print("[INFO] API Key được gán trực tiếp trong code.")
    print("Đang cấu hình Google AI...")
    try:
        # Lưu ý: Nên dùng biến môi trường thay vì gán trực tiếp key vào code
        # os.environ['GOOGLE_API_KEY'] = API_KEY
        # genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
        genai.configure(api_key=API_KEY) # Sử dụng key trực tiếp (ít bảo mật hơn)
        genai_configured = True
        print("[OK] Google AI đã được cấu hình thành công.")
    except Exception as e:
        print(f"[ERROR] Không thể cấu hình Google AI: {e}")
        genai_configured = False

MODEL_NAME_CHAT = "gemini-2.5-flash-preview-04-17" # Thay bằng model bạn muốn, ví dụ: "gemini-pro"
print(f"Sử dụng model chat: {MODEL_NAME_CHAT}")

# --- HÀM format_api_error (Giữ nguyên) ---
def format_api_error(e):
    error_message = str(e)
    error_type = type(e).__name__
    print(f"[ERROR] Lỗi khi gọi API: {error_type} - {error_message}")

    if isinstance(e, google_exceptions.PermissionDenied):
        if "API key not valid" in error_message or "API_KEY_INVALID" in error_message:
            return "❌ Lỗi: API Key được cấu hình nhưng Google từ chối khi sử dụng (API_KEY_INVALID)."
        elif "permission to access model" in error_message:
             return f"❌ Lỗi: Từ chối quyền truy cập cho model '{MODEL_NAME_CHAT}'. API Key có thể không được cấp quyền cho model này."
        else:
            return f"❌ Lỗi: Từ chối quyền truy cập (PermissionDenied): {error_message}"
    elif isinstance(e, google_exceptions.InvalidArgument) and "API key not valid" in error_message:
        return "❌ Lỗi: API Key không hợp lệ (InvalidArgument)."
    elif isinstance(e, google_exceptions.NotFound):
         return f"❌ Lỗi: Model '{MODEL_NAME_CHAT}' không tìm thấy hoặc không tồn tại."
    elif isinstance(e, google_exceptions.ResourceExhausted):
        return "❌ Lỗi: Quá hạn ngạch API. Vui lòng thử lại sau hoặc kiểm tra giới hạn sử dụng của bạn."
    elif isinstance(e, google_exceptions.DeadlineExceeded):
        return "❌ Lỗi: Yêu cầu vượt quá thời gian chờ. Vui lòng thử lại."
    else:
        return f"❌ Lỗi không xác định khi gọi AI ({error_type}): {error_message}"

# --- Danh sách Emoji Lớn (Giữ nguyên) ---
LARGE_CYCLING_EMOJIS = [
    "😀","😁","😂","🤣","😃","😄","😅","😆","😉","😊","😋","😎","😍","😘","🥰","😗","😙","😚","🙂","🤗",
    "🤩","🤔","🤨","😐","😑","😶","🙄","😏","😣","😥","😮","🤐","😯","😪","😫","😴","😌","😛","😜","😝",
    "🤤","😒","😓","😔","😕","🙃","🤑","😲","☹️","🙁","😖","😞","😟","😤","😢","😭","😦","😧","😨","😩",
    "🤯","😬","😰","😱","🥵","🥶","😳","🤪","😵","🥴","😠","😡","🤬","😷","🤒","🤕","🤢","🤮","🤧","😇",
    "🥳","🥺","🤠","🤡","🤥","🤫","🤭","🧐","🤓","😈","👿","👹","👺","💀","👻","👽","🤖","💩","😺","😸",
    "😹","😻","😼","😽","🙀","😿","😾","🫶","👍","👎","👌","🤌","🤏","✌️","🤞","🤟","🤘","🤙","👈","👉",
    "👆","🖕","👇","☝️","✋","🤚","🖐️","🖖","👋","🙏","🤝","💅","🤲","👐","🤜","🤛","🙌","👏","👊","✊",
    "💪","🦵","🦶","👂","👃","🧠","🫀","🫁","🦷","🦴","👀","👁️","👅","👄","👶","🧒","👦","👧","🧑","👱",
    "👨","🧔","👩","👵","👴","🧓","👲","👳","👮","🕵️","💂","👷","🤴","👸","👼","🎅","🤶","🦸","🦹","🧙",
    "🧚","🧛","🧝","🧞","🧜","🦩","🐵","🐒","🦍","🦧","🐶","🐕","🦮","🐕‍🦺","🐩","🐺","🦊","🐱","🐈","🐈‍⬛",
    "🦁","🐯","🐅","🐆","🐴","🦄","🦓","🦌","🐮","🐂","🐃","🐄","🐷","🐖","🐗","🐽","🐏","🐑","🐐","🐪",
    "🐫","🦙","🦒","🐘","🦣","🦏","🦛","🐭","🐁","🐀","🐹","🐰","🐇","🐿️","🦔","🦇","🐻","🐨","🐼","🦥",
    "🦦","🦨","🦘","🦡","🐾","🐉","🐲","🌵","🎄","🌲","🌳","🌴","🌱","🌿","☘️","🍀","🎍","🎋","🍃","🍂",
    "🍁","🍄","🌾","💐","🌷","🌹","🥀","🌺","🌸","🌼","🌻","🌞","🌝","🌛","🌜","🌚","🌕","🌖","🌗","🌘",
    "🌑","🌒","🌓","🌔","🌙","🌎","🌍","🌏","💫","⭐️","🌟","✨","⚡️","☄️","💥","🔥","🌪️","🌈","☀️","🌤️",
    "⛅️","🌥️","🌦️","🌧️","⛈️","🌩️","🌨️","❄️","☃️","⛄️","🌬️","💨","💧","🌊","🌫️","💦","☔️","☂️",
    "⚱️","🪴","🏵️","🎗️","🎟️","🎫","🎖️","🏆","🏅","🥇","🥈","🥉","⚽️","🏀","🏈","⚾️","🥎","🎾","🏐",
    "🏉","🥏","🎱","🪀","🏓","🏸","🥅","🏒","🏑","🏏","⛳️","🏹","🎣","🤿","🥊","🥋","🥌","🛷","⛸️","🎿",
    "⛷️","🏂","🏋️","🤼","🤸","⛹️","🤺","🤾","🏌️","🏇","🧘","🛹","🛼","🚣","🏊","⛴️","🚤","🛥️","🛳️",
    "⛵️","🚢","✈️","🛩️","🛫","🛬","🚁","🚟","🚠","🚡","🚂","🚆","🚇","🚈","🚉","🚊","🚝","🚞","🚋",
    "🚃","🚎","🚌","🚍","🚙","🚗","🚕","🚖","🚛","🚚","🚐","🛻","🚜","🏍️","🛵","🦽","🦼","🛺","🚲",
    "🛴","🛹","🛼","🚏","🛣️","🛤️","🛢️","⛽️","🚨","🚥","🚦","🛑","🚧","⚓️","⛵️","🚤","🛳️","🛥️","🚢",
    "⚓️","⛽️","🚧"
]

# --- HÀM respond (Giữ nguyên) ---
def respond(message, chat_history_state):
    if not genai_configured:
        error_msg = "❌ Lỗi: Google AI chưa được cấu hình đúng cách. Vui lòng kiểm tra API Key và kết nối mạng."
        chat_history_state = (chat_history_state or []) + [[message, error_msg]]
        return "", chat_history_state, chat_history_state

    # Xây dựng lịch sử chat cho API
    history = []
    if chat_history_state: # Chỉ xử lý nếu chat_history_state không rỗng
        for u, m in chat_history_state:
            # Bỏ qua các tin nhắn lỗi hoặc trống từ user/model
            if u and isinstance(u, str) and u.strip():
                history.append({'role': 'user', 'parts': [u]})
            if m and isinstance(m, str) and m.strip() and not m.startswith("❌"):
                history.append({'role': 'model', 'parts': [m]})

    # Thêm tin nhắn mới của người dùng vào cuối lịch sử hiển thị
    current_chat_entry = [message, ""] # Tạo entry mới
    chat_history_state = (chat_history_state or []) + [current_chat_entry]
    idx = len(chat_history_state) - 1 # Index của entry hiện tại

    full_text = ""
    char_count = 0
    emoji_idx = 0

    try:
        print(f"[DEBUG] Sending history to API: {history}") # Log lịch sử gửi đi
        model = genai.GenerativeModel(MODEL_NAME_CHAT)
        # Cấu hình an toàn (tùy chọn, có thể bỏ nếu muốn ít bị chặn hơn)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        chat = model.start_chat(history=history)
        response = chat.send_message(message, stream=True, safety_settings=safety_settings) # Thêm safety_settings

        for chunk in response:
            # Kiểm tra xem chunk có text không và xử lý lỗi nếu có
            if hasattr(chunk, 'prompt_feedback') and chunk.prompt_feedback.block_reason:
                 block_reason = chunk.prompt_feedback.block_reason_message # Lấy lý do chi tiết hơn
                 print(f"[WARN] Nội dung bị chặn: {block_reason}")
                 error_msg = f"⚠️ Nội dung có thể không phù hợp hoặc bị chặn bởi bộ lọc an toàn ({block_reason})."
                 chat_history_state[idx][1] = error_msg
                 yield "", chat_history_state, chat_history_state
                 return # Dừng xử lý nếu bị chặn

            # Kiểm tra lỗi trong candidates nếu có
            if not chunk.candidates:
                print(f"[WARN] Chunk không có candidates: {chunk}")
                # Có thể là chunk cuối cùng hoặc lỗi khác, tạm thời bỏ qua
                continue
            if chunk.candidates[0].finish_reason not in (None, 0): # 0 = FINISH_REASON_UNSPECIFIED
                finish_reason = chunk.candidates[0].finish_reason
                reason_msg = f"Lý do kết thúc: {finish_reason}"
                if hasattr(chunk.candidates[0], 'safety_ratings'):
                     ratings_str = ", ".join([f"{r.category}: {r.probability.name}" for r in chunk.candidates[0].safety_ratings])
                     reason_msg += f" (Safety Ratings: {ratings_str})"
                print(f"[WARN] Stream kết thúc sớm hoặc bị chặn. {reason_msg}")
                if finish_reason == 1: # 1 = STOP
                     # Kết thúc bình thường, không cần báo lỗi
                     pass
                elif finish_reason == 2: # 2 = MAX_TOKENS
                    error_msg = "⚠️ Phản hồi đã đạt đến giới hạn độ dài tối đa."
                    chat_history_state[idx][1] = full_text + "\n" + error_msg
                    yield "", chat_history_state, chat_history_state
                    return
                elif finish_reason == 3: # 3 = SAFETY
                    error_msg = f"⚠️ Nội dung bị chặn bởi bộ lọc an toàn. {reason_msg}"
                    chat_history_state[idx][1] = error_msg
                    yield "", chat_history_state, chat_history_state
                    return
                elif finish_reason == 4: # 4 = RECITATION
                     error_msg = f"⚠️ Nội dung bị chặn do liên quan đến nguồn trích dẫn. {reason_msg}"
                     chat_history_state[idx][1] = error_msg
                     yield "", chat_history_state, chat_history_state
                     return
                else: # OTHER
                    error_msg = f"⚠️ Phản hồi bị dừng vì lý do không xác định. {reason_msg}"
                    chat_history_state[idx][1] = error_msg
                    yield "", chat_history_state, chat_history_state
                    return

            # Lấy text an toàn hơn
            txt = ""
            if chunk.parts:
                 txt = "".join(part.text for part in chunk.parts if hasattr(part, 'text'))

            if txt: # Chỉ xử lý nếu có text
                for ch in txt:
                    full_text += ch
                    char_count += 1
                    time.sleep(0.02 / 1.5) # Giữ hiệu ứng typing
                    # Cập nhật emoji xoay vòng
                    if char_count % 2 == 0:
                        emoji_idx += 1
                    current_emoji = LARGE_CYCLING_EMOJIS[emoji_idx % len(LARGE_CYCLING_EMOJIS)]
                    # Cập nhật tin nhắn của bot trong state
                    chat_history_state[idx][1] = full_text + f" {current_emoji}"
                    yield "", chat_history_state, chat_history_state
            else:
                # print(f"[DEBUG] Received empty text chunk: {chunk}")
                pass

        # Sau khi vòng lặp kết thúc, cập nhật tin nhắn cuối cùng không có emoji
        if full_text:
             chat_history_state[idx][1] = full_text
        elif not chat_history_state[idx][1].startswith("⚠️") and not chat_history_state[idx][1].startswith("❌"):
             print("[WARN] Không nhận được nội dung text từ API sau khi stream thành công.")
             # Giữ nguyên tin nhắn rỗng hoặc xử lý khác nếu cần

        # Cập nhật state cuối cùng
        yield "", chat_history_state, chat_history_state

    except Exception as e:
        err = format_api_error(e)
        # Đảm bảo cập nhật lỗi vào đúng entry cuối cùng
        chat_history_state[idx][1] = err
        yield "", chat_history_state, chat_history_state


# --- GIAO DIỆN GRADIO ---
with gr.Blocks(theme=gr.themes.Default(
    # primary_hue=gr.themes.colors.orange,
    # secondary_hue=gr.themes.colors.brown,
)) as demo:
    # --- CSS ĐÃ CẬP NHẬT ---
    gr.HTML('''
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@800&display=swap');

        /* Màu nền chung */
        body, .gradio-container {
            background-color: #f5f4ed !important; /* Màu nền bạn đang dùng */
        }

        /* Font chữ mặc định */
        * {
            font-family: 'Nunito', sans-serif !important;
        }

        /* --- THAY ĐỔI MÀU SẮC THEO YÊU CẦU --- */

        /* 1. Màu tiêu đề "ZyRa X - tạo bởi Dũng" */
        .gradio-container .prose h2 {
            color: #CC7F66 !important;
            text-align: center;
            margin-bottom: 1rem;
        }

        /* 2. Màu chữ khi chat (User và Bot) */
        .chatbot .message.user span,
        .chatbot .message.bot span,
        .chatbot .message.user p,
        .chatbot .message.bot p {
            color: #FFB57B !important; /* Màu cam bạn muốn cho chat */
        }

        /* 3. Màu chữ trong ô nhập liệu và nút Gửi */
        .gradio-textbox textarea,
        .gradio-button span {
           color: #FFB57B !important; /* Cho đồng bộ màu cam */
        }
        .gradio-textbox textarea::placeholder {
           color: #FFB57B;
           opacity: 0.6;
        }

        /* --- CÁC STYLE KHÁC GIỮ NGUYÊN HOẶC TINH CHỈNH --- */
        strong, b { color: #000000 !important; }
        .chatbot .message.bot,
        .chatbot .message.user,
        .gradio-textbox,
        .gradio-button {
            background-color: transparent !important;
            border: 1px solid #FFDAB9 !important;
            border-radius: 8px !important;
        }
         .chatbot .message {
             border: none !important;
             padding: 10px 15px !important;
             border-radius: 15px !important;
             box-shadow: 0 1px 3px rgba(0,0,0,0.1);
             max-width: 85%;
             word-wrap: break-word; /* Đảm bảo chữ tự xuống dòng */
             overflow-wrap: break-word; /* Tương tự word-wrap */
             white-space: pre-wrap; /* Giữ các khoảng trắng và xuống dòng từ markdown */
         }
         .chatbot .message.user {
             background: #FFF0E1 !important;
             border-radius: 15px 15px 0 15px !important;
             margin-left: auto;
         }
         .chatbot .message.bot {
             background: #ffffff !important;
             border-radius: 15px 15px 15px 0 !important;
             margin-right: auto;
         }
         .chatbot .message.user span, .chatbot .message.user p { color: #FFB57B !important; }
         .chatbot .message.bot span, .chatbot .message.bot p { color: #FFB57B !important; }

        /* Style cho LaTeX (do KaTeX/MathJax render) */
        .chatbot .message .math-inline .katex, /* Inline math */
        .chatbot .message .math-display .katex-display { /* Display math */
            color: #FFB57B !important; /* Áp dụng màu cam cho LaTeX */
            /* font-size: 1.1em !important; /* Có thể tăng cỡ chữ nếu muốn */
        }
        /* Đảm bảo code blocks cũng xuống dòng */
        .chatbot .message code {
             white-space: pre-wrap !important;
             word-wrap: break-word !important;
        }
        .chatbot .message pre code {
             display: block;
             overflow-x: auto; /* Thêm thanh cuộn ngang nếu code quá dài */
        }


        #component-8 { margin-top: 10px; }
        </style>
    ''')
    # Tiêu đề sử dụng Markdown để tạo thẻ H2
    gr.Markdown("## ZyRa X - tạo bởi Dũng")

    chatbot = gr.Chatbot(
        label="Chatbot",
        height=500,
        bubble_full_width=False,
        # ========= THÊM THAM SỐ NÀY ĐỂ HỖ TRỢ LATEX =========
        latex_delimiters=[
            {"left": "$$", "right": "$$", "display": True},  # $$...$$ for display math
            {"left": "$", "right": "$", "display": False}, # $...$ for inline math
            {"left": "\\(", "right": "\\)", "display": False}, # \(...\) for inline math
            {"left": "\\[", "right": "\\]", "display": True}   # \[...\] for display math
        ]
        # ======================================================
        # render_markdown=True # Mặc định là True, cần thiết cho LaTeX hoạt động cùng Markdown
    )
    state = gr.State([]) # Khởi tạo state là list rỗng

    with gr.Row():
        txt = gr.Textbox(
            placeholder="Nhập câu hỏi của bạn ở đây...",
            label="Bạn",
            scale=4,
            # elem_id="user_input"
        )
        btn = gr.Button("Gửi", variant="primary") # Làm nút nổi bật hơn

    clr = gr.Button("🗑️ Xóa cuộc trò chuyện")

    # Kết nối sự kiện
    txt.submit(respond, [txt, state], [txt, chatbot, state])
    btn.click(respond, [txt, state], [txt, chatbot, state])
    # Sửa hàm lambda cho nút xóa để đảm bảo state được reset đúng cách
    clr.click(lambda: (None, [], []), outputs=[txt, chatbot, state], queue=False) # queue=False để xóa ngay lập tức

print("Đang khởi chạy Gradio UI...")
# Chạy app
demo.queue().launch(
    server_name='0.0.0.0',
    server_port=int(os.environ.get('PORT', 7860)),
    debug=False, # Tắt debug khi deploy
    # share=True # Bật nếu muốn tạo link public tạm thời
)
print("Gradio UI đã khởi chạy.")
