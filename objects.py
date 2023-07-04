class Details:
    def __init__(self, name: str, badges: str, coefMatiere: int, prof: str, rang: str, min: float, max: float, mean: float):
        self.name = name
        self.badges = badges
        self.coefMatiere = coefMatiere
        self.prof = prof
        self.rang = rang
        self.min = min
        self.max = max
        self.mean = mean


class Note:
    def __init__(self, note: float, evaluation:str, coefficient: int, date: str, rang: str, min: float, max: float, mean: float):
        self.note = note
        self.evaluation = evaluation
        self.coefficient = coefficient
        self.date = date
        self.rang = Rang(rang)
        self.min = min
        self.max = max
        self.mean = mean


class Matiere:
    def __init__(self, matiere: str, name: str, badges: str, coefMatiere: int, prof: str, notes: Note):
        self.matiere = matiere
        self.name = name
        self.badges = badges
        self.coefMatiere = coefMatiere
        self.prof = prof
        self.notes = notes


class Rang:
    def __init__(self, rang: str):
        self.rang = rang
        self.current = int(str(self.rang.split("/")[0]).strip())
        self.max = int(str(self.rang.split("/")[1]).lstrip())
