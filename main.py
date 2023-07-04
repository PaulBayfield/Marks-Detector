from client import Client
from objects import Matiere, Note

import asyncio


USERNAME = ""
PASSWORD = ""


async def main():
    client = Client("https://iut-rcc-intranet.univ-reims.fr/sso/cas")
    status = await client.login(USERNAME, PASSWORD)
    if status:
        profil = await client.profile()
        print("Connexion réussie !\n\nConnecté en tant que", profil, "\n\n")

        matieres = await client.notes()

        for matiere in matieres:
            matiere: Matiere = matiere
            print(f"Matière: [{matiere.matiere}] {matiere.name} ({', '.join(matiere.badges)}) [{matiere.coefMatiere}] {matiere.prof} ({len(matiere.notes)} notes)")

            for note in matiere.notes:
                note: Note = note
                print("\t", note.note)
                print("\t", note.evaluation)
                print("\t", note.coefficient)
                print("\t", note.date)
                print("\t", note.rang.rang, f"({note.rang.current}/{note.rang.max})")
                print("\t", note.min)
                print("\t", note.max)
                print("\t", note.mean)
                print("\n")

        print(await client.coefficients())


asyncio.run(main())
