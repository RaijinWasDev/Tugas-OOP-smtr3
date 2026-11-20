from decimal import Decimal, ROUND_HALF_UP


def rata(rows):
    sks = sum(r["sks"] for r in rows)
    mutu = sum(Decimal(str(r["bobot"])) * r["sks"] for r in rows)
    return (mutu / sks if sks else Decimal(0)).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)


def hitung(rows, semester):
    terbaik = {}
    for r in rows:
        if r["semester"] <= semester and r["lulus"]:
            kode = r["kode_mk"]
            if kode not in terbaik or r["bobot"] > terbaik[kode]["bobot"]:
                terbaik[kode] = r
    return rata([r for r in rows if r["semester"] == semester]), rata(terbaik.values())
