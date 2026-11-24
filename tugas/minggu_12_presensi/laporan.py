from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

from fastapi import Depends
from sqlalchemy import text
from database import get_db

WIB = timezone(timedelta(hours=7))
HARI = ("Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu")


def sekarang():
    return datetime.now(WIB)


def laporan(db, now):
    rows = db.execute(text("""SELECT s.kode,s.semester,s.mulai,s.tutup,p.nim,p.status
        FROM sesi_presensi s JOIN peserta_presensi p ON p.sesi=s.id
        WHERE s.tutup<=:t ORDER BY s.kode,s.semester,p.nim,s.mulai"""),dict(t=now)).all()
    counts = defaultdict(Counter)
    absen = Counter()
    slots = defaultdict(Counter)
    for r in rows:
        key=(r.nim,r.kode,r.semester)
        mulai=datetime.fromtimestamp(r.mulai,WIB)
        slot=f"{HARI[mulai.weekday()]} {mulai:%H:%M}"
        counts[key][r.status or "absen"]+=1
        slots[r.kode,r.semester,slot][r.status or "absen"]+=1
        if not r.status:
            absen[key,slot]+=1
    rekap=[]
    for (nim,kode,semester),c in counts.items():
        total=sum(c.values())
        rekap.append(dict(nim=nim,kode=kode,semester=semester,sesi=total,hadir=c["hadir"],
                          terlambat=c["terlambat"],absen=c["absen"],
                          persen=round(100*(total-c["absen"])/total,2),risiko=4*c["absen"]>total))
    actions=[f"Hubungi {nim} untuk konseling: absen {n} kali di {kode} semester {sem} pada {slot}."
             for ((nim,kode,sem),slot),n in absen.items() if n>=2]
    for (kode,sem,slot),c in slots.items():
        rate=c["absen"]/sum(c.values())
        if rate>=0.4:
            actions.append(f"Evaluasi jadwal {kode} semester {sem} pada {slot}: {rate:.0%} absen.")
    warning=[r for r in rekap if r["risiko"]]
    return dict(rekap=rekap,peringatan=warning,jumlah_berisiko=len({r["nim"] for r in warning}),actions=actions)


class PresensiAkademik:
    def __init__(self,db=Depends(get_db)):
        self.db=db

    def persentase(self,nim,kode,semester):
        hadir,total=self.db.execute(text("""SELECT COUNT(p.status),COUNT(*) FROM peserta_presensi p
            JOIN sesi_presensi s ON s.id=p.sesi WHERE p.nim=:nim AND s.kode=:kode AND s.semester=:semester
            AND s.tutup<=:now"""),dict(nim=nim,kode=kode,semester=semester,now=int(sekarang().timestamp()))).one()
        return 100*hadir/total if total else 0
