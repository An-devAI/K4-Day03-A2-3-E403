# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `5/5` | Agent cần xác định đơn hàng, kiểm tra trạng thái, đối chiếu chính sách đổi trả rồi mới quyết định hướng xử lý. |
| 🛠️ **Tool Interaction** | `4/5` | Cần truy vấn nhiều hệ thống như Order Database, Logistics API, Return Policy và tạo yêu cầu đổi trả. |
| 🔀 **Dynamic Decision** | `4/5` | Quy trình xử lý thay đổi theo trạng thái đơn hàng (đang giao, đã giao, quá hạn, không đủ điều kiện...). |
| ⏳ **Long Horizon** | `4/5` | Bao gồm nhiều bước liên tiếp: tra cứu → xác minh → đánh giá điều kiện → tạo yêu cầu → thông báo kết quả. |
| **TỔNG ĐIỂM FIT** | **17/20** | **KẾT LUẬN: ** |

---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #3)

**Câu hỏi**: *"Đơn hàng DH10234 của tôi hiện đang ở đâu?"*

### 🤖 Chatbot Baseline:
* **Phản hồi**: *"Chào bạn! Rất tiếc là hiện tại mình chỉ là một chatbot tư vấn thông thường và không thể truy cập vào hệ thống cơ sở dữ liệu nội bộ hay thông tin thời gian thực của cửa hàng được. 

Vì vậy, mình không thể tra cứu giúp bạn tình trạng hiện tại của đơn hàng **DH10234**. 

Để biết chính xác đơn hàng của mình đang ở đâu, bạn vui lòng liên hệ trực tiếp với bộ phận chăm sóc khách hàng của cửa hàng nơi bạn đặt mua, hoặc kiểm tra trên ứng dụng/website mà bạn đã dùng để đặt hàng nhé. 

Chúc bạn một ngày tốt lành và hy vọng bạn sẽ nhận được hàng thật sớm!"*
* **Nhận xét**: An toàn nhưng không giải quyết được nhu cầu thực tế của người dùng.

Câu hỏi: “Đơn hàng DH10234 đã giao chưa? Nếu áo bị rộng thì tôi có thể đổi sang size L không?”

🧠 ReAct Agent
Thought 1: Người dùng có hai yêu cầu: kiểm tra trạng thái đơn hàng và xác minh khả năng đổi áo sang size L. Trước tiên cần tra cứu đơn hàng DH10234.
Action 1: get_order_status['DH10234']
Observation 1: Đơn hàng DH10234 đã được giao ngày 24/07/2026. Sản phẩm: Áo sơ mi size M.
Thought 2: Đơn hàng đã được giao. Tiếp theo cần kiểm tra thời hạn và điều kiện đổi size của sản phẩm.
Action 2: check_return_policy['DH10234', 'Đổi size']
Observation 2: Đơn hàng còn trong thời hạn đổi trả 30 ngày. Áo được phép đổi size nếu chưa qua sử dụng, còn nguyên tem mác và không bị hư hỏng.
Thought 3: Đơn hàng còn thời hạn đổi trả, nhưng cần kiểm tra size L có còn hàng hay không trước khi xác nhận với người dùng.
Action 3: check_product_availability['Áo sơ mi', 'L']
Observation 3: Áo sơ mi size L hiện còn hàng tại kho Hà Nội.
Thought 4: Sản phẩm đủ điều kiện đổi size và size L còn hàng. Có thể thông báo cho người dùng về khả năng đổi sản phẩm.
Final Answer: “Đơn hàng DH10234 đã được giao ngày 24/07/2026. Bạn có thể đổi áo từ size M sang size L vì đơn hàng vẫn còn trong thời hạn đổi trả 30 ngày và size L hiện còn hàng. Sản phẩm cần chưa qua sử dụng, còn nguyên tem mác và không bị hư hỏng.”
Nhận xét: Agent hoàn thành nhiệm vụ nhiều bước bằng cách lần lượt tra cứu trạng thái đơn hàng, kiểm tra chính sách đổi trả và xác minh tồn kho size L.
