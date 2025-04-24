# -*- coding: utf-8 -*-
import os
import time
import random
import gradio as gr
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# --- PHẦN API KEY VÀ CẤU HÌNH GENAI (Giữ nguyên) ---
API_KEY = "AIzaSyBybfBSDLx39DdnZbHyLbd21tQAdfHtbeE" # Thay bằng key của bạn nếu cần

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

MODEL_NAME_CHAT = "gemini-1.5-flash-latest" # Thay bằng model bạn muốn, ví dụ: "gemini-1.5-flash-latest"
print(f"Sử dụng model chat: {MODEL_NAME_CHAT}")

# --- HÀM format_api_error (Giữ nguyên) ---
def format_api_error(e):
    error_message = str(e)
    error_type = type(e).__name__
    print(f"[ERROR] Lỗi khi gọi API: {error_type} - {error_message}")
    # (Các trường hợp lỗi khác giữ nguyên)
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
        chat = model.start_chat(history=history)
        response = chat.send_message(message, stream=True)

        for chunk in response:
            # Kiểm tra xem chunk có text không và xử lý lỗi nếu có
            if hasattr(chunk, 'prompt_feedback') and chunk.prompt_feedback.block_reason:
                 block_reason = chunk.prompt_feedback.block_reason
                 safety_ratings = chunk.prompt_feedback.safety_ratings
                 print(f"[WARN] Nội dung bị chặn: {block_reason}, Ratings: {safety_ratings}")
                 error_msg = f"⚠️ Nội dung có thể không phù hợp hoặc bị chặn bởi bộ lọc an toàn ({block_reason})."
                 # Cập nhật tin nhắn lỗi vào đúng entry
                 chat_history_state[idx][1] = error_msg
                 yield "", chat_history_state, chat_history_state
                 return # Dừng xử lý nếu bị chặn

            txt = getattr(chunk, 'text', '')
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
                # Đôi khi chunk cuối không có text nhưng chứa thông tin khác
                # print(f"[DEBUG] Received empty text chunk: {chunk}")
                pass


        # Sau khi vòng lặp kết thúc, cập nhật tin nhắn cuối cùng không có emoji
        # Kiểm tra lại xem full_text có nội dung không trước khi cập nhật
        if full_text:
             chat_history_state[idx][1] = full_text
        elif not chat_history_state[idx][1].startswith("⚠️"): # Nếu không có text và không phải lỗi chặn
             # Có thể là lỗi khác hoặc không có phản hồi text
             print("[WARN] Không nhận được nội dung text từ API sau khi stream.")
             # Giữ nguyên tin nhắn rỗng hoặc xử lý khác nếu cần
             # chat_history_state[idx][1] = "..." # Ví dụ: hiển thị dấu ba chấm

        # Cập nhật state cuối cùng
        yield "", chat_history_state, chat_history_state

    except Exception as e:
        err = format_api_error(e)
        # Đảm bảo cập nhật lỗi vào đúng entry cuối cùng
        chat_history_state[idx][1] = err
        yield "", chat_history_state, chat_history_state


# --- GIAO DIỆN GRADIO ---
with gr.Blocks(theme=gr.themes.Default(
    # Bạn có thể tuỳ chỉnh thêm theme ở đây nếu muốn
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
            /* Không đặt màu chung ở đây nữa */
        }

        /* --- THAY ĐỔI MÀU SẮC THEO YÊU CẦU --- */

        /* 1. Màu tiêu đề "ZyRa X - tạo bởi Dũng" */
        .gradio-container .prose h2 { /* Nhắm mục tiêu h2 bên trong container */
            color: #CC7F66 !important; /* Màu bạn yêu cầu cho tiêu đề */
            text-align: center; /* Căn giữa tiêu đề cho đẹp */
            margin-bottom: 1rem; /* Thêm khoảng cách dưới tiêu đề */
        }

        /* 2. Màu chữ khi chat (User và Bot) */
        .chatbot .message.user span, /* Chữ trong bong bóng User */
        .chatbot .message.bot span,  /* Chữ trong bong bóng Bot */
        .chatbot .message.user p,    /* Đảm bảo cả thẻ <p> nếu có */
        .chatbot .message.bot p {
            color: #FFB57B !important; /* Màu cam bạn muốn cho chat */
        }

        /* 3. Màu chữ trong ô nhập liệu và nút Gửi */
        .gradio-textbox textarea, /* Chữ khi gõ trong ô input */
        .gradio-button span {     /* Chữ trên nút "Gửi" */
           color: #FFB57B !important; /* Cho đồng bộ màu cam */
        }
        /* Màu chữ placeholder (chữ mờ gợi ý) */
        .gradio-textbox textarea::placeholder {
           color: #FFB57B; /* Màu cam */
           opacity: 0.6; /* Làm mờ đi một chút */
        }

        /* --- CÁC STYLE KHÁC GIỮ NGUYÊN HOẶC TINH CHỈNH --- */

        /* Màu chữ đậm (giữ màu đen để nhấn mạnh) */
        strong, b {
            color: #000000 !important;
        }

        /* Nền trong suốt cho bong bóng chat, ô nhập, nút */
        .chatbot .message.bot,
        .chatbot .message.user,
        .gradio-textbox,
        .gradio-button {
            background-color: transparent !important;
            border: 1px solid #FFDAB9 !important; /* Thêm viền màu cam nhạt cho dễ thấy */
            border-radius: 8px !important; /* Bo góc nhẹ */
        }

        /* Tinh chỉnh riêng cho bong bóng chat để đẹp hơn */
         .chatbot .message {
             border: none !important; /* Bỏ viền ngoài cùng của message */
             padding: 10px 15px !important; /* Tăng padding */
             border-radius: 15px !important; /* Bo góc kiểu tin nhắn */
             box-shadow: 0 1px 3px rgba(0,0,0,0.1); /* Thêm bóng đổ nhẹ */
             max-width: 85%; /* Giới hạn chiều rộng bong bóng */
             word-wrap: break-word; /* Tự xuống dòng */
         }
         .chatbot .message.user {
             background: #FFF0E1 !important; /* Nền hơi khác cho user */
             border-radius: 15px 15px 0 15px !important; /* Bo góc đặc trưng */
             margin-left: auto; /* Đẩy sang phải */
             /* color: #a46a52 !important; */ /* Màu chữ đậm hơn cho user nếu muốn */
         }
         .chatbot .message.bot {
             background: #ffffff !important; /* Nền trắng cho bot */
             border-radius: 15px 15px 15px 0 !important; /* Bo góc đặc trưng */
             margin-right: auto; /* Đẩy sang trái */
         }
         /* Đảm bảo chữ bên trong user/bot vẫn màu cam nếu màu nền thay đổi */
         .chatbot .message.user span, .chatbot .message.user p {
            color: #FFB57B !important;
         }
         .chatbot .message.bot span, .chatbot .message.bot p {
            color: #FFB57B !important;
         }

        /* Căn chỉnh nút xóa */
        #component-8 { /* ID này có thể thay đổi, cần kiểm tra hoặc dùng class */
            margin-top: 10px;
        }

        </style>
    ''')
    # Tiêu đề sử dụng Markdown để tạo thẻ H2
    gr.Markdown("## ZyRa X - tạo bởi Dũng")

    chatbot = gr.Chatbot(
        label="Chatbot",
        height=500,
        bubble_full_width=False,
        # elem_id="chatbot_window" # Thêm id để dễ target CSS nếu cần
        # render_markdown=True # Mặc định là True
    )
    state = gr.State([]) # Khởi tạo state là list rỗng

    with gr.Row():
        txt = gr.Textbox(
            placeholder="Nhập câu hỏi của bạn ở đây...",
            label="Bạn",
            scale=4, # Chiếm nhiều không gian hơn
            # elem_id="user_input"
        )
        btn = gr.Button("Gửi", variant="primary") # Làm nút nổi bật hơn

    clr = gr.Button("🗑️ Xóa cuộc trò chuyện")

    # Kết nối sự kiện
    txt.submit(respond, [txt, state], [txt, chatbot, state])
    btn.click(respond, [txt, state], [txt, chatbot, state])
    # Sửa hàm lambda cho nút xóa để đảm bảo state được reset đúng cách
    clr.click(lambda: (None, [], []), outputs=[txt, chatbot, state], queue=False)

print("Đang khởi chạy Gradio UI...")
# Chạy app
demo.queue().launch(
    server_name='0.0.0.0',
    server_port=int(os.environ.get('PORT', 7860)),
    debug=False, # Tắt debug khi deploy
    # share=True # Bật nếu muốn tạo link public tạm thời
)
print("Gradio UI đã khởi chạy.")
