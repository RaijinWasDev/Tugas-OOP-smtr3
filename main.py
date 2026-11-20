from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from routers import admin, jadwal, krs, pmb
from services.krs import KRSError

app = FastAPI(title="Sevima Mini", description="Administrasi PMB, KRS, dan jadwal kuliah")
akses_admin = [Depends(pmb.require_admin)]
app.include_router(admin.router)
for modul in (pmb, krs, jadwal):
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
