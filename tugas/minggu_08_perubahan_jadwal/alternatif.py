from collections import defaultdict
from sqlalchemy import text


class IntervalNode:
    """Balanced tree of half-open intervals sorted by start time."""
    def __init__(self, rows):
        mid = len(rows) // 2
        self.row = rows[mid]
        self.left = IntervalNode(rows[:mid]) if mid else None
        self.right = IntervalNode(rows[mid+1:]) if mid+1 < len(rows) else None
        self.end = max(node.end for node in (self.left, self.right) if node) if len(rows)>1 else 0
        self.end = max(self.end, self.row.selesai)

    def overlaps(self, start, end):
        if self.end <= start:
            return
        if self.left:
            yield from self.left.overlaps(start, end)
        if self.row.mulai >= end:
            return
        if self.row.selesai > start:
            yield self.row
        if self.right:
            yield from self.right.overlaps(start, end)


class Calendar:
    def __init__(self, db, kode):
        days = defaultdict(list)
        for row in db.execute(text("""SELECT m.kode,m.hari,m.mulai,m.selesai,j.ruangan,j.dosen
            FROM jadwal j JOIN matakuliah m USING(kode) WHERE m.kode<>:kode ORDER BY m.mulai"""),
                              {"kode": kode}):
            days[row.hari].append(row)
        self.days = {day: IntervalNode(rows) for day,rows in days.items()}

    def conflicts(self, slot):
        result = []
        tree = self.days.get(slot["hari"])
        if tree:
            for row in tree.overlaps(slot["mulai"], slot["selesai"]):
                types = []
                if row.ruangan == slot["ruangan"]:
                    types.append("room_conflict")
                if row.dosen.casefold() == slot["dosen"].casefold():
                    types.append("lecturer_conflict")
                if types:
                    result.append({"types":["time_overlap", *types], "jadwal":[slot["kode"],row.kode]})
        return result


def alternatives(db, calendar, slot, enrolled):
    rooms = db.execute(text("SELECT kode FROM ruangan WHERE kapasitas>=:n ORDER BY kode"),
                       {"n": enrolled}).scalars().all()
    duration = slot["selesai"] - slot["mulai"]
    choices = []
    for day in range(1, 8):
        for start in sorted({slot["mulai"], *range(480, 1021-duration, 30)}):
            if start+duration > 1440:
                continue
            for room in rooms:
                candidate = dict(slot, hari=day, mulai=start, selesai=start+duration, ruangan=room)
                if candidate == slot or calendar.conflicts(candidate):
                    continue
                rank = (abs(day-slot["hari"]), abs(start-slot["mulai"]), room!=slot["ruangan"], start, room)
                choices.append((rank, dict(candidate, reason="Kapasitas cukup, ruangan dan dosen tersedia.")))
    return [choice for _, choice in sorted(choices,key=lambda pair: pair[0])[:3]]
