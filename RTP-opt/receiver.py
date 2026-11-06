import sys
import socket
import argparse

try:
    from utils import PacketHeader, compute_checksum
except ImportError:
    from util import PacketHeader, compute_checksum

PKT_START = 0
PKT_END = 1
PKT_DATA = 2
PKT_ACK = 3

HEADER_SIZE = 16


def dong_goi_ack(so_seq):
    hdr_tam = PacketHeader(type=PKT_ACK, seq_num=so_seq, length=0, checksum=0)
    ma_crc = compute_checksum(bytes(hdr_tam))
    hdr_chuan = PacketHeader(type=PKT_ACK, seq_num=so_seq, length=0, checksum=ma_crc)
    return bytes(hdr_chuan)


def tach_va_kiem_tra(goi_raw):
    if len(goi_raw) < HEADER_SIZE:
        return None, None, False
        
    hdr = PacketHeader(goi_raw[:HEADER_SIZE])
    if hdr.length < 0 or len(goi_raw) < HEADER_SIZE + hdr.length:
        return None, None, False
        
    noi_dung = goi_raw[HEADER_SIZE : HEADER_SIZE + hdr.length]
    
    crc_cu = hdr.checksum
    hdr.checksum = 0
    crc_moi = compute_checksum(bytes(hdr) + noi_dung)
    
    return hdr, noi_dung, (crc_cu == crc_moi)


def chay_receiver_opt(ip_lang_nghe, port_lang_nghe, kich_thuoc_cua_so):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip_lang_nghe, port_lang_nghe))

    dang_ket_noi = False
    dia_chi_sender = None
    seq_mong_doi = 1
    
    temp_storage = {}

    while True:
        goi_raw, addr_gui = sock.recvfrom(2048)
        hdr, noi_dung, hop_le = tach_va_kiem_tra(goi_raw)

        if not hop_le:
            continue

        # Xu ly goi START
        if hdr.type == PKT_START:
            if not dang_ket_noi:
                dang_ket_noi = True
                dia_chi_sender = addr_gui
                seq_mong_doi = 1
                sock.sendto(dong_goi_ack(1), dia_chi_sender)
            elif addr_gui == dia_chi_sender and seq_mong_doi == 1:
                sock.sendto(dong_goi_ack(1), dia_chi_sender)
            continue

        if not dang_ket_noi or addr_gui != dia_chi_sender:
            continue

        # Xu ly goi DATA theo co che Selective ACK (Part 3)
        if hdr.type == PKT_DATA:
            seq_nhan = hdr.seq_num

            # Bo qua neu seq_num khong hop le hoac vuot qua pham vi cua so
            if seq_nhan < 1 or seq_nhan >= seq_mong_doi + kich_thuoc_cua_so:
                continue

            if seq_nhan >= seq_mong_doi:
                if seq_nhan not in temp_storage:
                    temp_storage[seq_nhan] = noi_dung

                while seq_mong_doi in temp_storage:
                    chunk = temp_storage.pop(seq_mong_doi)
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.flush()
                    seq_mong_doi += 1

            # Nhan goi DATA so nao thi gui tra ACK dung so do
            sock.sendto(dong_goi_ack(seq_nhan), dia_chi_sender)

        # Xu ly goi END
        elif hdr.type == PKT_END:
            if hdr.seq_num == seq_mong_doi:
                sock.sendto(dong_goi_ack(hdr.seq_num), dia_chi_sender)
                break

    sock.close()


def main():
    trinh_phan_tich = argparse.ArgumentParser()
    trinh_phan_tich.add_argument("receiver_ip", type=str)
    trinh_phan_tich.add_argument("receiver_port", type=int)
    trinh_phan_tich.add_argument("window_size", type=int)
    tham_so = trinh_phan_tich.parse_args()

    chay_receiver_opt(tham_so.receiver_ip, tham_so.receiver_port, tham_so.window_size)


if __name__ == "__main__":
    main()
