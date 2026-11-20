from fastapi import Depends, HTTPException
from secrets import compare_digest
import os
from fastapi.security import APIKeyHeader


admin_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)

def require_admin(key: str | None = Depends(admin_header)):
    expected = os.environ.get("PMB_ADMIN_KEY")
    if not expected:
        raise HTTPException(503, "Kunci admin belum dikonfigurasi")
    if not key or not compare_digest(key.encode(), expected.encode()):
        raise HTTPException(403, "Akses admin diperlukan")

