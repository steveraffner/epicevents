from database import get_db
from models import User, UserRole
from utils import hash_password

def create_admin():
    # Récupérer une session de base de données
    db = next(get_db())
    
    print("--- Création de l'utilisateur Administrateur ---")
    username = input("Nom d'utilisateur : ")
    email = input("Email : ")
    password = input("Mot de passe : ")
    
    # Vérifier si l'utilisateur existe déjà
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        print("Erreur : Cet utilisateur existe déjà.")
        return

    # Création de l'objet User
    new_user = User(
        username=username,
        email=email,
        password_hash=hash_password(password), # On hache le mot de passe ici !
        role=UserRole.MANAGEMENT # On lui donne le rôle de gestionnaire
    )
    
    # Enregistrement en base
    try:
        db.add(new_user)
        db.commit()
        print(f"✅ Succès ! L'utilisateur {username} (MANAGEMENT) a été créé.")
    except Exception as e:
        print(f"Erreur lors de la création : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()