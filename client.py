from config import config
from objects import Matiere, Note, Details
from exception import InvalidCredentials, UnknownError, NotConnected


import re
import math

from cas import CAS
from bs4 import BeautifulSoup
from urllib.parse import urlencode, urljoin


class Client(CAS):
    def __init__(self, service: str):
        super().__init__()

        self.CAS_BASE_URL = config.get('cas').get('BASE_URL')
        self.SERVICE_URL = service

        self.profil = None


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
            "execution": await super().getTokenData(url),
            "_eventId": "submit",
            "geolocation": ""
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": config.get('userAgent')
        }

        resp = super().request(
            url=url,
            method="POST",
            data=urlencode(data),
            headers=headers,
            raw=True, 
            redirect=False
        )

        location = resp.headers.get("location", "")

        if "ticket" in location:
            return await super().createSession(self.SERVICE_URL, location)
        else:
            raise InvalidCredentials("Impossible de se connecter avec les identifiants fournis ! Vérifiez-les et réessayez.")


    
    async def profile(self) -> str:
        """
        Permet de récupérer le nom complet de l'utilisateur connecté

        :return: Le nom complet de l'utilisateur connecté
        """
        url = urljoin(self.BASE_URL, "/fr/utilisateur/mon-profil")

        res = self.request(
            url=url,
            method="GET"
        )

        if res:
            b = BeautifulSoup(res, "html.parser")

            self.profil = re.compile(r"\/fr\/etudiant\/profil\/(.*\..*)\/.*").match(str(b.find("a", {"class": "nav-link changeprofil"})).split("href=\"")[1].split("\"")[0])[1]
            return self.profil
        else:
            raise UnknownError("Nom complet introuvable")


    async def notes(self) -> dict:
        """
        Permet de récupérer les notes de l'utilisateur connecté
        
        :return: Un dictionnaire contenant les matières et les notes de l'utilisateur connecté
        """
        if not self.profil:
            raise NotConnected()

        url = urljoin(self.BASE_URL, f"/fr/etudiant/profil/{self.profil}/notes")

        res = self.request(
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
                            _data = float(_data.replace(",", "."))

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


    async def noteInfo(self, detailsURL: str) -> str:
        """
        Permet de récupérer les informations d'une note
        
        :param detailsURL: L'URL de la note
        :return: Un dictionnaire contenant les informations de la note
        """
        detailsURL = urljoin(self.BASE_URL, detailsURL)

        res = self.request(
            url=detailsURL,
            method="GET"
        )

        if res:
            b = BeautifulSoup(res, "html.parser")

            data = b.find_all("dd")

            name = data[0].text.strip()

            badges = []
            bad = data[1].find_all("</span>")
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


    async def coefficients(self) -> dict:
        """
        Permet de récupérer les coefficients des UES

        :return: Un dictionnaire contenant les coefficients des UES
        """
        if not self.profil:
            raise NotConnected()

        url = urljoin(self.BASE_URL, "/fr/tableau-de-bord")

        res = self.request(
            url=url,
            method="GET",
        )

        if res:
            b = BeautifulSoup(res, "html.parser")

            UEs = []
            data = []
            loaded = []
            id = 0
            for elem in b.find("table", {"class": "table table-striped"}).find("tbody").find_all("tr"):
                for idx, el in enumerate(elem.find_all("td")):
                    if idx == 0:
                        matiere = el.text.strip()
                    elif idx == 1:
                        coefs = []
                        for UE in elem.find_all("td")[1].text.strip().split("\n\n"):
                            name = UE.split(" ")[0]

                            if name not in loaded:
                                UEs.append({
                                    "id": id,
                                    "name": name
                                })

                                id += 1
                                loaded.append(name)

                            for _id, _name in enumerate(UEs):
                                if _name["name"] == name:
                                    name = _id
                                    break

                            coefs.append({
                                "id": _id,
                                "coef": int(re.sub(r"[^0-9]", "", UE.split(" ")[1]).strip())
                            })

                        data.append({
                            "matiere": matiere,
                            "coefs": coefs
                        })

            return {
                "UEs": UEs,
                "data": data
            }
