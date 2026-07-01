import csv
from typing import Optional

from sqlalchemy.orm import Session
from database.models import Sirket, Kisi


def _normalize_domain(domain):
    if not domain or not str(domain).strip():
        return None
    return str(domain).strip().lower()


def _normalize_email(email):
    if not email:
        return None
    email = str(email).strip()
    if email.endswith("(Tahmini)"):
        return email
    return email or None


def _find_sirket(session: Session, ad: str, domain: Optional[str]) -> Optional[Sirket]:
    if domain:
        sirket = session.query(Sirket).filter(Sirket.domain == domain).first()
        if sirket:
            return sirket

    if ad:
        return session.query(Sirket).filter(Sirket.ad == ad).first()
    return None


def upsert_sirket(session: Session, row: dict) -> Sirket:
    domain = _normalize_domain(row.get("domain"))
    ad = (row.get("ad") or "").strip()
    kaynak = (row.get("kaynak") or "").strip() or None
    email = _normalize_email(row.get("email") or row.get("genel_email"))
    telefon = (row.get("telefon") or "").strip() or None
    sehir = (row.get("sehir") or "").strip() or None

    sirket = _find_sirket(session, ad, domain)
    if sirket:
        sirket.ad = ad or sirket.ad
        sirket.domain = domain or sirket.domain
        sirket.kaynak = kaynak or sirket.kaynak
        if email:
            sirket.genel_email = email
        if telefon:
            sirket.telefon = telefon
        if sehir:
            sirket.sehir = sehir
        return sirket

    sirket = Sirket(
        ad=ad,
        domain=domain,
        genel_email=email,
        telefon=telefon,
        sehir=sehir,
        kaynak=kaynak,
        sektor="lojistik",
    )
    session.add(sirket)
    return sirket


def upsert_kisi(session: Session, row: dict) -> Optional[Kisi]:
    sirket_adi = (row.get("sirket_adi") or "").strip()
    isim = (row.get("isim") or "").strip()
    if not sirket_adi or not isim:
        return None

    sirket = session.query(Sirket).filter(Sirket.ad == sirket_adi).first()
    if not sirket:
        sirket = upsert_sirket(session, {"ad": sirket_adi, "domain": row.get("domain")})

    unvan = (row.get("unvan") or "").strip() or None
    departman = (row.get("departman") or "").strip() or None
    email = _normalize_email(row.get("email"))
    linkedin_url = (row.get("linkedin_url") or "").strip() or None

    kisi = (
        session.query(Kisi)
        .filter(
            Kisi.sirket_id == sirket.id,
            Kisi.isim == isim,
            Kisi.linkedin_url == linkedin_url,
        )
        .first()
    )
    if kisi:
        kisi.unvan = unvan or kisi.unvan
        kisi.departman = departman or kisi.departman
        kisi.email = email or kisi.email
        return kisi

    kisi = Kisi(
        sirket_id=sirket.id,
        isim=isim,
        unvan=unvan,
        departman=departman,
        email=email,
        linkedin_url=linkedin_url,
    )
    session.add(kisi)
    return kisi


def import_sirketler_csv(session: Session, csv_path: str) -> int:
    count = 0
    with open(csv_path, mode="r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("ad"):
                continue
            upsert_sirket(session, row)
            count += 1
    session.commit()
    return count


def import_yoneticiler_csv(session: Session, csv_path: str) -> int:
    count = 0
    with open(csv_path, mode="r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if upsert_kisi(session, row):
                count += 1
    session.commit()
    return count


def sync_master_dict_to_db(session: Session, master_dict: dict) -> int:
    count = 0
    for data in master_dict.values():
        row = dict(data)
        if isinstance(row.get("kaynak"), list):
            row["kaynak"] = " + ".join(row["kaynak"])
        upsert_sirket(session, row)
        count += 1
    session.commit()
    return count
