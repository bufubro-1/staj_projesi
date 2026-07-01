"""
CSV dosyalarındaki verileri PostgreSQL'e aktarır.

Kullanım (proje kökünden):
    python database/migrate_csv_to_db.py
    python database/migrate_csv_to_db.py --init-only
    python database/migrate_csv_to_db.py --sirketler master_sirketler.csv
    python database/migrate_csv_to_db.py --yoneticiler yoneticiler_final.csv
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal, init_db, DATABASE_URL
from database.sync import import_sirketler_csv, import_yoneticiler_csv


def main():
    parser = argparse.ArgumentParser(description="CSV verilerini PostgreSQL'e aktar")
    parser.add_argument("--init-only", action="store_true", help="Sadece tabloları oluştur")
    parser.add_argument(
        "--sirketler",
        default="master_sirketler.csv",
        help="Şirket CSV dosyası (varsayılan: master_sirketler.csv)",
    )
    parser.add_argument(
        "--yoneticiler",
        default=None,
        help="Yönetici CSV dosyası (örn. yoneticiler_final.csv)",
    )
    args = parser.parse_args()

    print(f"[*] Veritabanı: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
    init_db()
    print("[+] Tablolar hazır.")

    if args.init_only:
        return

    session = SessionLocal()
    try:
        if os.path.exists(args.sirketler):
            n = import_sirketler_csv(session, args.sirketler)
            print(f"[+] {n} şirket aktarıldı ({args.sirketler})")
        else:
            print(f"[-] Şirket dosyası bulunamadı: {args.sirketler}")

        yonetici_dosyasi = args.yoneticiler
        if yonetici_dosyasi and os.path.exists(yonetici_dosyasi):
            n = import_yoneticiler_csv(session, yonetici_dosyasi)
            print(f"[+] {n} yönetici aktarıldı ({yonetici_dosyasi})")
        elif yonetici_dosyasi:
            print(f"[-] Yönetici dosyası bulunamadı: {yonetici_dosyasi}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
