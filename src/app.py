"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.

📌 ĐỀ TÀI SỐ 5: TRỢ LÝ TRA CỨU ĐƠN HÀNG & XỬ LÝ ĐỔI TRẢ
📌 TRẠNG THÁI: Đã hoàn thành tới MỐC 3 (Baseline Chatbot + ReAct Agent Loop + Guardrails).
"""

import json
import os
import re
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")

    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider, verbose: bool = True) -> str:
    """
    🤖 MỐC 2 — Dựng Chatbot gốc (Baseline): CHỈ dùng LLM, KHÔNG có công cụ.

    Mục đích: cho thấy hạn chế của chatbot thuần LLM với đề tài Tra cứu đơn hàng.
    Chatbot này không được phép gọi bất kỳ hàm nào trong AVAILABLE_TOOLS, nên khi
    khách hỏi trạng thái đơn hàng thật (ví dụ ORD123 / DH10234) nó chỉ có thể:
      - nói rằng không tra cứu được, hoặc
      - (nguy hiểm) bịa ra thông tin -> đây chính là hiện tượng ảo giác cần ghi nhận.

    Args:
        user_query (str): Câu hỏi của người dùng.
        provider: LLM Provider lấy từ get_llm_provider().
        verbose (bool): In chi tiết System Prompt hay không.

    Returns:
        str: Nội dung câu trả lời của Chatbot Baseline.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"🚫 Số tool được phép dùng: 0 / {len(AVAILABLE_TOOLS)} (Baseline không có tool)")

    if verbose:
        print("⚙️ System Prompt đang áp dụng (rút gọn):")
        print("   " + CHATBOT_BASELINE_PROMPT.strip().splitlines()[0])

    # Gọi LLM Provider thực hiện sinh câu trả lời (không có bước Action/Observation)
    try:
        response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    except Exception as e:
        response = f"[LỖI GỌI LLM]: {e}"

    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


# Regex nhận dạng từng thành phần trong định dạng ReAct (Role 3 quy định trong prompts.py)
_THOUGHT_RE = re.compile(r"Thought:\s*(.+)")
_ACTION_RE = re.compile(r"Action:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\[(.*)\]")
_FINAL_RE = re.compile(r"Final Answer:\s*(.+)", re.DOTALL)


def _parse_action_args(raw_args: str) -> list:
    """Tách chuỗi tham số trong Action: tool[a, b, c] thành list string đã bỏ dấu nháy/khoảng trắng."""
    raw_args = raw_args.strip()
    if not raw_args:
        return []
    return [part.strip().strip("'\"") for part in raw_args.split(",")]


def _execute_tool(action_name: str, action_args: list) -> str:
    """
    Thực thi tool theo tên LLM chọn. KHÔNG BAO GIỜ để crash cả vòng lặp:
    - Tool không tồn tại trong AVAILABLE_TOOLS -> trả chuỗi lỗi.
    - Tool tồn tại nhưng gọi sai số lượng/loại tham số hoặc raise Exception -> bắt lại, trả chuỗi lỗi.
    """
    tool_fn = AVAILABLE_TOOLS.get(action_name)
    if tool_fn is None:
        return (f"LỖI: Công cụ '{action_name}' không tồn tại trong AVAILABLE_TOOLS. "
                f"Các tool hợp lệ: {', '.join(AVAILABLE_TOOLS.keys())}.")
    try:
        return tool_fn(*action_args)
    except TypeError as e:
        return f"LỖI: Gọi công cụ '{action_name}' sai tham số ({e})."
    except Exception as e:
        return f"LỖI: Công cụ '{action_name}' gặp sự cố khi thực thi ({e})."


def run_react_agent(user_query: str, provider, verbose: bool = True) -> str:
    """
    🧠 MỐC 3 — Vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.

    Mỗi vòng lặp: gọi LLM với REACT_SYSTEM_PROMPT (Role 3) + lịch sử scratchpad hiện tại
    -> parse Thought/Action hoặc Final Answer -> nếu có Action thì thực thi tool tương ứng
    trong AVAILABLE_TOOLS (Role 2) -> nối Observation vào scratchpad -> lặp lại.

    🛡️ Guardrails:
      1. MAX_ITERATIONS: chặn cứng số vòng lặp tối đa (chống lặp vô tận).
      2. Phát hiện Action lặp lại y hệt bước trước -> dừng an toàn (chống agent "đứng hình").
      3. LLM không tuân theo định dạng Thought/Action/Final Answer -> dừng an toàn thay vì đoán mò.
      4. Tool lỗi hoặc không tồn tại -> trả Observation dạng lỗi, KHÔNG làm crash chương trình.

    Args:
        user_query (str): Câu hỏi của người dùng.
        provider: LLM Provider lấy từ get_llm_provider().
        verbose (bool): In chi tiết từng bước Thought/Action/Observation hay không.

    Returns:
        str: Final Answer cuối cùng gửi cho người dùng.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    scratchpad = ""
    seen_actions = set()
    final_answer = None
    step = 0

    while step < MAX_ITERATIONS:
        step += 1
        if verbose:
            print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        llm_input = f"Câu hỏi của người dùng: {user_query}\n{scratchpad}"
        try:
            raw_output = provider.generate(llm_input, system_prompt=REACT_SYSTEM_PROMPT)
        except Exception as e:
            raw_output = f"Final Answer: [LỖI GỌI LLM]: {e}"

        thought_match = _THOUGHT_RE.search(raw_output)
        action_match = _ACTION_RE.search(raw_output)
        final_match = _FINAL_RE.search(raw_output)

        thought = thought_match.group(1).strip() if thought_match else None
        if thought and verbose:
            print(f"🧠 Thought: {thought}")

        # Có Final Answer và KHÔNG có Action mới -> agent đã đủ thông tin, dừng vòng lặp
        if final_match and not action_match:
            final_answer = final_match.group(1).strip()
            print(f"🏁 Final Answer: {final_answer}")
            break

        # LLM không theo định dạng ReAct (không có cả Action lẫn Final Answer) -> Guardrail an toàn
        if not action_match:
            final_answer = raw_output.strip() or (
                "Xin lỗi, tôi chưa thể xử lý yêu cầu này. Bạn vui lòng cung cấp thêm thông tin."
            )
            print("🛡️ GUARDRAIL: LLM không trả về đúng định dạng Thought/Action/Final Answer. Dừng an toàn!")
            print(f"🏁 Final Answer: {final_answer}")
            break

        action_name = action_match.group(1)
        action_args = _parse_action_args(action_match.group(2))
        action_signature = f"{action_name}[{', '.join(action_args)}]"
        print(f"🛠️ Action: {action_signature}")

        # Guardrail chống lặp vô hạn: Action y hệt đã gọi ở bước trước
        if action_signature in seen_actions:
            final_answer = (
                "Xin lỗi, tôi không thể xác minh yêu cầu này sau nhiều lần thử với cùng một hành động. "
                "Vui lòng kiểm tra lại mã đơn hàng/sản phẩm hoặc liên hệ Hotline 1900-xxxx để được hỗ trợ."
            )
            print("🛡️ GUARDRAIL: Phát hiện Action lặp lại y hệt bước trước đó. Dừng an toàn!")
            print(f"🏁 Final Answer: {final_answer}")
            break
        seen_actions.add(action_signature)

        observation = _execute_tool(action_name, action_args)
        print(f"👁️ Observation: {observation}")

        scratchpad += f"Thought: {thought or ''}\nAction: {action_signature}\nObservation: {observation}\n"

    if final_answer is None:
        final_answer = (
            f"Xin lỗi, tôi chưa thể hoàn tất yêu cầu trong giới hạn {MAX_ITERATIONS} bước cho phép. "
            "Vui lòng cung cấp thêm thông tin chính xác (mã đơn hàng/sản phẩm) hoặc liên hệ Hotline 1900-xxxx."
        )
        print(f"\n🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")
        print(f"🏁 Final Answer: {final_answer}")

    return final_answer


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("📦 Đề tài 5: Trợ Lý Tra Cứu Đơn Hàng & Xử Lý Đổi Trả")
    print("==================================================")

    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    print(f"🛠️ Tool Specs của Role 2 đã khai báo: {len(AVAILABLE_TOOLS)} công cụ")
    for name in AVAILABLE_TOOLS:
        print(f"   - {name}")

    tests = load_test_cases()
    print(f"\n✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json")

    # === MỐC 2: CHẠY TOÀN BỘ TEST CASES QUA CHATBOT BASELINE ===
    print("\n=========== 🧪 MỐC 2: DEMO CHATBOT BASELINE ===========")
    for case in tests:
        print("\n" + "-" * 55)
        print(f"📌 Test Case #{case['id']} | {case['category']}")
        run_baseline_chatbot(case["question"], provider)
        print(f"🎯 Kỳ vọng: {case['expected_behavior']}")

    print("\n" + "=" * 55)
    print("📝 KẾT LUẬN MỐC 2: Chatbot Baseline KHÔNG truy cập được dữ liệu đơn hàng thật.")

    # === MỐC 3: CHẠY TOÀN BỘ TEST CASES QUA REACT AGENT ===
    print("\n\n=========== 🧠 MỐC 3: DEMO REACT AGENT (Thought -> Action -> Observation) ===========")
    for case in tests:
        print("\n" + "-" * 55)
        print(f"📌 Test Case #{case['id']} | {case['category']}")
        run_react_agent(case["question"], provider)
        print(f"🎯 Kỳ vọng: {case['expected_behavior']}")

    print("\n" + "=" * 55)
    print("📝 KẾT LUẬN MỐC 3: ReAct Agent gọi tool thật để tra cứu/xử lý, có Guardrail chặn lặp vô tận.")
    print("   ➜ Role 5 hãy trích chuỗi Thought/Action/Observation ở trên dán vào docs/trace_eval.md.")