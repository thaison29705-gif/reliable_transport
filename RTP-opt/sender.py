import sys
import socket
import time
import argparse

from utils import PacketHeader, compute_checksum

PKT_START = 0
PKT_END = 1
PKT_DATA = 2
PKT_ACK = 3

GIOI_HAN_DATA = 1456
HEADER_SIZE = 16
THOI_GIAN_CHO = 0.5  # 500ms


def tao_goi_tin(loai_goi, so_thu_tu, du_lieu=b""):
    if isinstance(du_lieu, str):
        du_lieu = du_lieu.encode('latin1')
    
    do_dai = len(du_lieu)
    hdr_tam = PacketHeader(type=loai_goi, seq_num=so_thu_tu, length=do_dai, checksum=0)
    ma_crc = compute_checksum(bytes(hdr_tam) + du_lieu)
    
    hdr_chuan = PacketHeader(type=loai_goi, seq_num=so_thu_tu, length=do_dai, checksum=ma_crc)
    return bytes(hdr_chuan) + du_lieu


def kiem_tra_goi_nhan(goi_raw):
    if len(goi_raw) < HEADER_SIZE:
        return None, False
        
    thong_tin_hdr = PacketHeader(goi_raw[:HEADER_SIZE])
    if thong_tin_hdr.length < 0 or len(goi_raw) < HEADER_SIZE + thong_tin_hdr.length:
        return None, False
        
    phan_than = goi_raw[HEADER_SIZE : HEADER_SIZE + thong_tin_hdr.length]
    
    crc_nhan_duoc = thong_tin_hdr.checksum
    thong_tin_hdr.checksum = 0
    crc_tinh_lai = compute_checksum(bytes(thong_tin_hdr) + phan_than)
    
    hop_le = (crc_nhan_duoc == crc_tinh_lai)
    return thong_tin_hdr, hop_le


def chay_sender_opt(ip_nhan, port_nhan, kich_thuoc_cua_so):
    dia_chi_dich = (ip_nhan, port_nhan)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    toan_bo_input = sys.stdin.buffer.read()
    danh_sach_doan = []
    vi_tri = 0
    while vi_tri < len(toan_bo_input):
        danh_sach_doan.append(toan_bo_input[vi_tri : vi_tri + GIOI_HAN_DATA])
        vi_tri += GIOI_HAN_DATA
        
    tong_so_goi = len(danh_sach_doan)

    # 1. Bat tay START
    goi_mo_dau = tao_goi_tin(PKT_START, 0)
    sock.sendto(goi_mo_dau, dia_chi_dich)
    
    while True:
        sock.settimeout(THOI_GIAN_CHO)
        try:
            du_lieu_ve, _ = sock.recvfrom(2048)
            hdr_ve, ok = kiem_tra_goi_nhan(du_lieu_ve)
            if ok and hdr_ve.type == PKT_ACK and hdr_ve.seq_num == 1:
                break
        except socket.timeout:
            sock.sendto(goi_mo_dau, dia_chi_dich)

    # 2. Selective Repeat (Part 3)
    left_window = 1
    cur_seq = 1
    acked = set()
    moc_thoi_gian = time.time()

    while left_window <= tong_so_goi:
        while cur_seq < left_window + kich_thuoc_cua_so and cur_seq <= tong_so_goi:
            doan_data = danh_sach_doan[cur_seq - 1]
            goi_data = tao_goi_tin(PKT_DATA, cur_seq, doan_data)
            sock.sendto(goi_data, dia_chi_dich)
            cur_seq += 1

        da_troi_qua = time.time() - moc_thoi_gian
        con_lai = THOI_GIAN_CHO - da_troi_qua

        if con_lai <= 0:
            # Timeout: chi truyen lai cac goi chua nhan duoc ACK trong cua so
            chi_so = left_window
            while chi_so < cur_seq:
                if chi_so not in acked:
                    goi_gui_lai = tao_goi_tin(PKT_DATA, chi_so, danh_sach_doan[chi_so - 1])
                    sock.sendto(goi_gui_lai, dia_chi_dich)
                chi_so += 1
            moc_thoi_gian = time.time()
            continue

        sock.settimeout(con_lai)
        try:
            du_lieu_ve, _ = sock.recvfrom(2048)
            hdr_ve, ok = kiem_tra_goi_nhan(du_lieu_ve)
            
            if ok and hdr_ve.type == PKT_ACK:
                ack_seq = hdr_ve.seq_num
                if left_window <= ack_seq < cur_seq:
                    acked.add(ack_seq)
                    # Dich cua so khi mep trai da duoc ACK
                    window_moved = False
                    while left_window in acked:
                        acked.remove(left_window)
                        left_window += 1
                        window_moved = True
                    if window_moved:
                        moc_thoi_gian = time.time()
        except socket.timeout:
            pass

    # 3. Dong ket noi END
    seq_ket_thuc = tong_so_goi + 1
    goi_dong = tao_goi_tin(PKT_END, seq_ket_thuc)
    sock.sendto(goi_dong, dia_chi_dich)
    
    moc_ket_thuc = time.time()
    while True:
        con_lai = THOI_GIAN_CHO - (time.time() - moc_ket_thuc)
        if con_lai <= 0:
            break
            
        sock.settimeout(con_lai)
        try:
            du_lieu_ve, _ = sock.recvfrom(2048)
            hdr_ve, ok = kiem_tra_goi_nhan(du_lieu_ve)
            if ok and hdr_ve.type == PKT_ACK and hdr_ve.seq_num >= seq_ket_thuc:
                break
        except socket.timeout:
            break

    sock.close()


def main():
    trinh_phan_tich = argparse.ArgumentParser()
    trinh_phan_tich.add_argument("receiver_ip", type=str)
    trinh_phan_tich.add_argument("receiver_port", type=int)
    trinh_phan_tich.add_argument("window_size", type=int)
    tham_so = trinh_phan_tich.parse_args()

    chay_sender_opt(tham_so.receiver_ip, tham_so.receiver_port, tham_so.window_size)


if __name__ == "__main__":
    main()
