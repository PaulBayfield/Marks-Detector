# Marks Detector

Authentification de l'intranet de l'IUT RCC en Python. Permet de récupérer toutes les notes et coefficients de toutes les matières.


# Installation

```sh
git clone https://github.com/PaulBayfield/Marks-Detector

cd Marks-Detector
```

Modifier le fichier [main.py](main.py) avec vos identifiants.
Puis lancez le script.

```sh
python3 main.py
```


# Connecion à l'intranet de l'IUT RCC

```py
from client import Client

import asyncio


USERNAME = ""
PASSWORD = ""


async def main():
    client = Client("https://iut-rcc-intranet.univ-reims.fr/sso/cas")
    status = await client.login(USERNAME, PASSWORD)
    if status:
        profil = await client.profile()
        print("Connexion réussie !\n\nConnecté en tant que", profil, "\n\n")

asyncio.run(main())
```
[Example dans le fichier main.py](main.py)