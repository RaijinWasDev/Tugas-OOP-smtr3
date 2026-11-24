import hashlib
import hmac
import base64
import json
import os
import secrets
from io import BytesIO
from datetime import timedelta
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import text
from database import get_db
from routers.akses import require_admin
from .laporan import laporan, sekarang

router=APIRouter(prefix="/attendance")
ADMIN=[Depends(require_admin)]


def b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=")


def token_sesi(kode,issued,exp):
    # HS256 JWT. Verifikasi memakai digest token aktif yang disimpan saat penerbitan.
    payload=json.dumps(dict(schedule_id=kode,iat=issued,exp=exp,jti=secrets.token_urlsafe(16)),separators=(",",":"))
    body=b64(b'{"alg":"HS256","typ":"JWT"}')+b"."+b64(payload.encode())
    signature=hmac.digest(os.environ["PMB_ADMIN_KEY"].encode(),body,"sha256")
    return (body+b"."+b64(signature)).decode()


def gambar(url):
    import qrcode
    from qrcode.image.svg import SvgPathImage
    output=BytesIO()
    qrcode.make(url,image_factory=SvgPathImage).save(output)
    return output.getvalue()


@router.get("/qr/{schedule_id}",dependencies=ADMIN)
def qr(schedule_id:str,request:Request,dosen:str,semester:int=Query(ge=1),db=Depends(get_db)):
    db.execute(text("BEGIN IMMEDIATE"))
    p=dict(kode=schedule_id,semester=semester,dosen=dosen.strip())
    jadwal=db.execute(text("""SELECT m.hari,m.mulai,m.selesai FROM jadwal j JOIN matakuliah m USING(kode)
        WHERE j.kode=:kode AND j.dosen=:dosen"""),p).first()
    if not jadwal:
        raise HTTPException(403,"Periksa jadwal dan nama dosen pengampu.")
    now=sekarang()
    start=now.replace(hour=0,minute=0,second=0,microsecond=0)+timedelta(minutes=jadwal.mulai)
    end=start+timedelta(minutes=min(30,jadwal.selesai-jadwal.mulai))
    if now.isoweekday()!=jadwal.hari or not start<=now<end:
        raise HTTPException(409,"Buka presensi dalam 30 menit pertama jadwal kuliah (WIB).")
    exp=int(min(end,now+timedelta(minutes=15)).timestamp())
    token=token_sesi(schedule_id,int(now.timestamp()),exp)
    p.update(tanggal=now.date().isoformat(),mulai=int(start.timestamp()),tutup=int(end.timestamp()),
             hash=hashlib.sha256(token.encode()).hexdigest(),exp=exp)
    sesi=db.scalar(text("SELECT id FROM sesi_presensi WHERE kode=:kode AND semester=:semester AND tanggal=:tanggal"),p)
    if sesi is None:
        sesi=db.execute(text("""INSERT INTO sesi_presensi(kode,semester,tanggal,mulai,tutup,token_hash,kedaluwarsa)
            VALUES(:kode,:semester,:tanggal,:mulai,:tutup,:hash,:exp)"""),p).lastrowid
        p["id"]=sesi
        peserta=db.execute(text("""INSERT INTO peserta_presensi(sesi,nim)
            SELECT :id,k.nim FROM krs k JOIN krs_detail d ON k.id=d.krs_id
            WHERE d.kode_mk=:kode AND k.semester=:semester AND k.status='approved'"""),p)
        if not peserta.rowcount:
            raise HTTPException(409,"Belum ada peserta dengan KRS disetujui pada semester ini.")
    else:
        db.execute(text("UPDATE sesi_presensi SET token_hash=:hash,kedaluwarsa=MIN(tutup,:exp) WHERE id=:id"),dict(p,id=sesi))
    link=str(request.base_url).rstrip("/")+"/aset/scan.html#"+quote(token)
    svg=gambar(link)
    db.commit()
    return Response(svg,media_type="image/svg+xml",headers={"Cache-Control":"no-store","X-Scan-Link":link})


class Scan(BaseModel):
    token:str=Field(min_length=1,max_length=2048)
    nim:str=Field(min_length=1,max_length=40)


@router.post("/scan")
def scan(data:Scan,request:Request,db=Depends(get_db)):
    now=int(sekarang().timestamp())
    p=dict(ip=request.client.host if request.client else "local",now=now,nim=data.nim.strip(),
           hash=hashlib.sha256(data.token.encode()).hexdigest())
    db.execute(text("BEGIN IMMEDIATE"))
    db.execute(text("DELETE FROM batas_scan WHERE awal<=:now-60"),p)
    db.execute(text("""INSERT INTO batas_scan VALUES(:ip,:now,1)
        ON CONFLICT(ip) DO UPDATE SET jumlah=jumlah+1"""),p)
    count=db.scalar(text("SELECT jumlah FROM batas_scan WHERE ip=:ip"),p)
    def tolak(code,message):
        db.commit()
        raise HTTPException(code,message)
    if count>30:
        tolak(429,"Terlalu banyak percobaan. Tunggu satu menit.")
    parts=data.token.encode().rsplit(b".",1)
    if len(parts)!=2 or not hmac.compare_digest(parts[1],b64(hmac.digest(os.environ["PMB_ADMIN_KEY"].encode(),parts[0],"sha256"))):
        tolak(410,"QR tidak valid.")
    s=db.execute(text("SELECT * FROM sesi_presensi WHERE token_hash=:hash"),p).first()
    if not s or not s.mulai<=now<min(s.kedaluwarsa,s.tutup):
        tolak(410,"QR sudah kedaluwarsa atau telah diganti.")
    p.update(id=s.id,kode=s.kode,semester=s.semester)
    peserta=db.execute(text("""SELECT p.status FROM peserta_presensi p WHERE p.sesi=:id AND p.nim=:nim
        AND EXISTS(SELECT 1 FROM krs k JOIN krs_detail d ON k.id=d.krs_id WHERE k.nim=p.nim
        AND k.status='approved' AND k.semester=:semester AND d.kode_mk=:kode)"""),p).first()
    if not peserta:
        tolak(403,"NIM tidak terdaftar pada kelas ini.")
    if peserta.status:
        tolak(409,"Presensi sudah tercatat.")
    p["status"]="hadir" if now<s.mulai+900 else "terlambat"
    db.execute(text("UPDATE peserta_presensi SET status=:status,waktu=:now WHERE sesi=:id AND nim=:nim"),p)
    db.commit()
    return dict(success=True,status=p["status"],message="Presensi tercatat.")


@router.get("/report",dependencies=ADMIN)
def report(db=Depends(get_db)):
    return laporan(db,int(sekarang().timestamp()))


@router.get("/report.xlsx",dependencies=ADMIN)
def excel(db=Depends(get_db)):
    from openpyxl import Workbook
    wb=Workbook()
    sheet=wb.active
    sheet.title="Presensi"
    fields=("nim","kode","semester","sesi","hadir","terlambat","absen","persen","risiko")
    sheet.append(fields)
    for r in report(db)["rekap"]:
        sheet.append([r[k] for k in fields])
    file=BytesIO()
    wb.save(file)
    return Response(file.getvalue(),media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition":"attachment; filename=presensi.xlsx"})

