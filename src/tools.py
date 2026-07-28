"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""

def get_order_status(order_id: str) -> str:
    pass


def get_order_details(order_id: str) -> str:
    pass


def check_return_eligibility(order_id: str, product_id: str) -> str:
    pass


def create_return_request(order_id: str, product_id: str, reason: str) -> str:
    pass


def cancel_order(order_id: str, reason: str) -> str:
    pass


def lookup_store_policy(query: str) -> str:
    pass


AVAILABLE_TOOLS = {
    "get_order_status": get_order_status,
    "get_order_details": get_order_details,
    "check_return_eligibility": check_return_eligibility,
    "create_return_request": create_return_request,
    "cancel_order": cancel_order,
    "lookup_store_policy": lookup_store_policy,
}