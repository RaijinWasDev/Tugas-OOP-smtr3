import json
import os

import httpx


def select_suggestions(slot, choices, provider=None):
    """Only model-selected slots that match our prevalidated catalogue may leave this function."""
    if not choices:
        return []
    model = os.getenv("SEVIMA_MODEL")
    if provider is None and not model:
        return [dict(c, sumber="Aturan lokal") for c in choices[:3]]
    catalogue = {(c["hari"], c["mulai"], c["ruangan"]): c for c in choices}
    try:
        proposals = (provider or ollama)(slot, list(catalogue), model)
        if not isinstance(proposals, list):
            raise ValueError("Format usulan")
    except (ValueError, KeyError, TypeError, httpx.HTTPError):
        return [dict(c, sumber="Aturan lokal (AI tidak tersedia)") for c in choices[:3]]
    valid = []
    for p in proposals:
        if not isinstance(p, dict):
            continue
        day, start, room = p.get("hari"), p.get("mulai"), p.get("ruangan")
        if type(day) is not int or type(start) is not int or not isinstance(room, str):
            continue
        candidate = catalogue.pop((day, start, room), None)
        reason = p.get("reason")
        if candidate and isinstance(reason, str) and reason.strip():
            valid.append(dict(candidate, reason=reason.strip()[:300], sumber="AI"))
        if len(valid) == 3:
            break
    return valid


def ollama(slot, available, model):
    prompt = ("Pilih hingga tiga slot tersedia yang paling sedikit mengganggu mahasiswa. "
              "Utamakan pagi atau siang. Balas JSON dengan kunci saran berisi array objek "
              "hari, mulai (menit), ruangan, reason. " +
              json.dumps({"jadwal":slot,"slot_tersedia":available}, ensure_ascii=False))
    response = httpx.post("http://127.0.0.1:11434/api/generate",
                          json={"model":model,"prompt":prompt,"format":"json","stream":False},
                          timeout=15, trust_env=False)
    response.raise_for_status()
    return json.loads(response.json()["response"])["saran"]
