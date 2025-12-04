import sentry_sdk
from models import User, UserRole, Client, Contract, Event
from datetime import datetime
from sqlalchemy.orm import Session
from models import User, UserRole
from utils import hash_password
from session import session

class UserController:
    def __init__(self, db: Session):
        self.db = db

    def _check_permission(self):
        """Vérifie si l'utilisateur connecté est du département MANAGEMENT"""
        current_user = session.get_current_user_info()
        if not current_user:
            return False, "Vous devez être connecté."
        
        if current_user['role'] != "management":
            return False, "Accès refusé. Réservé à l'équipe GESTION."
        
        return True, None

    def create_user(self, username, email, password, role):
        # 1. Vérification des permissions
        authorized, message = self._check_permission()
        if not authorized:
            return None, message

        # 2. Vérifier si l'utilisateur existe déjà
        if self.db.query(User).filter(User.username == username).first():
            return None, f"L'utilisateur '{username}' existe déjà."

        # 3. Création
        new_user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=UserRole(role) # Conversion du string en Enum
        )
        self.db.add(new_user)
        self.db.commit()

        # --- LOG SENTRY ---
        sentry_sdk.capture_message(f"Nouveau collaborateur créé : {username} ({role})", level="info")
        # ------------------

        return new_user, "Utilisateur créé avec succès."

    def list_users(self):
        # Tout le monde peut voir la liste (lecture seule), pas de restriction stricte ici
        # sauf être connecté
        if not session.get_current_user_info():
             return None, "Vous devez être connecté."
        
        return self.db.query(User).all(), None

    def update_user(self, user_id, **kwargs):
        authorized, message = self._check_permission()
        if not authorized:
            return None, message

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None, "Utilisateur non trouvé."

        # Mise à jour des champs
        for key, value in kwargs.items():
            if value: # Si une valeur est fournie
                if key == "password":
                    user.password_hash = hash_password(value)
                elif key == "role":
                    user.role = UserRole(value)
                else:
                    setattr(user, key, value)
        
        self.db.commit()

        # --- LOG SENTRY ---
        sentry_sdk.capture_message(f"Collaborateur modifié : ID {user_id}", level="info")
        # ------------------

        return user, "Utilisateur mis à jour."

    def delete_user(self, user_id):
        authorized, message = self._check_permission()
        if not authorized:
            return False, message

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "Utilisateur non trouvé."

        self.db.delete(user)
        self.db.commit()
        return True, "Utilisateur supprimé."


class ClientController:
    def __init__(self, db: Session):
        self.db = db

    def list_clients(self):
        """Tout le monde peut voir les clients"""
        if not session.get_current_user_info():
             return None, "Vous devez être connecté."
        return self.db.query(Client).all(), None

    def create_client(self, full_name, email, phone, company_name):
        current_user = session.get_current_user_info()
        
        # 1. Seuls les commerciaux peuvent créer des clients
        if not current_user or current_user['role'] != "commercial":
            return None, "Seuls les COMMERCIAUX peuvent créer des clients."

        # 2. Création du client (associé automatiquement au commercial connecté)
        new_client = Client(
            full_name=full_name,
            email=email,
            phone=phone,
            company_name=company_name,
            commercial_contact_id=current_user['id']  # <-- Association automatique
        )
        
        self.db.add(new_client)
        self.db.commit()
        return new_client, "Client créé avec succès."

    def update_client(self, client_id, **kwargs):
        current_user = session.get_current_user_info()
        
        # 1. Vérification du rôle
        if not current_user or current_user['role'] != "commercial":
            return None, "Seuls les COMMERCIAUX peuvent modifier des clients."

        # 2. Récupération du client
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return None, "Client non trouvé."

        # 3. Vérification : Le commercial est-il responsable de ce client ?
        if client.commercial_contact_id != current_user['id']:
            return None, "Vous ne pouvez modifier que VOS propres clients."

        # 4. Mise à jour (et mise à jour automatique de la date de dernier contact)
        for key, value in kwargs.items():
            if value:
                setattr(client, key, value)
        
        client.last_contact_date = datetime.now() # Mise à jour auto de la date
        
        self.db.commit()
        return client, "Client mis à jour."


class ContractController:
    def __init__(self, db: Session):
        self.db = db

    def list_contracts(self, filter_signed=None, filter_paid=None):
        """
        Lister les contrats avec des filtres optionnels.
        filter_signed: True/False/None
        filter_paid: True (payé), False (non payé), None (tous)
        """
        if not session.get_current_user_info():
             return None, "Vous devez être connecté."
        
        query = self.db.query(Contract)

        # Filtre sur le statut signé/non signé
        if filter_signed is not None:
            # En BDD on a stocké "true"/"false" en string (selon votre modèle initial)
            # ou booléen selon l'implémentation. Le modèle a mis String "false".
            status_str = "true" if filter_signed else "false"
            query = query.filter(Contract.status == status_str)

        # Filtre sur le paiement (Reste à payer > 0)
        if filter_paid is False:
            query = query.filter(Contract.remaining_amount > 0)
        elif filter_paid is True:
            query = query.filter(Contract.remaining_amount == 0)

        return query.all(), None

    def create_contract(self, client_id, total_amount, remaining_amount):
        current_user = session.get_current_user_info()
        
        # 1. Seule la GESTION peut créer des contrats 
        if not current_user or current_user['role'] != "management":
            return None, "Seule l'équipe GESTION peut créer des contrats."

        # 2. Vérifier que le client existe
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return None, "Client introuvable."

        new_contract = Contract(
            client_id=client_id,
            total_amount=total_amount,
            remaining_amount=remaining_amount,
            status="false" # Créé non signé par défaut
        )
        
        self.db.add(new_contract)
        self.db.commit()
        return new_contract, "Contrat créé avec succès."

    def update_contract(self, contract_id, **kwargs):
        current_user = session.get_current_user_info()
        if not current_user:
            return None, "Connexion requise."

        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return None, "Contrat introuvable."

        # 1. Vérification des droits
        is_management = current_user['role'] == "management"
        is_commercial = current_user['role'] == "commercial"
        
        # Le commercial doit "posséder" le client lié au contrat
        is_owner = False
        if is_commercial and contract.client.commercial_contact_id == current_user['id']:
            is_owner = True

        if not (is_management or is_owner):
            return None, "Droit refusé. Vous n'êtes ni Gestionnaire, ni le Commercial responsable."

        # 2. Mise à jour
        contract_was_signed = False # Flag pour savoir si on vient de signer
        
        for key, value in kwargs.items():
            if value is not None: 
                if key == "status": 
                     value = str(value).lower()
                     # Si le statut passe à "true" alors qu'il ne l'était pas avant
                     if value == "true" and contract.status != "true":
                         contract_was_signed = True
                setattr(contract, key, value)
        
        self.db.commit()
        
        # --- LOG SENTRY ---
        if contract_was_signed:
            # ATTENTION : Il faut bien 12 espaces avant sentry_sdk ici (3 tabulations)
            sentry_sdk.capture_message(f"Contrat {contract_id} SIGNÉ !", level="info")
        # ------------------

        return contract, "Contrat mis à jour."


class EventController:
    def __init__(self, db: Session):
        self.db = db

    def list_events(self, filter_no_support=None, filter_my_events=None):
        current_user = session.get_current_user_info()
        if not current_user:
             return None, "Vous devez être connecté."
        
        query = self.db.query(Event)

        # Filtre "Pas de support assigné" (Pour la Gestion)
        if filter_no_support:
            query = query.filter(Event.support_contact_id == None)

        # Filtre "Mes événements" (Pour le Support)
        if filter_my_events:
            query = query.filter(Event.support_contact_id == current_user['id'])

        return query.all(), None

    def create_event(self, contract_id, date_start, date_end, location, attendees, notes):
        current_user = session.get_current_user_info()
        
        # 1. Seuls les COMMERCIAUX peuvent créer des événements
        if not current_user or current_user['role'] != "commercial":
            return None, "Seule l'équipe COMMERCIAL peut créer des événements."

        # 2. Vérifier que le contrat existe et est signé
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            return None, "Contrat introuvable."
        if contract.status != "true":
            return None, "Impossible de créer un événement pour un contrat NON SIGNÉ."
        
        # 3. Vérifier que le commercial est bien le responsable du client
        if contract.client.commercial_contact_id != current_user['id']:
            return None, "Vous ne pouvez créer des événements que pour vos propres clients."

        new_event = Event(
            contract_id=contract_id,
            event_date_start=date_start,
            event_date_end=date_end,
            location=location,
            attendees=attendees,
            notes=notes
        )
        
        self.db.add(new_event)
        self.db.commit()
        return new_event, "Événement créé avec succès."

    def update_event(self, event_id, **kwargs):
        current_user = session.get_current_user_info()
        if not current_user:
            return None, "Connexion requise."

        event = self.db.query(Event).filter(Event.id == event_id).first()
        if not event:
            return None, "Événement introuvable."

        role = current_user['role']
        
        # Cas 1 : GESTION (peut tout faire, mais surtout assigner le support)
        if role == "management":
            # On laisse passer la mise à jour
            pass
        
        # Cas 2 : SUPPORT (ne peut modifier que SES événements)
        elif role == "support":
            if event.support_contact_id != current_user['id']:
                return None, "Vous ne pouvez modifier que les événements qui vous sont assignés."
        
        # Cas 3 : COMMERCIAL (n'a pas le droit de modifier les événements selon le cahier des charges strict)
        # Mais dans la pratique, on pourrait imaginer qu'il puisse, ici on bloque pour respecter la consigne.
        else:
            return None, "Votre rôle ne vous permet pas de modifier les événements."

        # Mise à jour
        for key, value in kwargs.items():
            if value is not None:
                setattr(event, key, value)
        
        self.db.commit()
        return event, "Événement mis à jour."