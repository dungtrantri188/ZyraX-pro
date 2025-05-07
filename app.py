# -*- coding: utf-8 -*-
# CẢNH BÁO CỰC KỲ QUAN TRỌNG: VIỆC NHÚNG API KEY TRỰC TIẾP VÀO CODE LÀ KHÔNG AN TOÀN!
# CHỈ LÀM VẬY CHO MỤC ĐÍCH THỬ NGHIỆM CÁ NHÂN VÀ KHÔNG CHIA SẺ CODE NÀY CÔNG KHAI.

import os
import time
import random
import gradio as gr
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import re # Thư viện regex vẫn giữ lại phòng trường hợp cần dùng sau này

# --- PHẦN API KEY VÀ CẤU HÌNH GENAI ---
# THAY THẾ "PASTE_YOUR_ACTUAL_API_KEY_HERE" BẰNG API KEY THẬT CỦA BẠN
API_KEY = "PASTE_YOUR_ACTUAL_API_KEY_HERE"
# CẢNH BÁO: ĐÂY LÀ NƠI API KEY CỦA BẠN ĐANG ĐƯỢC HIỂN THỊ TRONG CODE

genai_configured = False
if not API_KEY or API_KEY == "AIzaSyCFCj6v8hD49BICKhnHLEpP5o_Wn7hrJgg":
    print("[ERROR] API Key bị thiếu hoặc chưa được thay thế.")
else:
    print("[INFO] API Key được gán trực tiếp trong code.")
    print("Đang cấu hình Google AI...")
    try:
        # Sử dụng genai.configure để thiết lập API Key - Đây là cách chuẩn hiện tại
        genai.configure(api_key=API_KEY)
        genai_configured = True
        print("[OK] Google AI đã được cấu hình thành công.")
    except Exception as e:
        print(f"[ERROR] Không thể cấu hình Google AI: {e}")
        genai_configured = False

# Sử dụng model chat mới nhất hoặc theo yêu cầu
MODEL_NAME_CHAT = "gemini-2.5-flash-latest" # Sử dụng latest để tự động cập nhật
print(f"Sử dụng model chat: {MODEL_NAME_CHAT}")

# --- HÀM format_api_error (Giữ nguyên) ---
# Lưu ý: Hàm này vẫn chứa một số câu chữ có thể hơi "gắt" theo phong cách cũ.
def format_api_error(e):
    error_message = str(e)
    error_type = type(e).__name__
    print(f"[ERROR] Lỗi khi gọi API: {error_type} - {error_message}")

    if isinstance(e, google_exceptions.PermissionDenied):
        if "API key not valid" in error_message or "API_KEY_INVALID" in error_message:
            return "❌ Lỗi: API Key được cấu hình nhưng Google từ chối khi sử dụng (API_KEY_INVALID). Hmph! Kiểm tra lại đi!"
        elif "permission to access model" in error_message:
             return f"❌ Lỗi: Hả?! Tôi không được phép dùng model '{MODEL_NAME_CHAT}' này à? Phiền phức thật..."
        else:
            return f"❌ Lỗi: Từ chối quyền truy cập (PermissionDenied): {error_message} ... Tch!"
    elif isinstance(e, google_exceptions.InvalidArgument) and "API key not valid" in error_message:
        return "❌ Lỗi: API Key không hợp lệ (InvalidArgument). Baka! Nhập key cho đúng vào!"
    elif isinstance(e, google_exceptions.NotFound):
         return f"❌ Lỗi: Không tìm thấy model '{MODEL_NAME_CHAT}'. Cậu chắc là nó tồn tại không đấy?!"
    elif isinstance(e, google_exceptions.ResourceExhausted):
        return "❌ Lỗi: Hết quota rồi! Đợi đi hoặc kiểm tra lại giới hạn xem nào! Mou~"
    elif isinstance(e, google_exceptions.DeadlineExceeded):
        return "❌ Lỗi: Yêu cầu mất thời gian quá! Thử lại sau đi! Chậm chạp!"
    else:
        return f"❌ Lỗi không xác định khi gọi AI ({error_type}): {error_message} ... Chả hiểu sao nữa."

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

# --- HÀM respond (Đã cập nhật để loại bỏ tích hợp tính cách và thinking_config) ---
def respond(message, chat_history_state):
    if not genai_configured:
        error_msg = "❌ Lỗi: Google AI chưa được cấu hình đúng cách. Hmph! Kiểm tra lại API Key đi!"
        chat_history_state = (chat_history_state or []) + [[message, error_msg]]
        yield "", chat_history_state, chat_history_state # Yield để cập nhật UI
        return

    if not message or message.strip() == "":
        no_input_responses = [
            "Này! Định hỏi gì thì nói đi chứ?",
            "Im lặng thế? Tính làm gì?",
            "Hửm? Sao không nói gì hết vậy?",
            "Baka! Có gì thì nhập vào đi chứ!",
            "Đừng có nhìn tôi chằm chằm như thế! Hỏi gì thì hỏi đi!"
        ]
        response_text = random.choice(no_input_responses)
        chat_history_state = (chat_history_state or []) + [[message, response_text]]
        yield "", chat_history_state, chat_history_state # Yield để cập nhật UI
        return

    # Xây dựng lịch sử chat cho API (Giữ nguyên logic lọc)
    history = []
    if chat_history_state:
        for u, m in chat_history_state:
            is_error = m and isinstance(m, str) and (m.startswith("❌") or m.startswith("⚠️"))
            is_no_input_response = u is None or (isinstance(u,str) and u.strip() == "")

            if u and isinstance(u, str) and u.strip() and not is_no_input_response:
                 history.append({'role': 'user', 'parts': [u]})
            # Chỉ thêm phản hồi của model nếu nó không phải là lỗi/cảnh báo và không phải phản hồi rỗng
            if m and isinstance(m, str) and m.strip() and not is_error and not is_no_input_response:
                 history.append({'role': 'model', 'parts': [m]})

    # Thêm tin nhắn mới của người dùng vào cuối lịch sử hiển thị
    current_chat_entry = [message, ""]
    chat_history_state = (chat_history_state or []) + [current_chat_entry]
    idx = len(chat_history_state) - 1

    full_text = ""
    char_count = 0
    emoji_idx = 0
    is_error_or_warning = False # Cờ để kiểm tra lỗi/cảnh báo

    try:
        print(f"[DEBUG] Sending history to API: {history}")
        model = genai.GenerativeModel(MODEL_NAME_CHAT)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        # Bắt đầu chat với lịch sử đã xây dựng
        chat = model.start_chat(history=history)
        # Gửi tin nhắn mới của người dùng, bật stream, áp dụng safety settings
        # Đã bỏ tham số 'config' bao gồm 'thinking_config' vì không hỗ trợ ở đây
        response = chat.send_message(message, stream=True, safety_settings=safety_settings)

        for chunk in response:
            # Kiểm tra chặn prompt (Giữ nguyên logic xử lý lỗi)
            if hasattr(chunk, 'prompt_feedback') and chunk.prompt_feedback.block_reason:
                block_reason = chunk.prompt_feedback.block_reason_message
                print(f"[WARN] Nội dung prompt bị chặn: {block_reason}")
                error_msg = f"⚠️ Hả?! Cậu hỏi cái gì mà bị chặn thế này ({block_reason})?! Nói năng cẩn thận vào!"
                chat_history_state[idx][1] = error_msg
                is_error_or_warning = True
                yield "", chat_history_state, chat_history_state
                return

            if not chunk.candidates:
                print(f"[WARN] Chunk không có candidates: {chunk}")
                continue

            candidate = chunk.candidates[0]
            # Sử dụng getattr an toàn hơn để lấy finish_reason
            finish_reason_value = getattr(getattr(candidate, 'finish_reason', None), 'value', None)

            # Kiểm tra chặn nội dung trả về (SAFETY) (Giữ nguyên logic xử lý lỗi)
            if finish_reason_value == 3: # 3 = SAFETY
                safety_ratings_str = ""
                if hasattr(candidate, 'safety_ratings'):
                    ratings_str_list = [f"{r.category.name}: {r.probability.name}" for r in candidate.safety_ratings if r.probability.name != 'NEGLIGIBLE']
                    if ratings_str_list:
                        safety_ratings_str = f" (Lý do: {', '.join(ratings_str_list)})"
                print(f"[WARN] Stream bị chặn do an toàn.{safety_ratings_str}")
                error_msg = f"⚠️ Tch! Tôi định nói... nhưng mà bị chặn mất rồi!{safety_ratings_str} Chắc tại cậu hỏi linh tinh đấy!"
                chat_history_state[idx][1] = error_msg
                is_error_or_warning = True
                yield "", chat_history_state, chat_history_state
                return

            # Kiểm tra các lý do kết thúc khác (Giữ nguyên logic xử lý lỗi)
            if finish_reason_value is not None and finish_reason_value not in (0, 1): # 0=UNSPECIFIED, 1=STOP
                reason_name = getattr(getattr(candidate, 'finish_reason', None), 'name', 'UNKNOWN')
                reason_msg = f"Lý do kết thúc: {reason_name}"
                print(f"[WARN] Stream kết thúc sớm. {reason_msg}")
                error_extra = ""
                if finish_reason_value == 2: # MAX_TOKENS
                    error_extra = "⚠️ Nói dài quá, hết token rồi! Tóm lại là thế đấy!"
                elif finish_reason_value == 4: # RECITATION
                    error_extra = "⚠️ Bị chặn vì trích dẫn nguồn! Phiền phức!"
                else: # OTHER
                    error_extra = f"⚠️ Bị dừng giữa chừng vì... {reason_msg}! Chả hiểu kiểu gì!"

                chat_history_state[idx][1] = full_text + "\n" + error_extra
                is_error_or_warning = True
                yield "", chat_history_state, chat_history_state
                return

            # Lấy text an toàn hơn (Giữ nguyên)
            txt = ""
            if chunk.parts:
                txt = "".join(part.text for part in chunk.parts if hasattr(part, 'text'))

            # Stream text và emoji (Giữ nguyên)
            if txt:
                for ch in txt:
                    full_text += ch
                    char_count += 1
                    time.sleep(0.02 / 1.5) # Giữ tốc độ stream
                    if char_count % 2 == 0:
                        emoji_idx += 1
                    current_emoji = LARGE_CYCLING_EMOJIS[emoji_idx % len(LARGE_CYCLING_EMOJIS)]
                    chat_history_state[idx][1] = full_text + f" {current_emoji}"
                    yield "", chat_history_state, chat_history_state
            else:
                pass # Bỏ qua chunk rỗng

        # --- XỬ LÝ PHẢN HỒI CUỐI CÙNG SAU KHI STREAM ---
        if not is_error_or_warning and full_text:
            chat_history_state[idx][1] = full_text
        elif not is_error_or_warning and not full_text:
            empty_responses = [
                "Hửm? Chả nghĩ ra gì cả.",
                "... Im lặng là vàng.",
                "Tôi... không biết nói gì hết.",
                "Cậu hỏi cái gì lạ thế?",
                "..."
            ]
            chat_history_state[idx][1] = random.choice(empty_responses)
        # Nếu có lỗi/cảnh báo thì giữ nguyên thông báo lỗi đã gán trước đó

        # Cập nhật state cuối cùng (loại bỏ emoji nếu còn) (Giữ nguyên)
        final_text = chat_history_state[idx][1]
        # Kiểm tra xem có emoji ở cuối không trước khi cắt
        if final_text and len(final_text) > 1 and final_text[-1] in LARGE_CYCLING_EMOJIS:
             # Tìm vị trí khoảng trắng cuối cùng trước emoji
             space_before_emoji_idx = final_text[:-1].rfind(' ')
             if space_before_emoji_idx != -1:
                 final_text = final_text[:space_before_emoji_idx]
             else:
                 # Trường hợp không có khoảng trắng trước emoji (ít xảy ra)
                 final_text = final_text[:-1] # Cắt bỏ mỗi emoji

        chat_history_state[idx][1] = final_text

        yield "", chat_history_state, chat_history_state
        # ----------------------------------------------------

    except Exception as e:
        err = format_api_error(e) # Hàm format_api_error vẫn giữ giọng điệu cũ
        chat_history_state[idx][1] = err
        yield "", chat_history_state, chat_history_state


# --- GIAO DIỆN GRADIO (Giữ nguyên CSS và cấu trúc) ---
with gr.Blocks(theme=gr.themes.Default(
    # primary_hue=gr.themes.colors.orange,
    # secondary_hue=gr.themes.colors.brown,
)) as demo:
    # --- CSS ĐÃ CẬP NHẬT (Giữ nguyên như bạn cung cấp) ---
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
            color: #8B4513 !important; /* Đổi sang màu nâu đậm hơn cho dễ đọc */
        }
        /* Màu chữ cho phần bị chặn/lỗi */
        .chatbot .message.bot span:first-child:contains("❌"),
        .chatbot .message.bot span:first-child:contains("⚠️") {
             color: #D2691E !important; /* Màu cam đậm cho lỗi/cảnh báo */
             font-weight: bold;
        }


        /* 3. Màu chữ trong ô nhập liệu và nút Gửi */
        .gradio-textbox textarea,
        .gradio-button span {
           color: #8B4513 !important; /* Đồng bộ màu nâu đậm */
        }
        .gradio-textbox textarea::placeholder {
           color: #A0522D; /* Màu nâu nhạt hơn cho placeholder */
           opacity: 0.7;
        }

        /* --- CÁC STYLE KHÁC GIỮ NGUYÊN HOẶC TINH CHỈNH --- */
        strong, b { color: #000000 !important; }
        .chatbot .message.bot,
        .chatbot .message.user {
            border: 1px solid #FFDAB9 !important; /* Giữ viền màu đào nhạt */
            border-radius: 15px !important; /* Giữ bo tròn */
            padding: 10px 15px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            max-width: 85%;
            word-wrap: break-word;
            overflow-wrap: break-word;
            white-space: pre-wrap;
            margin-bottom: 8px; /* Thêm khoảng cách giữa các tin nhắn */
        }
         .chatbot .message.user {
             background: #FFF5E1 !important; /* Màu nền vàng kem nhạt cho user */
             border-radius: 15px 15px 0 15px !important; /* Bo góc khác nhau */
             margin-left: auto;
             margin-right: 10px; /* Thêm margin để không sát cạnh phải */
         }
         .chatbot .message.bot {
             background: #ffffff !important; /* Màu nền trắng cho bot */
             border-radius: 15px 15px 15px 0 !important; /* Bo góc khác nhau */
             margin-right: auto;
             margin-left: 10px; /* Thêm margin để không sát cạnh trái */
         }

        /* Style cho LaTeX (do KaTeX/MathJax render) */
        .chatbot .message .math-inline .katex, /* Inline math */
        .chatbot .message .math-display .katex-display { /* Display math */
            color: #8B4513 !important; /* Áp dụng màu nâu đậm cho LaTeX */
        }
        /* Đảm bảo code blocks cũng xuống dòng */
        .chatbot .message code {
             white-space: pre-wrap !important;
             word-wrap: break-word !important;
             background-color: #f0f0f0; /* Thêm nền nhẹ cho code */
             padding: 2px 4px;
             border-radius: 4px;
             color: #333; /* Màu chữ tối hơn cho code */
        }
        .chatbot .message pre { /* Style cho khối code ``` */
             background-color: #f0f0f0 !important;
             padding: 10px !important;
             border-radius: 5px !important;
             border: 1px solid #ddd !important;
             overflow-x: auto; /* Thêm thanh cuộn ngang nếu code quá dài */
        }
        .chatbot .message pre code {
             background-color: transparent !important; /* Bỏ nền riêng của code trong pre */
             padding: 0 !important;
             border-radius: 0 !important;
             border: none !important;
             color: #333 !important; /* Màu chữ tối hơn cho code */
        }

        #component-8 { margin-top: 10px; } /* ID này có thể thay đổi, cần kiểm tra */
        .gradio-button {
            background-color: #FFDAB9 !important; /* Nền màu đào nhạt cho nút */
            border: 1px solid #CC7F66 !important; /* Viền nâu đỏ */
        }
         .gradio-button:hover {
            background-color: #FFCFAF !important; /* Sáng hơn khi hover */
            box-shadow: 0 2px 4px rgba(0,0,0,0.15);
        }
        </style>
    ''')
    # Tiêu đề sử dụng Markdown
    gr.Markdown("## ZyraX - tạo bởi Dũng ") # Giữ nguyên tiêu đề

    chatbot = gr.Chatbot(
        label="Cuộc trò chuyện", # Giữ nguyên label
        height=500,
        bubble_full_width=False,
        latex_delimiters=[
            {"left": "$$", "right": "$$", "display": True},
            {"left": "$", "right": "$", "display": False},
            {"left": "\\(", "right": "\\)", "display": False},
            {"left": "\\[", "right": "\\]", "display": True}
        ]
    )
    state = gr.State([]) # Khởi tạo state là list rỗng

    with gr.Row():
        txt = gr.Textbox(
            placeholder="Hỏi tôi điều gì đó...", # Thay đổi placeholder cho trung lập hơn
            label="Bạn",
            scale=4,
        )
        btn = gr.Button("Gửi", variant="primary") # Thay đổi text nút cho trung lập hơn

    clr = gr.Button("🗑️ Xóa cuộc trò chuyện") # Thay đổi text nút xóa cho trung lập hơn

    # Kết nối sự kiện (giữ nguyên)
    txt.submit(respond, [txt, state], [txt, chatbot, state])
    btn.click(respond, [txt, state], [txt, chatbot, state])
    clr.click(lambda: (None, [], []), outputs=[txt, chatbot, state], queue=False)

print("Đang khởi chạy Gradio UI...")
# Chạy app (Giữ nguyên)
demo.queue().launch(
    server_name='0.0.0.0',
    server_port=int(os.environ.get('PORT', 7860)),
    debug=False,
)
print("Gradio UI đã khởi chạy.")
