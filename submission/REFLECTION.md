# Reflection

Anti-pattern nhóm em dễ gặp nhất là **small-files problem**. Khi ingest dữ liệu
theo streaming hoặc micro-batch, mỗi batch nhỏ có thể tạo một file Delta mới.
Kết quả truy vấn vẫn đúng nên vấn đề dễ bị bỏ qua, nhưng chi phí metadata,
object-store request và thời gian lập kế hoạch sẽ tăng rất nhanh khi dữ liệu lớn
lên. Trong NB2, việc tạo nhiều file nhỏ khiến truy vấn chậm hơn rõ rệt; sau
`OPTIMIZE` và `ZORDER BY (user_id)`, số file giảm và tốc độ lọc được cải thiện.

Để tránh lặp lại, nhóm sẽ theo dõi số lượng/kích thước file theo từng partition,
chạy compaction định kỳ cho Silver và Gold, và chỉ dùng Z-ORDER cho các cột thật
sự xuất hiện trong điều kiện lọc phổ biến. Bronze vẫn ưu tiên ghi append để giữ
dữ liệu raw, còn các lớp downstream cần được tối ưu theo workload truy vấn.
