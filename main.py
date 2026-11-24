from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from tugas.minggu_09_nilai import api as nilai
from tugas.minggu_11_keuangan import api as spp
from tugas.minggu_12_presensi import api as presensi
from routers import admin
from routers.akses import require_admin
from tugas.minggu_03_pendaftaran_pmb import api as pendaftaran
from tugas.minggu_04_persetujuan_pmb import api as persetujuan
from tugas.minggu_05_pengisian_krs import api as pengisian
from tugas.minggu_06_persetujuan_krs import api as workflow
from tugas.minggu_07_jadwal_ruangan import jadwal
from tugas.minggu_05_pengisian_krs.pengisian import KRSError

app = FastAPI(lifespan=spp.lifespan, title="Sevima Mini", description="Administrasi PMB, KRS, dan jadwal kuliah")
akses_admin = [Depends(require_admin)]
app.include_router(presensi.router)
app.include_router(admin.router)
app.include_router(spp.router, dependencies=akses_admin)
app.include_router(spp.gateway)
for modul in (pendaftaran, persetujuan, pengisian, workflow, jadwal, nilai):
    app.include_router(modul.router, dependencies=akses_admin)
app.mount("/aset", StaticFiles(directory=admin.WEB), name="aset")


@app.get("/", include_in_schema=False)
@app.get("/demo-jadwal", include_in_schema=False)
def beranda():
    return RedirectResponse("/admin")


@app.exception_handler(RequestValidationError)
async def invalid_input(request, exc):
    return JSONResponse(status_code=400, content={"detail": [
        {"field": ".".join(map(str, e["loc"])), "pesan": e["msg"]} for e in exc.errors()
    ]})


@app.exception_handler(KRSError)
async def invalid_krs(request, exc):
    return JSONResponse(status_code=exc.status, content={"detail": str(exc)})
