import os
import jwt
import datetime
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from dotenv import load_dotenv

# Charger les variables secrètes
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# Initialiser le hacheur de mots de passe Argon2
ph = PasswordHasher()

def hash_password(password: str) -> str:
    """Hache un mot de passe pour le stockage sécurisé."""
    return ph.hash(password)

def verify_password(hashed_password: str, plain_password: str) -> bool:
    """Vérifie si le mot de passe correspond au hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False

def create_access_token(data: dict, expires_delta: int = 24) -> str:
    """
    Génère un token JWT (JSON Web Token).
    expires_delta : durée de validité en heures.
    """
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(hours=expires_delta)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    """Décode et vérifie un token JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None # Le token a expiré
    except jwt.InvalidTokenError:
        return None # Le token est invalide