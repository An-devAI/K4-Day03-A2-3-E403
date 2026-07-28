"""
TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Các tool tra cứu đơn hàng, đổi/trả và chính sách cửa hàng cho ReAct Agent.
"""

import json
import os
from datetime import date
from functools import lru_cache


DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "ecommerce_data.json")


@lru_cache(maxsize=1)
def _load_data() -> dict:
    """Load mock dataset từ config/ecommerce_data.json."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _orders_by_id() -> dict:
    return {order["order_id"].upper(): order for order in _load_data()["orders"]}


def _products_by_id() -> dict:
    return {product["product_id"].upper(): product for product in _load_data()["products"]}


def _format_money(value: int) -> str:
    return f"{value:,.0f} VNĐ".replace(",", ".")


def _get_order(order_id: str):
    return _orders_by_id().get(order_id.upper().strip())


def _get_product(product_id: str):
    return _products_by_id().get(product_id.upper().strip())


def _order_total(order: dict) -> int:
    products = _products_by_id()
    subtotal = 0
    for item in order["items"]:
        product = products.get(item["product_id"].upper())
        if product:
            subtotal += product["price"] * item["quantity"]
    return subtotal + order.get("shipping_fee", 0)


def _find_item(order: dict, product_id: str):
    target = product_id.upper().strip()
    for item in order["items"]:
        if item["product_id"].upper() == target:
            return item
    return None


def get_order_status(order_id: str) -> str:
    """
    Tra cứu trạng thái hiện tại của một đơn hàng.

    Args:
        order_id (str): Mã đơn hàng, ví dụ: ORD123, ORD456, ORD1000.

    Returns:
        str: Trạng thái hiện tại của đơn hàng hoặc chuỗi lỗi nếu không tìm thấy.
    """
    order = _get_order(order_id)
    if not order:
        return f"LỖI: Không tìm thấy đơn hàng nào có mã '{order_id}' trong hệ thống."

    carrier = order.get("carrier") or "chưa có đơn vị vận chuyển"
    delivered = order.get("delivered_date") or "chưa giao"
    return (
        f"Đơn hàng {order['order_id']}: {order['status_text']}. "
        f"Trạng thái nội bộ: {order['status']}. "
        f"Đơn vị vận chuyển: {carrier}. Ngày giao: {delivered}."
    )


def get_order_details(order_id: str) -> str:
    """
    Lấy thông tin chi tiết của đơn hàng: sản phẩm, số lượng, tổng tiền, thanh toán.

    Args:
        order_id (str): Mã đơn hàng, ví dụ: ORD123.

    Returns:
        str: Chi tiết danh sách sản phẩm, tổng tiền và phương thức thanh toán.
    """
    order = _get_order(order_id)
    if not order:
        return f"LỖI: Không thể lấy chi tiết vì mã đơn hàng '{order_id}' không tồn tại."

    products = _products_by_id()
    lines = [f"Chi tiết đơn {order['order_id']} của {order['customer_name']}:"]
    for item in order["items"]:
        product = products.get(item["product_id"].upper())
        if not product:
            lines.append(f"- {item['quantity']}x sản phẩm {item['product_id']} (không tìm thấy metadata)")
            continue
        line_total = product["price"] * item["quantity"]
        lines.append(
            f"- {item['quantity']}x {product['name']} ({product['variant']}) - "
            f"Mã: {product['product_id']} - Thành tiền: {_format_money(line_total)}"
        )

    lines.append(f"Phí vận chuyển: {_format_money(order.get('shipping_fee', 0))}")
    lines.append(f"Tổng tiền: {_format_money(_order_total(order))}")
    lines.append(f"Thanh toán: {order['payment_method']} ({order['payment_status']})")
    return "\n".join(lines)


def check_return_eligibility(order_id: str, product_id: str) -> str:
    """
    Kiểm tra xem một sản phẩm trong đơn hàng có đủ điều kiện đổi/trả hay không.
    Nên gọi hàm này trước khi tạo yêu cầu trả hàng.

    Args:
        order_id (str): Mã đơn hàng, ví dụ: ORD123.
        product_id (str): Mã sản phẩm muốn đổi trả, ví dụ: SP001.

    Returns:
        str: HỢP LỆ kèm số ngày còn lại hoặc lý do từ chối.
    """
    data = _load_data()
    order = _get_order(order_id)
    product = _get_product(product_id)

    if not order:
        return f"LỖI: Không tìm thấy đơn hàng '{order_id}'."
    if not product:
        return f"LỖI: Không tìm thấy sản phẩm '{product_id}'."
    if not _find_item(order, product_id):
        return f"LỖI: Sản phẩm {product_id.upper()} không thuộc đơn hàng {order['order_id']}."
    if order["status"] not in {"delivered", "return_requested"}:
        return "KHÔNG HỢP LỆ: Chỉ hỗ trợ đổi/trả sau khi đơn hàng đã giao thành công."
    if not product.get("returnable", False):
        return f"KHÔNG HỢP LỆ: Sản phẩm {product['product_id']} thuộc nhóm không hỗ trợ đổi/trả."
    if product.get("sale_percent", 0) > 50:
        return f"KHÔNG HỢP LỆ: Sản phẩm {product['product_id']} được sale trên 50%, không áp dụng đổi/trả."

    delivered_date = order.get("delivered_date")
    if not delivered_date:
        return "KHÔNG HỢP LỆ: Đơn hàng chưa có ngày giao thành công."

    return_window = data["metadata"].get("return_window_days", 7)
    days_since_delivery = (date.today() - date.fromisoformat(delivered_date)).days
    remaining_days = return_window - days_since_delivery
    if remaining_days < 0:
        return f"KHÔNG HỢP LỆ: Đơn hàng đã quá hạn đổi/trả {abs(remaining_days)} ngày."

    return (
        f"HỢP LỆ: Sản phẩm {product['product_id']} đủ điều kiện đổi/trả. "
        f"Khách hàng còn {remaining_days} ngày để tạo yêu cầu."
    )


def create_return_request(order_id: str, product_id: str, reason: str) -> str:
    """
    Khởi tạo yêu cầu trả hàng - hoàn tiền cho khách hàng.

    Args:
        order_id (str): Mã đơn hàng chứa sản phẩm.
        product_id (str): Mã sản phẩm khách muốn trả.
        reason (str): Lý do trả hàng.

    Returns:
        str: Thông báo tạo yêu cầu thành công kèm Return ID hoặc lý do từ chối.
    """
    if not reason or not reason.strip():
        return "LỖI: Cần cung cấp lý do trả hàng trước khi tạo yêu cầu."

    eligibility = check_return_eligibility(order_id, product_id)
    if not eligibility.startswith("HỢP LỆ"):
        return f"THẤT BẠI: Chưa thể tạo yêu cầu trả hàng. {eligibility}"

    order = _get_order(order_id)
    return_id = f"RET-{order['order_id'].replace('ORD', '')}-{product_id.upper()}"
    return (
        f"THÀNH CÔNG: Đã tạo yêu cầu trả hàng cho sản phẩm {product_id.upper()} "
        f"(Đơn {order['order_id']}).\n"
        f"Lý do ghi nhận: {reason.strip()}.\n"
        f"Mã yêu cầu (Return ID): {return_id}. Bưu tá sẽ đến lấy hàng trong 24h."
    )


def cancel_order(order_id: str, reason: str) -> str:
    """
    Thực hiện hủy đơn hàng, chỉ thành công nếu đơn chưa giao cho bên vận chuyển.

    Args:
        order_id (str): Mã đơn hàng muốn hủy.
        reason (str): Lý do hủy đơn.

    Returns:
        str: Thông báo hủy thành công hoặc lỗi không thể hủy.
    """
    if not reason or not reason.strip():
        return "LỖI: Cần cung cấp lý do hủy đơn."

    order = _get_order(order_id)
    if not order:
        return f"LỖI: Không tìm thấy đơn hàng '{order_id}'."

    if order["status"] in {"processing", "packed"}:
        refund_note = "Tiền sẽ được hoàn lại trong 3-5 ngày làm việc." if order["payment_status"] == "paid" else "Đơn COD chưa thu tiền nên không cần hoàn tiền."
        return f"THÀNH CÔNG: Đã hủy đơn hàng {order['order_id']} với lý do '{reason.strip()}'. {refund_note}"

    return (
        f"THẤT BẠI: Không thể hủy đơn {order['order_id']} vì trạng thái hiện tại là "
        f"'{order['status_text']}'."
    )


def lookup_store_policy(query: str) -> str:
    """
    Tra cứu thông tin chính sách của cửa hàng.

    Args:
        query (str): Câu hỏi hoặc từ khóa về chính sách.

    Returns:
        str: Nội dung chính sách trích xuất từ dữ liệu nội bộ.
    """
    q_lower = query.lower().strip()
    policies = _load_data()["policies"]

    keyword_map = {
        "doi_tra": ["đổi trả", "trả hàng", "hoàn hàng", "return"],
        "phi_ship": ["phí ship", "vận chuyển", "giao hàng", "ship"],
        "bao_hanh": ["bảo hành", "warranty"],
        "huy_don": ["hủy đơn", "huỷ đơn", "cancel"],
        "hoan_tien": ["hoàn tiền", "refund"],
    }

    for policy_key, keywords in keyword_map.items():
        if any(keyword in q_lower for keyword in keywords):
            return policies[policy_key]

    return "Tôi không tìm thấy chính sách cụ thể cho câu hỏi này. Vui lòng liên hệ Hotline 1900-xxxx để được hỗ trợ chi tiết."


AVAILABLE_TOOLS = {
    "get_order_status": get_order_status,
    "get_order_details": get_order_details,
    "check_return_eligibility": check_return_eligibility,
    "create_return_request": create_return_request,
    "cancel_order": cancel_order,
    "lookup_store_policy": lookup_store_policy,
}