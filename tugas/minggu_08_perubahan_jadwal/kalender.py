from datetime import date, datetime, time, timedelta, timezone
from fastapi import HTTPException, Response
from sqlalchemy import text

WIB = timezone(timedelta(hours=7))


def stamp(value):
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def escape(value):
    return value.replace("\\", "\\\\").replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")


def folded(line):
    parts = [""]
    for char in line:
        if len((parts[-1]+char).encode()) > 75:
            parts.append(" ")
        parts[-1] += char
    return "\r\n".join(parts)


def export(db, awal: date, akhir: date):
    if akhir < awal or (akhir-awal).days > 366:
        raise HTTPException(400, "Pilih rentang semester sampai satu tahun.")
    rows = db.execute(text("""SELECT m.*,j.ruangan,j.dosen,
        COALESCE((SELECT MAX(id) FROM outbox_jadwal o WHERE o.kode=m.kode),0) AS versi
        FROM jadwal j JOIN matakuliah m USING(kode) ORDER BY m.kode"""))
    lines = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Sevima Mini//Jadwal//ID","CALSCALE:GREGORIAN"]
    now = stamp(datetime.now(timezone.utc))
    until = stamp(datetime.combine(akhir,time(23,59,59),WIB))
    for row in rows:
        first = awal + timedelta(days=(row.hari-awal.isoweekday()) % 7)
        if first > akhir:
            continue
        midnight = datetime.combine(first,time.min,WIB)
        lines.extend(["BEGIN:VEVENT", f"UID:{row.kode}-{awal:%Y%m%d}@sevima-mini",
                      f"SEQUENCE:{row.versi}", f"DTSTAMP:{now}",
                      "DTSTART:"+stamp(midnight+timedelta(minutes=row.mulai)),
                      "DTEND:"+stamp(midnight+timedelta(minutes=row.selesai)),
                      f"RRULE:FREQ=WEEKLY;UNTIL={until}", "SUMMARY:"+escape(row.nama),
                      "LOCATION:"+escape(row.ruangan), "DESCRIPTION:"+escape(row.dosen), "END:VEVENT"])
    lines.append("END:VCALENDAR")
    return Response("\r\n".join(map(folded,lines))+"\r\n",media_type="text/calendar",
                    headers={"Content-Disposition":'attachment; filename="jadwal.ics"'})
