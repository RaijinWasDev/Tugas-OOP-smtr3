from enum import StrEnum
from services.krs import KRSError, KRSManager

class KRSStatus(StrEnum):
    DRAFT="draft"
    SUBMITTED="submitted"
    REVISION="revision"
    APPROVED="approved"

ALLOWED={
    (KRSStatus.APPROVED,KRSStatus.REVISION):"dosen",
    (KRSStatus.DRAFT,KRSStatus.SUBMITTED):"mahasiswa",
    (KRSStatus.REVISION,KRSStatus.SUBMITTED):"mahasiswa",
    (KRSStatus.SUBMITTED,KRSStatus.REVISION):"dosen",
    (KRSStatus.SUBMITTED,KRSStatus.APPROVED):"dosen",
}

def check_transition(source,target,role):
    if (source,target) not in ALLOWED:
        raise KRSError(f"Transisi {source} ke {target} tidak diizinkan",409)
    if ALLOWED[source,target]!=role:
        raise KRSError("Peran tidak berwenang",403)

class KRSWorkflow(KRSManager):
    def transition(self,nim,semester,target,role,actor,version,note=None,expected_status=None):
        with self.db.begin():
            self.query("BEGIN IMMEDIATE")
            k=self.header(nim,semester)
            if not k:
                raise KRSError("KRS belum dibuat",404)
            expected_role="mahasiswa" if target==KRSStatus.SUBMITTED else "dosen"
            owner=nim if expected_role=="mahasiswa" else k.dosen_pa_id
            if role!=expected_role or actor!=owner:
                raise KRSError("Aktor tidak berhak atas KRS ini",403)
            if version!=k.version:
                raise KRSError("Versi lama. Muat ulang KRS.",409)
            if expected_status is not None and k.status != expected_status:
                raise KRSError("Status KRS telah berubah. Muat ulang KRS.",409)
            check_transition(k.status,target,role)
            if target==KRSStatus.SUBMITTED:
                report=self.validate_krs(nim,semester)
                if not report["mata_kuliah"] or not report["valid"]:
                    raise KRSError("; ".join(report["kesalahan"]) or "KRS kosong")
            if target==KRSStatus.REVISION and not (note or "").strip():
                raise KRSError("Catatan revisi wajib diisi")
            self.query("""UPDATE krs SET status=:target,version=version+1,catatan=:note,
                submitted_at=CASE WHEN :target='submitted' THEN CURRENT_TIMESTAMP ELSE submitted_at END,
                approved_at=CASE WHEN :target='approved' THEN CURRENT_TIMESTAMP WHEN :target='revision' THEN NULL ELSE approved_at END
                WHERE id=:id""",target=target,note=note,id=k.id)
            self.query("""INSERT INTO krs_log(krs_id,asal,tujuan,aktor,catatan)
                VALUES(:id,:old,:new,:actor,:note)""",id=k.id,old=k.status,new=target,actor=actor,note=note)
            self.query("INSERT INTO notifikasi(krs_id,penerima,pesan) VALUES(:id,:to,:msg)",
                       id=k.id,to=k.dosen_pa_id if role=="mahasiswa" else nim,msg=f"KRS {target}. {note or ''}".strip())
            return self.summary(k.id,target)

    def submit_krs(self,nim,semester,actor,version):
        return self.transition(nim,semester,KRSStatus.SUBMITTED,"mahasiswa",actor,version)

    def approve_krs(self,nim,semester,dosen_pa_id,version):
        return self.transition(nim,semester,KRSStatus.APPROVED,"dosen",dosen_pa_id,version)

    def revise_krs(self,nim,semester,dosen_pa_id,version,note):
        return self.transition(nim,semester,KRSStatus.REVISION,"dosen",dosen_pa_id,version,note,expected_status=KRSStatus.SUBMITTED)

    def reopen_krs(self, nim, semester, dosen_pa_id, version, note):
        return self.transition(nim, semester, KRSStatus.REVISION, "dosen", dosen_pa_id,
                               version, note, expected_status=KRSStatus.APPROVED)
