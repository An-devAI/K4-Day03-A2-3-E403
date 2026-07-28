"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp AI chỉ bằng cách đổi biến môi trường LLM_PROVIDER.
"""

import os
import re
import sys
import json
import requests
from dotenv import load_dotenv

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho tất cả các LLM Provider"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env!"
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (GPT-4o, GPT-3.5-turbo, etc.)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env!"
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider (Claude 3.5 Sonnet, Claude 3 Haiku)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "claude-3-haiku-20240307"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_anthropic_api_key_here":
            return "[Anthropic Error]: Chưa cấu hình ANTHROPIC_API_KEY trong file .env!"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic Exception]: {str(e)}"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider (Hỗ trợ gọi mọi model qua OpenRouter API)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return "[OpenRouter Error]: Chưa cấu hình OPENROUTER_API_KEY trong file .env!"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"[OpenRouter API Error {res.status_code}]: {res.text}"
        except Exception as e:
            return f"[OpenRouter Exception]: {str(e)}"


class MockProvider(BaseLLMProvider):
    """
    Offline Mock Provider (Cho bài test không cần kết nối API).
    Mô phỏng đúng bối cảnh Đề tài 5: Trợ Lý Tra Cứu Đơn Hàng & Xử Lý Đổi Trả.
    """
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        # Nếu đang chạy trong vòng lặp ReAct (Mốc 3) -> mô phỏng Thought/Action/Final Answer
        if "ReAct Agent" in system_prompt:
            return self._mock_react_step(prompt)

        text = prompt.lower()

        # Ưu tiên 1: Câu hỏi cần DỮ LIỆU HỆ THỐNG (có mã đơn cụ thể hoặc yêu cầu hành động)
        # -> Baseline bó tay. Đây chính là hạn chế cần ghi nhận ở Mốc 2.
        has_order_id = re.search(r"\b(ord|dh)[-_ ]?\d+", text) is not None
        needs_action = any(k in text for k in [
            "đơn hàng của tôi", "hủy đơn", "tạo yêu cầu", "hoàn tiền", "đang ở đâu"
        ])
        if has_order_id or needs_action:
            return (
                "[Mock Baseline] Rất tiếc, mình là chatbot baseline không có quyền truy cập "
                "hệ thống đơn hàng nên không thể kiểm tra trạng thái, tạo yêu cầu đổi trả "
                "hay hủy đơn giúp bạn. Bạn vui lòng cung cấp mã đơn hàng và liên hệ CSKH, "
                "hoặc chờ ReAct Agent (Mốc 3) có tool tra cứu thật."
            )

        # Ưu tiên 2: Câu hỏi CHÍNH SÁCH CHUNG -> Chatbot thuần LLM vẫn trả lời được
        if any(k in text for k in ["chính sách", "đổi trả", "bảo hành", "phí ship", "vận chuyển"]):
            return (
                "[Mock Baseline] Theo hiểu biết chung, cửa hàng thường hỗ trợ đổi/trả trong "
                "khoảng 7 ngày kể từ khi nhận hàng nếu sản phẩm còn nguyên tem mác, và thường "
                "không áp dụng cho hàng sale sâu hoặc sản phẩm đã qua sử dụng. "
                "Tuy nhiên mình chưa thể xác nhận chính sách chính xác vì không có công cụ tra cứu nội bộ."
            )

        return "🤖 [Mock Provider]: Phản hồi giả lập offline cho bài test."

    def _mock_react_step(self, text: str) -> str:
        """
        Mô phỏng 1 bước suy luận ReAct dựa trên scratchpad (Thought/Action/Observation) đã
        tích lũy trong `text`. Dùng để test offline vòng lặp ReAct trong app.py mà không cần
        gọi API thật.
        """
        lower = text.lower()
        obs_matches = re.findall(r"Observation:\s*(.+)", text)
        last_obs = obs_matches[-1] if obs_matches else None
        obs_count = len(obs_matches)

        order_match = re.search(r"\b(ORD|DH)[-_ ]?(\d+)", text, re.IGNORECASE)
        order_id = (order_match.group(1) + order_match.group(2)).upper() if order_match else None
        product_match = re.search(r"\bSP\d+\b", text, re.IGNORECASE)
        product_id = product_match.group(0).upper() if product_match else "SP001"

        wants_return = any(k in lower for k in ["đổi", "trả hàng", "đổi trả", "size", "hoàn tiền"])
        wants_cancel = "hủy" in lower
        wants_policy_only = order_id is None and any(
            k in lower for k in ["chính sách", "bao nhiêu ngày", "trường hợp nào", "phí ship", "vận chuyển", "bảo hành"]
        )

        # Bước đầu tiên (chưa có Observation nào)
        if last_obs is None:
            if wants_policy_only:
                return ("Thought: Đây là câu hỏi về chính sách chung, cần tra cứu tài liệu chính sách nội bộ.\n"
                        "Action: lookup_store_policy['đổi trả']")
            if order_id:
                return (f"Thought: Cần tra cứu trạng thái đơn hàng {order_id} trước khi trả lời.\n"
                        f"Action: get_order_status['{order_id}']")
            return ("Thought: Tôi đã có đủ thông tin để trả lời.\n"
                    "Final Answer: Bạn vui lòng cung cấp mã đơn hàng để mình kiểm tra giúp bạn nhé.")

        # Observation gần nhất báo lỗi/không tìm thấy -> Guardrail: KHÔNG suy đoán, dừng an toàn
        if "lỗi" in last_obs.lower() or "không tìm thấy" in last_obs.lower():
            return ("Thought: Không tìm thấy đơn hàng trong hệ thống nên không thể suy đoán hoặc "
                    "tự ý tạo yêu cầu đổi trả/hủy đơn.\n"
                    f"Final Answer: Xin lỗi, tôi không thể xác minh đơn hàng {order_id or ''} vì không "
                    "tìm thấy trong hệ thống. Bạn vui lòng kiểm tra lại mã đơn hàng giúp mình nhé.")

        # Đã có 1 Observation hợp lệ (vd: trạng thái đơn hàng) -> quyết định bước kế tiếp
        # CHÚ Ý: chỉ đi tiếp sang hủy/đổi trả khi đang trong ngữ cảnh có order_id (đơn hàng cụ thể).
        # Câu hỏi chính sách chung (obs đến từ lookup_store_policy, không có order_id) phải dừng ở đây,
        # tránh việc từ khóa "đổi trả" trong câu hỏi chính sách bị hiểu nhầm thành yêu cầu đổi trả đơn hàng.
        if obs_count == 1:
            if order_id and wants_cancel:
                return (f"Thought: Đơn hàng tồn tại, tiến hành hủy đơn theo yêu cầu của khách.\n"
                        f"Action: cancel_order['{order_id}', 'Khách yêu cầu hủy đơn']")
            if order_id and wants_return:
                return (f"Thought: Đơn hàng đã có trạng thái, giờ kiểm tra điều kiện đổi/trả cho "
                        f"sản phẩm {product_id}.\n"
                        f"Action: check_return_eligibility['{order_id}', '{product_id}']")
            return f"Thought: Tôi đã có đủ thông tin để trả lời.\nFinal Answer: {last_obs}"

        # Đã có 2 Observation (vd: trạng thái đơn hàng + kết quả kiểm tra điều kiện đổi trả)
        if obs_count == 2 and "hợp lệ" in last_obs.lower() and "không hợp lệ" not in last_obs.lower():
            return ("Thought: Sản phẩm đủ điều kiện đổi trả, tôi đã có đủ thông tin để trả lời khách "
                    "và sẽ xin xác nhận trước khi tạo yêu cầu trả hàng thật.\n"
                    f"Final Answer: {last_obs} Bạn xác nhận muốn tạo yêu cầu đổi trả để mình hoàn tất giúp bạn nhé.")

        return f"Thought: Tôi đã có đủ thông tin để trả lời.\nFinal Answer: {last_obs}"


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Factory function tự chọn Provider từ biến môi trường LLM_PROVIDER"""
    name = (provider_name or os.getenv("LLM_PROVIDER") or "mock").lower().strip()
    
    if name == "gemini":
        return GeminiProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "openrouter":
        return OpenRouterProvider()
    else:
        return MockProvider()


if __name__ == "__main__":
    print("=== TEST MULTI-PROVIDER LLM ADAPTER ===")
    provider = get_llm_provider()
    print(f"✅ Provider đang dùng: {provider.__class__.__name__}")
    print(f"🤖 User Query: Hello")
    print(f"💬 Response  : {provider.generate('Hello')}")
