from fastapi import FastAPI

app = FastAPI(
    title="Sistem Informasi Akademik",
    description="API untuk modul PMB dan KRS",
    version="1.0.0",
)


@app.get("/")
def halaman_utama():
    return {
        "pesan": "API Sistem Akademik berhasil dijalankan",
        "modul": ["PMB", "KRS"],
    }
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from routers.pmb import router

app.include_router(router)

@app.exception_handler(RequestValidationError)
async def invalid_input(request, exc):
    return JSONResponse(status_code=400, content={"detail": [
        {"field": ".".join(map(str, e["loc"])), "pesan": e["msg"]} for e in exc.errors()
    ]})
