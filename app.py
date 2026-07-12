"""Thuận AI All-in-One: Xưởng Content + Chat AI tìm kiếm web."""

import os
from pathlib import Path
from typing import Any

import anthropic
from flask import Flask, jsonify, render_template, request
from anthropic import Anthropic

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
MAX_HISTORY_MESSAGES = 16
MAX_QUERY_LENGTH = 4000

PLATFORM_GUIDANCE = {
    "facebook": "Ngắn gọn, gần gũi, có emoji vừa phải, kết thúc bằng câu hỏi hoặc CTA rõ ràng.",
    "instagram": "Ngắn, giàu cảm xúc, dùng hashtag liên quan ở cuối (5-8 hashtag), giọng trẻ trung.",
    "tiktok": "Kịch bản video ngắn 15-30 giây: hook mở đầu 3 giây, nội dung chính, CTA cuối.",
    "blog": "Có cấu trúc rõ ràng, văn phong mạch lạc và thân thiện với SEO.",
    "email": "Có tiêu đề hấp dẫn, mở đầu cá nhân hóa, nội dung ngắn gọn và CTA rõ ràng.",
    "linkedin": "Chuyên nghiệp, có insight hoặc số liệu, giọng điệu đáng tin cậy.",
}
TYPE_LABELS = {"caption": "caption", "article": "bài viết", "script": "kịch bản video", "email_body": "nội dung email"}
TONE_GUIDANCE = {
    "friendly": "thân thiện, gần gũi như đang trò chuyện",
    "professional": "chuyên nghiệp, đáng tin cậy",
    "playful": "vui tươi, hài hước, năng lượng cao",
    "luxury": "sang trọng, tinh tế, đẳng cấp",
    "urgent": "khẩn cấp, tạo cảm giác cấp bách",
}
LENGTH_GUIDANCE = {
    "short": "rất ngắn gọn, tối đa 3-4 câu",
    "medium": "độ dài vừa phải, khoảng 150-250 từ",
    "long": "chi tiết, đầy đủ, khoảng 500-800 từ",
}

def anthropic_client() -> Anthropic:
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Chưa cấu hình ANTHROPIC_API_KEY trên Vercel.")
    return Anthropic(api_key=key)

def build_prompt(topic: str, platform: str, content_type: str, tone: str, length: str, context: str) -> str:
    context_line = f"- Bối cảnh thêm: {context}" if context else ""
    return f"""Bạn là chuyên gia content marketing. Hãy viết {TYPE_LABELS.get(content_type, content_type)} về chủ đề sau:

CHỦ ĐỀ: {topic}

YÊU CẦU:
- Nền tảng: {platform} — {PLATFORM_GUIDANCE.get(platform, "")}
- Giọng điệu: {TONE_GUIDANCE.get(tone, tone)}
- Độ dài: {LENGTH_GUIDANCE.get(length, length)}
- Ngôn ngữ: Tiếng Việt
{context_line}

Chỉ trả về nội dung content, không giải thích thêm, không dùng markdown backticks."""

def search_web(query: str) -> list[dict[str, str]]:
    """Web search is disabled in this build; Claude chat still works normally."""
    return []

def normalize_history(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return []
    cleaned = []
    for item in raw[-MAX_HISTORY_MESSAGES:]:
        if isinstance(item, dict):
            role = item.get("role")
            content = str(item.get("content", "")).strip()
            if role in {"user", "assistant"} and content:
                cleaned.append({"role": role, "content": content[:8000]})
    return cleaned

def source_context(sources: list[dict[str, str]]) -> str:
    return ""

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/content")
def content_page():
    return render_template("content.html")

@app.get("/chat")
def chat_page():
    return render_template("chat.html")

@app.get("/health")
def health():
    return jsonify({"status": "ok", "model": MODEL, "templates": True})

@app.post("/api/generate")
def generate():
    data = request.get_json(silent=True) or {}
    topic = str(data.get("topic") or "").strip()
    if not topic:
        return jsonify({"error": "Thiếu chủ đề. Nhập chủ đề trước khi tạo nội dung."}), 400
    try:
        response = anthropic_client().messages.create(
            model=MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": build_prompt(
                topic,
                str(data.get("platform") or "facebook"),
                str(data.get("type") or "caption"),
                str(data.get("tone") or "friendly"),
                str(data.get("length") or "medium"),
                str(data.get("context") or "").strip(),
            )}],
        )
        result = "\n".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        ).strip()
        return jsonify({"result": result or "Claude chưa trả về nội dung."})
    except anthropic.AuthenticationError:
        return jsonify({"error": "API key Anthropic không hợp lệ."}), 500
    except anthropic.RateLimitError:
        return jsonify({"error": "Anthropic đang giới hạn lượt dùng hoặc tài khoản hết hạn mức."}), 429
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": f"Lỗi máy chủ: {exc}"}), 500

@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    use_web = bool(data.get("use_web", False))
    history = normalize_history(data.get("history"))
    if not message:
        return jsonify({"error": "Bạn chưa nhập câu hỏi."}), 400
    if len(message) > MAX_QUERY_LENGTH:
        return jsonify({"error": "Câu hỏi quá dài. Hãy rút gọn dưới 4.000 ký tự."}), 400
    try:
        sources = []
        final_user_message = message
        web_notice = ""
        if use_web:
            web_notice = "Tính năng tìm kiếm web hiện đang tắt vì chưa cấu hình dịch vụ tìm kiếm. Claude sẽ trả lời bằng kiến thức sẵn có."
        response = anthropic_client().messages.create(
            model=MODEL,
            max_tokens=2200,
            system="Bạn là trợ lý AI hữu ích, trả lời bằng tiếng Việt rõ ràng. Không bịa thông tin.",
            messages=history + [{"role": "user", "content": final_user_message}],
        )
        answer = "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        ).strip()
        return jsonify({
            "answer": answer or "Mình chưa tạo được câu trả lời.",
            "sources": [],
            "web_used": False,
            "notice": web_notice,
        })
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:
        return jsonify({"error": f"Lỗi hệ thống: {exc}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
