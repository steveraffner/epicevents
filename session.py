import json
import os
from utils import decode_token

SESSION_FILE = ".session"

class SessionManager:
    def save_token(self, token):
        """Sauvegarde le token dans un fichier local .session"""
        with open(SESSION_FILE, "w") as f:
            json.dump({"token": token}, f)

    def load_token(self):
        """Charge le token depuis le fichier local s'il existe"""
        if not os.path.exists(SESSION_FILE):
            return None
        try:
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)
                return data.get("token")
        except (json.JSONDecodeError, FileNotFoundError):
            return None

    def get_current_user_info(self):
        """Récupère les infos de l'utilisateur connecté depuis le token"""
        token = self.load_token()
        if not token:
            return None
        
        # On décode le token pour lire ce qu'il y a dedans (username, role, etc.)
        payload = decode_token(token)
        return payload

    def logout(self):
        """Supprime le fichier de session pour déconnecter l'utilisateur"""
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)

# On crée une instance unique qu'on pourra importer partout
session = SessionManager()