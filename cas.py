from config import config

from exception import UnknownError


from requests import Response, request

from bs4 import BeautifulSoup
from typing import Union


class CAS:
    def __init__(self):
        self.BASE_URL = config.get('service').get('BASE_URL')

        self.headers = {
            "User-Agent": config.get('userAgent'),
        }


    def request(self, url: str, method: str, data: dict = None, headers: dict = None, redirect: bool = True, raw: bool = False) -> Union[Response, dict, str]:
        """
        Permet d'effectuer une requête HTTP avec la session courante

        :param url: URL de la requête
        :param method: Méthode de la requête
        :param data: Données de la requête
        :param headers: Headers de la requête
        :param redirect: Redirection autorisée ou pas
        :param raw: Retourne la réponse brute
        :return: Réponse de la requête
        """
        if headers:
            hd = headers
        else:
            hd = self.headers

        response = request(method=method, url=url, data=data, headers=hd, allow_redirects=redirect)

        if raw:
            return response

        try:
            return response.json()
        except:
            return response.text

    
    async def createSession(self, SERVICE_URL: str, redirectURL: str) -> bool:
        """
        Permet de récupérer le cookie PHPSESSID
        
        :param redirectURL: URL de redirection
        :return: Un booleen indiquant si la connection a reussi
        """
        resp = self.request(
            url=redirectURL,
            method="GET",
            redirect=False,
            raw=True
        )

        cookies = resp.headers.get("set-cookie", [])
        PHPSESSID = cookies

        if PHPSESSID:
            headers = {
                "Cookie": PHPSESSID
            }

            resp2 = self.request(
                url=SERVICE_URL,
                method="GET",
                headers=headers,
                redirect=False,
                raw=True
            )
            
            cookies2 = resp2.headers.get("set-cookie", [])
            PHPSESSID2 = cookies2

            if PHPSESSID2:
                self.headers = {
                    **self.headers,
                    "Cookie": PHPSESSID2
                }

                return True
            else:
                raise UnknownError("Impossible de récupérer le cookie PHPSESSID ! (2eme requête)")
        else:
            raise UnknownError("Impossible de récupérer le cookie PHPSESSID ! (1ere requête)")
        


    async def getTokenData(self, url: str) -> str:
        """
        Permet de récupérer le token d'authentification
        
        :param url: URL de la requête
        :return: Token d'authentification
        """
        resp = self.request(
            url=url,
            method="GET",
            raw=True
        )

        b = BeautifulSoup(resp.text, "html.parser")
        data = b.find_all("input", {"type": "hidden"})
        if len(data) > 0:
            return str(data[0]).split("value=\"")[1].split("\"/>")[0]
        else:
            UnknownError("Impossible de récupérer le token d'authentification !")
    