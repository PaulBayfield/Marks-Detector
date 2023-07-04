class InvalidCredentials(Exception):
    def __init__(self, error):
        self.error = error
        super().__init__(self.error)


class UnknownError(Exception):
    def __init__(self, error):
        self.error = error
        super().__init__(self.error)


class NotConnected(Exception):
    def __init__(self):
        self.error = "Aucune session n'est actuellement ouverte ! Merci d'utiliser la méthode profile après avoir utilisé la méthode login."
        super().__init__(self.error)
