from config import config
from objects import Matiere, Note, Details, MCC, Competence, MatiereCoefficient, Coefficient, Absence
from exception import InvalidCredentials, UnknownError, NotConnected
from utils import stringToDatetime


import re
import math

from cas import CAS
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlencode, urljoin


class Client(CAS):
    def __init__(self, service: str):
        super().__init__()

        self.CAS_BASE_URL = config.get('cas').get('BASE_URL')
        self.SERVICE_URL = service

        self.__profil = None


    async def login(self, username: str, password: str) -> bool:
        """
        Connection au Service
        
        :param username: Nom d'utilisateur
        :param password: Mot de passe
        :return: Un booleen indiquant si la connection a reussi
        """
        url = f"{self.CAS_BASE_URL}?service={self.SERVICE_URL}"

        data = {
            "username": username,
            "password": password,
            "execution": await self.getTokenData(url),
            "_eventId": "submit",
            "geolocation": ""
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": config.get('userAgent')
        }

        resp = await self.request(
            url=url,
            method="POST",
            data=urlencode(data),
            headers=headers,
            raw=True, 
            redirect=False
        )

        location = resp.headers.get("location", "")

        if "ticket" in location:
            return await self.createSession(self.SERVICE_URL, location)
        else:
            raise InvalidCredentials("Impossible de se connecter avec les identifiants fournis ! Vérifiez-les et réessayez.")


    
    async def profil(self) -> str:
        """
        Permet de récupérer le nom complet de l'utilisateur connecté

        :return: Le nom complet de l'utilisateur connecté
        """
        url = urljoin(self.BASE_URL, "/fr/utilisateur/mon-profil")

        res = await self.request(
            url=url,
            method="GET"
        )

        if res:
            if not self.__profil:
                b = BeautifulSoup(res, "html.parser")

                self.__profil = re.compile(r"\/fr\/etudiant\/profil\/(.*\..*)\/.*").match(str(b.find("a", {"class": "nav-link changeprofil"})).split("href=\"")[1].split("\"")[0])[1]
            return self.__profil
        else:
            raise UnknownError("Nom complet introuvable")


    async def notes(self) -> list[Matiere]:
        """
        Permet de récupérer les notes de l'utilisateur connecté
        
        :return: Une liste de Matiere
        """
        if not self.__profil:
            raise NotConnected()

        url = urljoin(self.BASE_URL, f"/fr/etudiant/profil/{self.__profil}/notes")

        res = await self.request(
            url=url,
            method="GET",
        )

        if res:
            b = BeautifulSoup(res, "html.parser")

            headers = [
                {"name": "matiere", "type": "string"},
                {"name": "evaluation", "type": "string"},
                {"name": "date", "type": "string"},
                {"name": "commentaire", "type": "string"},
                {"name": "note", "type": "number"},
                {"name": "coefficient", "type": "number"},
                {"name": "detailsURL", "type": "string"}
            ]

            data = []
            for elem in b.find("tbody").find_all("tr"):
                obj = {}
                for idx, el in enumerate(elem.find_all("td")):
                    if headers[idx]:
                        header = headers[idx]
                        _data = el.text.strip()

                        if header["type"] == "number":
                            try:
                                _data = float(_data.replace(",", "."))
                            except ValueError:
                                _data = 0

                            if math.isnan(_data):
                                _data = 0
                        elif header["name"] == "detailsURL":
                            _data = str(el).split("-url-value=\"")[1].split("\"")[0]

                        if (
                            header["name"] == "matiere" or
                            header["name"] == "evaluation" or
                            header["name"] == "date" or
                            header["name"] == "note" or
                            header["name"] == "coefficient" or
                            header["name"] == "detailsURL"
                        ):
                            obj[header["name"]] = _data

                data.append(obj)

            result = {}
            for d in data:
                details: Details = await self.noteInfo(d["detailsURL"])

                matiere = d["matiere"]
                if matiere not in result:
                    result[matiere] = Matiere(
                        matiere=matiere, 
                        name=details.name, 
                        badges=details.badges, 
                        coefMatiere=details.coefMatiere, 
                        prof=details.prof, 
                        notes=[]
                    )

                result[matiere].notes.append(
                    Note(
                        note=d['note'], 
                        evaluation=d['evaluation'],
                        coefficient=d['coefficient'], 
                        date=d['date'],
                        rang=details.rang,
                        min=details.min,
                        max=details.max,
                        mean=details.mean,
                    )
                )

            return list(result.values())
        else:
            raise UnknownError("Impossible d'importer les notes")


    async def noteInfo(self, detailsURL: str) -> Details:
        """
        Permet de récupérer les informations d'une note
        
        :param detailsURL: L'URL de la note
        :return: Une instance de Details
        """
        detailsURL = urljoin(self.BASE_URL, detailsURL)

        res = await self.request(
            url=detailsURL,
            method="GET"
        )

        if res:
            b = BeautifulSoup(res, "html.parser")

            data: Tag = b.find_all("dd")

            name = data[0].text.strip()

            badges = []
            bad = BeautifulSoup(str(data[1]), "html.parser").find_all("span")
            for b in bad:
                t = b.text.strip()
                if t != "":
                    badges.append(t)

            coefMatiere = float(data[2].text.strip().replace(",", "."))
            prof = data[4].text.strip()
            rang = data[8].text.strip()
            min = float(data[10].text.strip())
            max = float(data[11].text.strip())
            mean = float(data[12].text.strip().replace(",", "."))

            return Details(name=name, badges=badges, coefMatiere=coefMatiere, prof=prof, rang=rang, min=min, max=max, mean=mean)
        else:
            return {
                "ok": False,
                "err": "Impossible d'importer les informations de la note"
            }


    async def mcc(self, return_zeros: bool = False) -> MCC:
        """
        Permet de récupérer les Modalités de Contrôle des Connaissances, les coefficients des UES et des matières

        :param return_zeros: Si True, les coefficients des UES et des matières seront retournés même si ils sont égaux à 0
        :return: Une instance de MCC
        """
        if not self.__profil:
            raise NotConnected()

        url = urljoin(self.BASE_URL, "/fr/tableau-de-bord")

        res = await self.request(
            url=url,
            method="GET",
        )

        if res:
            b = BeautifulSoup(res, "html.parser")

            competences = []
            data = []
            loaded = []
            id = 0
            for elem in b.find("table", {"class": "table table-striped"}).find("tbody").find_all("tr"):
                for idx, el in enumerate(elem.find_all("td")):
                    if idx == 0:
                        matiere = el.text.strip()
                    elif idx == 1:
                        coefs = []
                        for competence in elem.find_all("td")[1].text.strip().split("\n\n"):
                            name = competence.split(" ")[0]

                            if name not in loaded:
                                competences.append(
                                    Competence(
                                        id=id+1,
                                        name=name
                                    )
                                )

                                id += 1
                                loaded.append(name)

                            for i in range(0, len(competences)):
                                if competences[i].name == name:
                                    coefId = i
                                    break

                            if return_zeros:
                                coefs.append(
                                    Coefficient(
                                        id=coefId+1,
                                        coefficient=int(re.sub(r"[^0-9]", "", competence.split(" ")[1]).strip())
                                    )
                                )
                            else:
                                if int(re.sub(r"[^0-9]", "", competence.split(" ")[1]).strip()) > 0:
                                    coefs.append(
                                        Coefficient(
                                            id=coefId+1,
                                            coefficient=int(re.sub(r"[^0-9]", "", competence.split(" ")[1]).strip())
                                        )
                                    )

                        data.append(
                            MatiereCoefficient(
                                name=matiere,
                                coefficients=coefs
                            )
                        )

            return MCC(
                competences=competences,
                matieres=data
            )


    async def absences(self) -> list[Absence]:
        """
        Permet de récupérer les absences de l'utilisateur connecté
        
        :return: Une liste d'Absence
        """
        if not self.__profil:
            raise NotConnected()

        url = urljoin(self.BASE_URL, f"/fr/etudiant/profil/{self.__profil}/absences")

        res = await self.request(
            url=url,
            method="GET",
        )

        absences = []
        if res:
            b = BeautifulSoup(res, "html.parser")
            for elem in b.find("tbody").find_all("tr"):
                obj = {}
                for idx, el in enumerate(elem.find_all("td")):
                    if el.text.strip() == "Aucune absence n'a été saisie":
                        return absences

                    obj[idx] = el.text.strip()

                absences.append(
                    Absence(
                        date=stringToDatetime(obj[0]),
                        matiere=obj[1],
                        justifiee=False if obj[2]=="Non" else True,
                        saisie=obj[3]
                    )
                )

        return absences

