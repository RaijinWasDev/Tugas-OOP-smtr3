from .aturan_krs import RULES, PrerequisiteValidator
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

MISSING = """SELECT p.kode_mk,m.nama FROM prerequisite p JOIN matakuliah m ON m.kode=p.syarat
 WHERE p.kode_mk IN (SELECT kode_mk FROM krs_detail WHERE krs_id=:id UNION SELECT :kode)
 AND NOT EXISTS (SELECT 1 FROM krs k JOIN krs_detail d ON d.krs_id=k.id
 WHERE k.nim=:nim AND k.semester<:semester AND k.status='approved'
 AND d.kode_mk=p.syarat AND d.bobot>=2) ORDER BY p.kode_mk,m.nama"""

class KRSError(ValueError):
    def __init__(self,message,status=400):
        super().__init__(message)
        self.status=status

class KRSManager:
    def __init__(self,db):
        self.db=db

    def query(self,sql,**args):
        try:
            return self.db.execute(text(sql),args)
        except IntegrityError as exc:
            if str(exc.orig) == "SPP tertunggak":
                raise KRSError("Lunasi tunggakan SPP sebelum mengisi atau mengajukan KRS.", 409) from exc
            raise

    def header(self,nim,semester):
        if not self.query("SELECT 1 FROM calon_mahasiswa WHERE nim=:nim AND status='approved'",nim=nim).first():
            raise KRSError("NIM mahasiswa aktif tidak ditemukan",404)
        return self.query("SELECT * FROM krs WHERE nim=:nim AND semester=:semester",nim=nim,semester=semester).first()

    def courses(self,id):
        return self.query("""SELECT m.* FROM matakuliah m JOIN krs_detail d ON d.kode_mk=m.kode
          WHERE d.krs_id=:id ORDER BY m.kode""",id=id).all()

    def missing(self,id,nim,semester,kode=None):
        result={}
        for key,name in self.query(MISSING,id=id,nim=nim,semester=semester,kode=kode):
            result.setdefault(key,[]).append(name)
        return result

    def edit(self,nim,semester,kode,remove=False,approved_version=None):
        with self.db.begin():
            self.query("BEGIN IMMEDIATE")
            krs=self.header(nim,semester)
            if approved_version is not None:
                if not krs or krs.status != "approved" or krs.version != approved_version:
                    raise KRSError("KRS telah berubah. Muat ulang untuk melanjutkan.",409)
                note = ("Hapus " if remove else "Tambah ") + kode
                self.query("""UPDATE krs SET status='revision', approved_at=NULL, catatan=:note
                              WHERE id=:id""", id=krs.id, note=note)
                self.query("""INSERT INTO krs_log(krs_id,asal,tujuan,aktor,catatan)
                              VALUES(:id,'approved','revision','admin',:note)""", id=krs.id,note=note)
                self.query("""INSERT INTO notifikasi(krs_id,penerima,pesan) VALUES(:id,:nim,:note)""",
                           id=krs.id,nim=nim,note="KRS dikoreksi admin: "+note)
            elif krs and krs.status not in ("draft","revision"):
                raise KRSError("KRS hanya dapat diubah saat draft atau revision",409)
            course=self.query("SELECT * FROM matakuliah WHERE kode=:kode",kode=kode).first()
            if not course:
                raise KRSError("Kode mata kuliah tidak ditemukan",404)
            if remove:
                if not krs or not self.query("DELETE FROM krs_detail WHERE krs_id=:id AND kode_mk=:kode",id=krs.id,kode=kode).rowcount:
                    raise KRSError("Mata kuliah belum dipilih",404)
                id=krs.id
            else:
                id=krs.id if krs else self.query("INSERT INTO krs(nim,semester) VALUES(:nim,:semester)",nim=nim,semester=semester).lastrowid
                others=self.courses(id)
                missing={}
                for rule in RULES:
                    if isinstance(rule,PrerequisiteValidator):
                        missing=self.missing(id,nim,semester,kode)
                    check=rule.check(course,others,missing)
                    if not check.passed:
                        raise KRSError(check.message)
                self.query("INSERT INTO krs_detail(krs_id,kode_mk) VALUES(:id,:kode)",id=id,kode=kode)
            self.query("UPDATE krs SET version=version+1 WHERE id=:id",id=id)
            status = "revision" if approved_version is not None else (krs.status if krs else "draft")
            return self.summary(id,status)

    def add_course(self,nim,semester,kode):
        return self.edit(nim,semester,kode)

    def remove_course(self,nim,semester,kode):
        return self.edit(nim,semester,kode,remove=True)

    def summary(self,id,status):
        courses=self.courses(id)
        meta=self.query("SELECT version,dosen_pa_id,catatan FROM krs WHERE id=:id",id=id).mappings().one()
        return {**meta,"status":status,"mata_kuliah":[c.kode for c in courses],"total_sks":sum(c.sks for c in courses)}

    def validate_krs(self,nim,semester):
        k=self.header(nim,semester)
        if not k:
            raise KRSError("KRS semester ini belum dibuat",404)
        courses=self.courses(k.id)
        missing=self.missing(k.id,nim,semester)
        errors=[]
        for course in courses:
            others=[x for x in courses if x.kode!=course.kode]
            for rule in RULES:
                result=rule.check(course,others,missing)
                if not result.passed and result.message not in errors:
                    errors.append(result.message)
        return {**self.summary(k.id,k.status),"valid":not errors,"kesalahan":errors}


