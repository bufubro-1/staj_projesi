from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class Sirket(Base):
    __tablename__ = 'sirketler'
    
    id = Column(Integer, primary_key=True)
    ad = Column(String(255), nullable=False)
    domain = Column(String(255), unique=True, nullable=False)
    sektor = Column(String(100))
    genel_email = Column(String(255))
    telefon = Column(String(50))
    sehir = Column(String(100))
    catch_all = Column(Boolean, default=False)
    calisan_sayisi = Column(Integer, nullable=True)
    kaynak = Column(String(100))
    olusturulma_tarihi = Column(DateTime, default=datetime.datetime.utcnow)
    guncelleme_tarihi = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Kisi(Base):
    __tablename__ = 'kisiler'
    
    id = Column(Integer, primary_key=True)
    sirket_id = Column(Integer, ForeignKey('sirketler.id', ondelete='CASCADE'))
    isim = Column(String(100))
    soyisim = Column(String(100))
    unvan = Column(String(150))
    linkedin_url = Column(String(300), nullable=True)
    dogrulanmis_email = Column(String(255), nullable=True)
    email_dogrulama_tarihi = Column(DateTime, nullable=True)
