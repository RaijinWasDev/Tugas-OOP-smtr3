from abc import ABC, abstractmethod
from dataclasses import dataclass
@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    message: str = ""

class Validator(ABC):
    @abstractmethod
    def check(self, course, others, missing):
        pass

class DuplicateValidator(Validator):
    def check(self,c,others,missing):
        return ValidationResult(all(x.kode!=c.kode for x in others), f"{c.nama} sudah dipilih")

class SKSValidator(Validator):
    def check(self,c,others,missing):
        total=c.sks+sum(x.sks for x in others)
        return ValidationResult(total<=24,f"Total {total} SKS melebihi batas 24")

class PrerequisiteValidator(Validator):
    def check(self,c,others,missing):
        names=missing.get(c.kode,[])
        return ValidationResult(not names,f"{c.nama} memerlukan kelulusan: "+", ".join(names))

class ConflictValidator(Validator):
    def check(self,c,others,missing):
        names=[x.nama for x in others if x.hari==c.hari and x.mulai<c.selesai and c.mulai<x.selesai]
        return ValidationResult(not names,f"{c.nama} bentrok dengan "+", ".join(names))

RULES=(DuplicateValidator(),SKSValidator(),PrerequisiteValidator(),ConflictValidator())

