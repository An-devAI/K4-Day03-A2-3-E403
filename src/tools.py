"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.

"""

def get_order_status(order_id: str) -> str:
    """
    Tra cứu trạng thái hiện tại của một đơn hàng.
    
    Args:
        order_id (str): Mã đơn hàng (Ví dụ: 'ORD123', 'ORD456')
        
    Returns:
        str: Trạng thái hiện tại của đơn hàng (Đang xử lý, Đang giao, Đã giao...)
    """
    order_upper = order_id.upper()
    if order_upper == "ORD123":
        return f"Đơn hàng {order_upper}: Đã giao thành công vào lúc 10:30 sáng nay."
    elif order_upper == "ORD456":
        return f"Đơn hàng {order_upper}: Đang được giao bởi J&T Express. Dự kiến nhận hàng trong hôm nay."
    elif order_upper == "ORD789":
        return f"Đơn hàng {order_upper}: Đang xử lý tại kho. Chưa bàn giao cho đơn vị vận chuyển."
    else:
        return f"LỖI: Không tìm thấy đơn hàng nào có mã '{order_id}' trong hệ thống."


def get_order_details(order_id: str) -> str:
    """
    Lấy thông tin chi tiết của đơn hàng (Sản phẩm, Số lượng, Tổng tiền).
    
    Args:
        order_id (str): Mã đơn hàng (Ví dụ: 'ORD123')
        
    Returns:
        str: Chi tiết danh sách sản phẩm, tổng tiền và phương thức thanh toán.
    """
    order_upper = order_id.upper()
    if order_upper == "ORD123":
        return (
            f"Chi tiết đơn {order_upper}:\n"
            f"- 1x Áo thun nam Basic (Màu đen, Size L) - Mã: SP001\n"
            f"- 1x Quần Jean form rộng (Màu xanh, Size 32) - Mã: SP002\n"
            f"Tổng tiền: 650,000 VNĐ (Đã thanh toán qua Momo)."
        )
    elif order_upper == "ORD789":
        return (
            f"Chi tiết đơn {order_upper}:\n"
            f"- 1x Giày thể thao nam (Size 42) - Mã: SP003\n"
            f"Tổng tiền: 1,200,000 VNĐ (Thanh toán khi nhận hàng - COD)."
        )
    else:
        return f"LỖI: Không thể lấy chi tiết vì mã đơn hàng '{order_id}' không tồn tại."


def check_return_eligibility(order_id: str, product_id: str) -> str:
    """
    Kiểm tra xem một sản phẩm trong đơn hàng có đủ điều kiện đổi/trả hay không.
    NÊN GỌI hàm này trước khi tạo yêu cầu trả hàng.
    
    Args:
        order_id (str): Mã đơn hàng (Ví dụ: 'ORD123')
        product_id (str): Mã sản phẩm muốn đổi trả (Ví dụ: 'SP001')
        
    Returns:
        str: Trạng thái hợp lệ và số ngày đổi trả còn lại, hoặc lý do từ chối.
    """
    order_upper = order_id.upper()
    prod_upper = product_id.upper()
    
    if order_upper == "ORD123" and prod_upper == "SP001":
        return "HỢP LỆ: Sản phẩm SP001 đủ điều kiện đổi/trả. Khách hàng còn 5 ngày để thực hiện yêu cầu này."
    elif order_upper == "ORD123" and prod_upper == "SP002":
        return "KHÔNG HỢP LỆ: Sản phẩm SP002 thuộc chương trình Sale Flash 80%, không áp dụng chính sách đổi trả."
    else:
        return "LỖI: Không tìm thấy sản phẩm trong đơn hàng hoặc đơn hàng chưa được giao thành công."


def create_return_request(order_id: str, product_id: str, reason: str) -> str:
    """
    Khởi tạo yêu cầu trả hàng - hoàn tiền cho khách hàng.
    
    Args:
        order_id (str): Mã đơn hàng chứa sản phẩm
        product_id (str): Mã sản phẩm khách muốn trả
        reason (str): Lý do trả hàng (Ví dụ: 'Hàng bị rách', 'Giao sai màu')
        
    Returns:
        str: Thông báo tạo yêu cầu thành công kèm Mã yêu cầu đổi trả (Return ID).
    """
    return (
        f"THÀNH CÔNG: Đã tạo yêu cầu trả hàng cho sản phẩm {product_id} (Đơn {order_id}).\n"
        f"Lý do ghi nhận: {reason}.\n"
        f"Mã yêu cầu (Return ID): RET-9988. Vui lòng hướng dẫn khách đóng gói hàng, bưu tá sẽ đến lấy trong 24h."
    )


def cancel_order(order_id: str, reason: str) -> str:
    """
    Thực hiện hủy đơn hàng (Chỉ thành công nếu đơn chưa được giao cho bên vận chuyển).
    
    Args:
        order_id (str): Mã đơn hàng muốn hủy
        reason (str): Lý do hủy đơn
        
    Returns:
        str: Thông báo hủy thành công hoặc lỗi không thể hủy.
    """
    order_upper = order_id.upper()
    if order_upper == "ORD789": # Trạng thái đang xử lý
        return f"THÀNH CÔNG: Đã hủy đơn hàng {order_upper} với lý do '{reason}'. Tiền sẽ được hoàn lại về ví trong 3-5 ngày làm việc."
    else:
        return f"THẤT BẠI: Không thể hủy đơn {order_upper} vì đơn hàng đã được đóng gói hoặc đang trên đường giao."


def lookup_store_policy(query: str) -> str:
    """
    Tra cứu thông tin chính sách của cửa hàng (RAG mô phỏng).
    Dùng để trả lời các câu hỏi chung về quy định đổi trả, phí ship, bảo hành.
    
    Args:
        query (str): Câu hỏi hoặc từ khóa về chính sách (Ví dụ: 'phí đổi trả', 'thời gian bảo hành')
        
    Returns:
        str: Nội dung chính sách trích xuất từ tài liệu nội bộ.
    """
    q_lower = query.lower()
    if "đổi trả" in q_lower or "trả hàng" in q_lower:
        return "CHÍNH SÁCH ĐỔI TRẢ: Cửa hàng hỗ trợ đổi/trả miễn phí trong vòng 7 ngày kể từ khi nhận hàng. Áp dụng cho sản phẩm còn nguyên tem mác. Hàng Sale trên 50% không hỗ trợ đổi trả."
    elif "phí ship" in q_lower or "vận chuyển" in q_lower:
        return "CHÍNH SÁCH VẬN CHUYỂN: Miễn phí giao hàng toàn quốc cho đơn hàng từ 500,000 VNĐ. Dưới 500k, đồng giá phí ship 30,000 VNĐ."
    else:
        return "Tôi không tìm thấy chính sách cụ thể cho câu hỏi này. Vui lòng liên hệ Hotline 1900-xxxx để được hỗ trợ chi tiết."


AVAILABLE_TOOLS = {
    "get_order_status": get_order_status,
    "get_order_details": get_order_details,
    "check_return_eligibility": check_return_eligibility,
    "create_return_request": create_return_request,
    "cancel_order": cancel_order,
    "lookup_store_policy": lookup_store_policy,
}