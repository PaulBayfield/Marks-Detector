from client import Client
from utils import getMatiere

import asyncio


USERNAME = ""
PASSWORD = ""


async def main():
    client = Client("https://iut-rcc-intranet.univ-reims.fr/sso/cas")
    status = await client.login(USERNAME, PASSWORD)
    if status:
        profil = await client.profil()
        print("Connexion réussie !\n\nConnecté en tant que", profil, "\n\n")


        # Matieres & Notes
        matieres = await client.notes()

        for matiere in matieres:
            print(f"Matière: [{matiere.matiere}] {matiere.name} ({', '.join(matiere.badges)}) [{matiere.coefMatiere}] {matiere.prof} ({len(matiere.notes)} notes)")

            for note in matiere.notes:
                print("\t • Note : ", note.note)
                print("\t • Type : ", note.evaluation)
                print("\t • Coef : ", note.coefficient)
                print("\t • Date : ", note.date)
                print("\t • Rang : ", note.rang.rang, f"({note.rang.current}/{note.rang.max})")
                print("\t • Mini : ", note.min)
                print("\t • Maxi : ", note.max)
                print("\t • Mean : ", note.mean)
                print(" ")


        # Competences & Coefficients
        mcc = await client.mcc()

        print("Compétences: ")
        for ue in mcc.competences:
            print(f"\t • {ue.name} [{ue.id}] ({len(mcc.getMatieresByUEId(ue.id))} matières) (Total coef : {mcc.getTotalCoefficientByUEId(ue.id)})")
        print(" ")

        for coefficient in mcc.matieres:
            print("Matieres: ", coefficient.name)
            for coef in coefficient.coefficients:
                print("\t • Coef : ", coef.coefficient)
                print("\t • Compétence : ", mcc.getUEById(coef.id).name, f"({coef.id})")
                print(" ")


        # Absences
        absences = await client.absences()

        print(f"{len(absences)} absences: ")
        for idx, absence in enumerate(absences):
            m = getMatiere(mcc.matieres, absence.matiere)

            print(f"Absence n°{idx+1}:")
            print("\t • Date : ", absence.date)
            print("\t • Matière : ", m.code, m.name)
            print("\t • Justifié : ", absence.justifiee)
            print("\t • Saisie : ", absence.saisie)


asyncio.run(main())
