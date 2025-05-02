# -*- coding: utf-8 -*-
import os
import time
import random
import gradio as gr
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# --- PHẦN API KEY VÀ CẤU HÌNH GENAI (Giữ nguyên key và model gốc của bạn) ---
API_KEY = "AIzaSyAzz9aSguVHcu-Ef_6HeQifwjXIeNURUhM" # Giữ nguyên key của bạn

genai_configured = False
if not API_KEY:
    print("[ERROR] API Key bị thiếu.")
else:
    print("[INFO] API Key được gán trực tiếp trong code.")
    print("Đang cấu hình Google AI...")
    try:
        # Sử dụng key trực tiếp (ít bảo mật hơn)
        genai.configure(api_key=API_KEY)
        genai_configured = True
        print("[OK] Google AI đã được cấu hình thành công.")
    except Exception as e:
        print(f"[ERROR] Không thể cấu hình Google AI: {e}")
        genai_configured = False

# Khôi phục model gốc từ tin nhắn đầu tiên của bạn
MODEL_NAME_CHAT = "gemini-2.5-flash-preview-04-17"
print(f"Sử dụng model chat: {MODEL_NAME_CHAT}")

# --- HÀM format_api_error (Giữ nguyên theo code gốc bạn cung cấp) ---
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
    # Giữ lại các lỗi cụ thể hơn nếu bạn đã thêm vào trước đó
    elif "API_KEY_SERVICE_BLOCKED" in error_message:
         return "❌ Lỗi: API Key đã bị chặn hoặc dịch vụ không khả dụng cho key này."
    elif "USER_LOCATION_INVALID" in error_message:
         return "❌ Lỗi: Khu vực của bạn không được hỗ trợ để sử dụng API này."
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

# --- HÀM respond (Giữ nguyên logic cốt lõi từ code gốc ban đầu của bạn) ---
def respond(message, chat_history_state):
    if not genai_configured:
        error_msg = "❌ Lỗi: Google AI chưa được cấu hình đúng cách. Vui lòng kiểm tra API Key."
        chat_history_state = (chat_history_state or []) + [[message, error_msg]]
        return "", chat_history_state, chat_history_state

    history = []
    if chat_history_state: # Chỉ xử lý nếu chat_history_state không rỗng
        for u, m in chat_history_state:
            # Bỏ qua các tin nhắn lỗi hoặc trống từ user/model
            if u and isinstance(u, str) and u.strip():
                history.append({'role': 'user', 'parts': [u]})
            # Điều chỉnh ở đây: chỉ thêm tin nhắn model không bắt đầu bằng lỗi/cảnh báo
            if m and isinstance(m, str) and m.strip() and not m.startswith("❌") and not m.startswith("⚠️"):
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
        # Sử dụng safety_settings từ code gốc ban đầu của bạn
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        chat = model.start_chat(history=history)
        response = chat.send_message(message, stream=True, safety_settings=safety_settings) # Thêm safety_settings

        for chunk in response:
            # Kiểm tra xem chunk có text không và xử lý lỗi nếu có (logic từ code gốc)
            if hasattr(chunk, 'prompt_feedback') and chunk.prompt_feedback.block_reason:
                 block_reason = chunk.prompt_feedback.block_reason_message # Lấy lý do chi tiết hơn
                 print(f"[WARN] Nội dung bị chặn: {block_reason}")
                 error_msg = f"⚠️ Nội dung có thể không phù hợp hoặc bị chặn bởi bộ lọc an toàn ({block_reason})."
                 chat_history_state[idx][1] = error_msg
                 yield "", chat_history_state, chat_history_state
                 return # Dừng xử lý nếu bị chặn

            # Kiểm tra lỗi trong candidates nếu có (logic từ code gốc)
            if not chunk.candidates:
                print(f"[WARN] Chunk không có candidates: {chunk}")
                if hasattr(chunk, '_error'): # Kiểm tra lỗi ẩn nếu có
                     err = format_api_error(chunk._error)
                     chat_history_state[idx][1] = err
                     yield "", chat_history_state, chat_history_state
                     return
                continue # Bỏ qua chunk rỗng không lỗi
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

            # Lấy text an toàn hơn (logic từ code gốc)
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
        # Chỉ giữ lại lỗi/cảnh báo nếu không có text nào được tạo ra VÀ chưa có lỗi nào được gán
        elif not chat_history_state[idx][1].startswith("⚠️") and not chat_history_state[idx][1].startswith("❌"):
             print("[WARN] Không nhận được nội dung text từ API sau khi stream thành công.")
             # Giữ nguyên tin nhắn rỗng hoặc xử lý khác nếu cần

        # Cập nhật state cuối cùng
        yield "", chat_history_state, chat_history_state

    except Exception as e:
        err = format_api_error(e)
        # Đảm bảo cập nhật lỗi vào đúng entry cuối cùng
        if idx < len(chat_history_state):
            chat_history_state[idx][1] = err
        else: # Trường hợp lỗi xảy ra trước khi entry kịp thêm vào state (ít khả năng)
             # Tạo entry mới với lỗi nếu chưa có
             chat_history_state.append([message, err])
        yield "", chat_history_state, chat_history_state

# --- GIAO DIỆN GRADIO ---
with gr.Blocks(theme=gr.themes.Default()) as demo:
    # --- SỬ DỤNG THẺ <video> VỚI LINK TRỰC TIẾP TỪ CLOUDINARY ---
    gr.HTML('''
        <!-- 1. Thẻ Video làm nền -->
        <video autoplay loop muted playsinline id="background-video">
            <!-- Sử dụng link Cloudinary của bạn ở đây -->
            <source src="https://res.cloudinary.com/dkkv5rtbr/video/upload/v1746203977/3850436-hd_1920_1080_24fps_cw5lzy.mp4" type="video/mp4">
            <!-- Bạn có thể thêm các source khác nếu cần trình duyệt hỗ trợ định dạng khác -->
            <!-- <source src="LINK_DEN_FILE.webm" type="video/webm"> -->
            Trình duyệt của bạn không hỗ trợ thẻ video.
        </video>

        <style>
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@800&display=swap');

        /* --- CSS CHO VIDEO NỀN --- */
        #background-video {
            position: fixed; right: 0; bottom: 0;
            min-width: 100%; min-height: 100%;
            width: auto; height: auto; z-index: -100;
            object-fit: cover; /* Đảm bảo video phủ kín nền */
        }

        /* --- CSS CHO GRADIO UI (Giữ style gốc, điều chỉnh độ mờ/màu sắc) --- */
        /* Nền trong suốt */
        body, .gradio-container { background-color: transparent !important; }

        /* Font chữ */
        * { font-family: 'Nunito', sans-serif !important; }

        /* Tiêu đề */
        .gradio-container .prose h2 {
            color: #CC7F66 !important; /* Màu cam đậm */
            text-align: center; margin-bottom: 1rem;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.4); /* Bóng đổ */
        }

        /* Bong bóng chat */
         .chatbot .message {
             border: none !important; padding: 10px 15px !important; border-radius: 15px !important;
             box-shadow: 0 2px 5px rgba(0,0,0,0.2); max-width: 85%;
             word-wrap: break-word; overflow-wrap: break-word; white-space: pre-wrap;
             backdrop-filter: blur(1px); /* Hiệu ứng mờ nhẹ nền sau bong bóng */
         }
         .chatbot .message.user {
             /* Giữ màu nền gốc của bạn, thêm độ mờ (0.8) */
             background: rgba(255, 240, 225, 0.8) !important; /* #FFF0E1 với alpha 0.8 */
             border-radius: 15px 15px 0 15px !important; margin-left: auto;
         }
         .chatbot .message.bot {
             /* Giữ màu nền gốc của bạn, thêm độ mờ (0.85) */
             background: rgba(255, 255, 255, 0.85) !important; /* #ffffff với alpha 0.85 */
             border-radius: 15px 15px 15px 0 !important; margin-right: auto;
         }
         /* Giữ màu chữ gốc của bạn */
         .chatbot .message.user span, .chatbot .message.user p,
         .chatbot .message.bot span, .chatbot .message.bot p {
             color: #FFB57B !important; /* Màu cam gốc của bạn */
         }

        /* Ô nhập liệu và nút bấm */
        .gradio-textbox, .gradio-button
         {
            /* Nền trắng mờ */
            background-color: rgba(255, 255, 255, 0.75) !important;
             /* Giữ border gốc, thêm độ mờ */
            border: 1px solid rgba(255, 218, 185, 0.6) !important; /* #FFDAB9 với alpha 0.6 */
            border-radius: 8px !important;
            backdrop-filter: blur(2px); /* Mờ nền phía sau rõ hơn */
        }

        /* Màu chữ trong ô nhập liệu và nút (giữ màu gốc) */
        .gradio-textbox textarea, .gradio-button span {
           color: #FFB57B !important;
        }
        .gradio-textbox textarea::placeholder {
           color: #FFB57B; opacity: 0.6;
        }

        /* Style cho LaTeX (giữ màu gốc) */
        .chatbot .message .math-inline .katex,
        .chatbot .message .math-display .katex-display {
            color: #FFB57B !important;
        }

        /* Code blocks (điều chỉnh cho dễ đọc trên nền mờ) */
         .chatbot .message code { white-space: pre-wrap !important; word-wrap: break-word !important; }
         .chatbot .message pre {
             background-color: rgba(50, 50, 50, 0.85) !important; /* Nền tối mờ */
             padding: 12px !important; border-radius: 6px !important;
             box-shadow: inset 0 0 6px rgba(0,0,0,0.25); border: none !important;
         }
         .chatbot .message pre code {
             display: block; overflow-x: auto; color: #f2f2f2 !important; /* Chữ sáng */
             background-color: transparent !important; padding: 0 !important;
         }

        /* Hover effect cho nút */
        .gradio-button:hover {
             background-color: rgba(255, 255, 255, 0.9) !important; /* Sáng hơn khi hover */
             border-color: rgba(255, 218, 185, 0.9) !important; /* Border rõ hơn khi hover */
             box-shadow: 0 3px 7px rgba(0,0,0,0.2);
        }
        /* Nút xóa */
        #component-8 { margin-top: 10px; } /* ID mặc định cho button cuối cùng, có thể cần điều chỉnh */

        </style>
    ''')
    # Tiêu đề
    gr.Markdown("## ZyRa X - tạo bởi Dũng")

    chatbot = gr.Chatbot(
        label="Chatbot",
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
            placeholder="Nhập câu hỏi của bạn ở đây...",
            label="Bạn",
            scale=4,
            # elem_id="user_input" # Bỏ nếu không cần thiết
        )
        btn = gr.Button("Gửi", variant="primary", scale=1) # Giữ scale=1

    # Nút xóa, kiểm tra lại ID nếu cần style riêng
    clr = gr.Button("🗑️ Xóa cuộc trò chuyện") # Có thể có ID là component-8 hoặc khác

    # Kết nối sự kiện (Giữ nguyên)
    txt.submit(respond, [txt, state], [txt, chatbot, state])
    btn.click(respond, [txt, state], [txt, chatbot, state])
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
