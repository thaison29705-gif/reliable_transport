# Reliable Transport Protocol (RTP)
Project 4: Reliable Transport

## Sinh viên thực hiện
- **Họ và tên**: Nguyễn Thái Sơn
- **Mã sinh viên**: 24020631

---

## Cấu trúc bài nộp

```text
.
├── RTP-base/
│   ├── receiver.py   # Receiver sử dụng cơ chế Cumulative ACK (Go-Back-N)
│   ├── sender.py     # Sender sử dụng cơ chế Cumulative ACK
│   └── utils.py      # Định nghĩa PacketHeader và tính CRC32
├── RTP-opt/
│   ├── receiver.py   # Receiver tối ưu sử dụng cơ chế Selective ACK
│   ├── sender.py     # Sender tối ưu chỉ gửi lại các gói chưa ACK
│   └── utils.py      # Định nghĩa PacketHeader và tính CRC32
└── test_scripts/     # Bộ công cụ giả lập lỗi mạng và kiểm tra tự động
    ├── compare.sh
    ├── proxy.py
    ├── test.sh
    └── test_message.txt
```

---

## Hướng dẫn chạy thử nghiệm
Chạy trên môi trường Linux / WSL:

```bash
# Kiểm tra phần 1 & 2 (RTP-base)
./test_scripts/test.sh RTP-base

# Kiểm tra phần 3 (RTP-opt)
./test_scripts/test.sh RTP-opt
```
