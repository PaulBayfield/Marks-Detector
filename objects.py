from datetime import datetime


class Details:
    def __init__(self, name: str, badges: str, coefMatiere: int, prof: str, rang: str, min: float, max: float, mean: float) -> None:
        self.name = name
        self.badges = badges
        self.coefMatiere = coefMatiere
        self.prof = prof
        self.rang = rang
        self.min = min
        self.max = max
        self.mean = mean


class Note:
    def __init__(self, note: float, evaluation:str, coefficient: int, date: str, rang: str, min: float, max: float, mean: float) -> None:
        self.note = note
        self.evaluation = evaluation
        self.coefficient = coefficient
        self.date = date
        self.rang = Rang(rang)
        self.min = min
        self.max = max
        self.mean = mean


class Matiere:
    def __init__(self, matiere: str, name: str, badges: str, coefMatiere: int, prof: str, notes: list[Note]) -> None:
        self.matiere = matiere
        self.name = name
        self.badges = badges
        self.coefMatiere = coefMatiere
        self.prof = prof
        self.notes = notes


class Rang:
    def __init__(self, rang: str) -> None:
        self.rang = rang
        self.current = int(str(self.rang.split("/")[0]).strip())
        self.max = int(str(self.rang.split("/")[1]).lstrip())


class Competence:
    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name


class Coefficient:
    def __init__(self, id: int, coefficient: int) -> None:
        self.id = id
        self.coefficient = coefficient


class MatiereCoefficient:
    def __init__(self, name: str, coefficients: list[Coefficient]) -> None:
        self.code = name.split(" | ")[0]
        self.name = name.split(" | ")[1]
        self.coefficients = coefficients


class MCC:
    """
    Modalités de Contrôle des Connaissances
    """
    def __init__(self, competences: list[Competence], matieres: list[MatiereCoefficient]) -> None:
        self.competences = competences
        self.matieres = matieres


    def getMatiere(self, matiere: str) -> MatiereCoefficient:
        for m in self.matieres:
            if m.name == matiere:
                return m
        return None


    def getUEById(self, id: int) -> Competence:
        for ue in self.competences:
            if ue.id == id:
                return ue
        return None


    def getMatieresByUEId(self, id: int) -> list[MatiereCoefficient]:
        matieres = []
        for matiere in self.matieres:
            for coef in matiere.coefficients:
                if coef.id == id:
                    matieres.append(matiere)
        return matieres
    

    def getTotalCoefficientByUEId(self, id: int) -> int:
        total = 0
        for matiere in self.getMatieresByUEId(id):
            for coef in matiere.coefficients:
                total += coef.coefficient
        return total


class Absence:
    def __init__(self, date: datetime, matiere: str, justifiee: bool, saisie: str) -> None:
        self.date = date
        self.matiere = matiere
        self.justifiee = justifiee
        self.saisie = saisie
