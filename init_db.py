# init_db.py
from database import engine, Base
# Il est impératif d'importer les modèles ici pour que SQLAlchemy les "voie"
# avant de créer les tables
from models import User, Client, Contract, Event

def init_db():
    print("Initialisation de la base de données...")
    
    # Cette ligne crée toutes les tables définies dans models.py
    # si elles n'existent pas déjà.
    Base.metadata.create_all(bind=engine)
    
    print("Tables créées avec succès !")

if __name__ == "__main__":
    init_db()