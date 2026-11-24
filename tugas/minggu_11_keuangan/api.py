from contextlib import asynccontextmanager
from datetime import date
import hashlib
import hmac
import os

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from .service import email_queue, generate, mulai_jadwal

router=APIRouter(prefix="/api/spp",tags=["Keuangan"])
gateway=APIRouter(tags=["Gateway SPP"])


@asynccontextmanager
async def lifespan(app):
    scheduler=mulai_jadwal()
    try:
        yield
    finally:
        scheduler.shutdown()


class Pembayaran(BaseModel):
    transaction_id: str=Field(min_length=1,max_length=100)
    billing_id: int=Field(gt=0)
    amount: int=Field(gt=0,strict=True)


class Notifikasi(Pembayaran):
    status: str


def bayar(db, data, metode):
    db.execute(text("BEGIN IMMEDIATE"))
    params=dict(id=data.transaction_id,b=data.billing_id,n=data.amount,m=metode)
    lama=db.execute(text("SELECT billing_id,jumlah,metode FROM payment WHERE id=:id"),params).first()
    if lama:
        if tuple(lama)!=(data.billing_id,data.amount,metode):
            raise HTTPException(409,"ID transaksi sudah digunakan dengan data berbeda.")
        return {"transaksi":data.transaction_id}
    b=db.execute(text("SELECT * FROM saldo_spp WHERE id=:b"),params).first()
    if not b:
        raise HTTPException(404,"Tagihan tidak ditemukan.")
    if b.sisa==0:
        raise HTTPException(422,"Tagihan sudah lunas.")
    db.execute(text("INSERT INTO payment(id,billing_id,jumlah,metode) VALUES (:id,:b,:n,:m)"),params)
    email_queue(db,"receipt-"+data.transaction_id,b.nim,f"Bukti pembayaran {data.transaction_id}: Rp{data.amount}. Sisa Rp{max(0,b.sisa-data.amount)}.")
    db.commit()
    return {"transaksi":data.transaction_id}


@router.post("/tagihan")
def tagihan(awal: date,db: Session=Depends(get_db)):
    dibuat=generate(db,awal)
    db.commit()
    return {"dibuat":dibuat}


@router.post("/bayar")
def manual(data:Pembayaran,db:Session=Depends(get_db)):
    return bayar(db,data,"manual")


@gateway.post("/api/spp/webhook")
async def webhook(request:Request,x_signature:str=Header(default=""),db:Session=Depends(get_db)):
    secret=os.getenv("SPP_WEBHOOK_SECRET")
    if not secret:
        raise HTTPException(503,"Kunci gateway belum diatur.")
    body=await request.body()
    if not hmac.compare_digest(hmac.new(secret.encode(),body,hashlib.sha256).hexdigest().encode(),x_signature.encode()):
        raise HTTPException(403,"Tanda tangan tidak sesuai.")
    try:
        data=Notifikasi.model_validate_json(body)
    except ValueError:
        raise HTTPException(422,"Format notifikasi tidak valid.")
    if data.status!="success":
        return {"diproses":False}
    return bayar(db,data,"gateway")


@router.get("/dashboard")
def dashboard(db:Session=Depends(get_db)):
    def rows(sql):
        return [dict(r) for r in db.execute(text(sql)).mappings()]
    daftar=rows("""SELECT s.*,m.nama_lengkap,p.nama prodi FROM saldo_spp s JOIN calon_mahasiswa m USING(nim)
        JOIN program_studi p ON p.id=m.program_studi_id ORDER BY s.awal DESC,m.nama_lengkap""")
    mahasiswa=rows("""SELECT nim,SUM(pokok+denda) tagihan,SUM(dibayar) dibayar,SUM(sisa) sisa
        FROM saldo_spp GROUP BY nim""")
    prodi=rows("""SELECT p.nama,ROUND(100.0*SUM(MIN(s.dibayar,s.pokok+s.denda))/SUM(s.pokok+s.denda),2) persen FROM saldo_spp s
        JOIN calon_mahasiswa m USING(nim) JOIN program_studi p ON p.id=m.program_studi_id GROUP BY p.id""")
    bulan=rows("SELECT substr(tanggal,1,7) bulan,SUM(jumlah) jumlah FROM payment GROUP BY 1 ORDER BY 1")
    top=rows("""SELECT nim,SUM(sisa) tunggakan FROM saldo_spp WHERE status='overdue'
        GROUP BY nim ORDER BY tunggakan DESC,nim LIMIT 10""")
    lama=db.scalar(text("SELECT COUNT(DISTINCT nim) FROM saldo_spp WHERE status='overdue' AND tempo<date('now','localtime','-2 months')"))
    return dict(tagihan=daftar,mahasiswa=mahasiswa,prodi=prodi,bulan=bulan,top=top,
                revenue=sum(r['jumlah'] for r in bulan if r['bulan']==date.today().strftime('%Y-%m')),
                collection_rate=round(100*sum(r['sisa']==0 for r in mahasiswa)/len(mahasiswa),2) if mahasiswa else 0,
                rekomendasi=f"Kirim pengingat kepada {lama} mahasiswa dengan tunggakan lebih dari dua bulan.")



@router.post("/laporan-csv")
async def laporan_csv(request: Request, db: Session = Depends(get_db)):
    """CSV pembayaran menggantikan sumber penerimaan bulanan; saldo berasal dari buku tagihan."""
    import csv
    from io import StringIO

    pendapatan = 0
    try:
        reader = csv.DictReader(StringIO((await request.body()).decode("utf-8-sig")))
        if not {"nim", "jumlah", "tanggal", "status"}.issubset(reader.fieldnames or []):
            raise ValueError()
        for row in reader:
            tanggal = date.fromisoformat(row["tanggal"])
            jumlah = int(row["jumlah"])
            if not row["nim"] or jumlah < 0 or row["status"] not in {"paid","partial","unpaid","overdue"}:
                raise ValueError()
            if tanggal.replace(day=1) == date.today().replace(day=1):
                pendapatan += jumlah
    except (ValueError, TypeError, csv.Error):
        raise HTTPException(422, "Periksa kolom nim, jumlah, tanggal (YYYY-MM-DD), dan status.")
    saldo = dashboard(db)
    return dict(revenue=pendapatan, collection_rate=saldo["collection_rate"],
                top=saldo["top"], rekomendasi=saldo["rekomendasi"])
