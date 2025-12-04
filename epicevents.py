
import os
import sentry_sdk
from dotenv import load_dotenv
from rich.table import Table
import click
from rich.console import Console
from database import get_db
from models import User
from utils import verify_password, create_access_token
from session import session
from controllers import UserController, ClientController, ContractController, EventController # <-- je les ajoutes ici

# Chargement des variables d'environnement
load_dotenv()

# Initialisation de Sentry
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    # Taux d'échantillonnage des traces (1.0 = capture 100% des transactions pour le débogage)
    traces_sample_rate=1.0,
    # Capture les informations locales (variables) pour aider au débogage
    send_default_pii=True
)

console = Console()

@click.group()
def cli():
    """Application CRM Epic Events"""
    pass

@cli.command()
@click.option("--username", prompt="Nom d'utilisateur", help="Votre nom d'utilisateur")
@click.option("--password", prompt="Mot de passe", hide_input=True, help="Votre mot de passe")
def login(username, password):
    """Se connecter à l'application"""
    db = next(get_db())
    
    # 1. Chercher l'utilisateur dans la BDD
    user = db.query(User).filter(User.username == username).first()
    
    # 2. Vérifier si l'utilisateur existe et si le mot de passe est bon
    if not user or not verify_password(user.password_hash, password):
        console.print("[bold red]Erreur : Nom d'utilisateur ou mot de passe incorrect.[/bold red]")
        return

    # 3. Créer le token avec les infos importantes (id, username, role)
    # Note : user.role.value permet de récupérer la chaîne "management" au lieu de l'objet Enum
    access_token = create_access_token(
        data={"sub": user.username, "id": user.id, "role": user.role.value}
    )
    
    # 4. Sauvegarder le token
    session.save_token(access_token)
    
    console.print(f"[bold green]Connexion réussie ! Bienvenue {user.username}.[/bold green]")

@cli.command()
def logout():
    """Se déconnecter"""
    session.logout()
    console.print("[bold yellow]Vous avez été déconnecté.[/bold yellow]")

@cli.command()
def whoami():
    """Affiche l'utilisateur connecté (Test)"""
    user_info = session.get_current_user_info()
    if user_info:
        console.print(f"Connecté en tant que : [bold blue]{user_info['sub']}[/bold blue] (Rôle : {user_info['role']})")
    else:
        console.print("[red]Vous n'êtes pas connecté.[/red]")


# --- GROUPE UTILISATEURS ---
@cli.group()
def users():
    """Gestion des collaborateurs (Réservé GESTION)"""
    pass

@users.command("list")
def list_users():
    """Lister tous les collaborateurs"""
    db = next(get_db())
    controller = UserController(db)
    users_list, error = controller.list_users()

    if error:
        console.print(f"[bold red]{error}[/bold red]")
        return

    # Création du tableau avec Rich
    table = Table(title="Liste des Collaborateurs")
    table.add_column("ID", style="cyan")
    table.add_column("Username", style="magenta")
    table.add_column("Email")
    table.add_column("Rôle", style="green")

    for user in users_list:
        table.add_row(str(user.id), user.username, user.email, user.role.value)

    console.print(table)

@users.command("create")
@click.option("--username", prompt=True)
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@click.option("--role", type=click.Choice(['management', 'commercial', 'support'], case_sensitive=False), prompt=True)
def create_user(username, email, password, role):
    """Créer un nouveau collaborateur"""
    db = next(get_db())
    controller = UserController(db)
    
    new_user, message = controller.create_user(username, email, password, role)
    
    if new_user:
        console.print(f"[bold green]{message}[/bold green]")
    else:
        console.print(f"[bold red]{message}[/bold red]")

@users.command("update")
@click.argument("user_id", type=int)
@click.option("--username", help="Nouveau nom d'utilisateur")
@click.option("--email", help="Nouvel email")
@click.option("--role", type=click.Choice(['management', 'commercial', 'support']), help="Nouveau rôle")
@click.option("--password", help="Nouveau mot de passe")
def update_user(user_id, username, email, role, password):
    """Modifier un collaborateur (via son ID)"""
    db = next(get_db())
    controller = UserController(db)
    
    updated_user, message = controller.update_user(user_id, username=username, email=email, role=role, password=password)
    
    if updated_user:
        console.print(f"[bold green]{message}[/bold green]")
    else:
        console.print(f"[bold red]{message}[/bold red]")

@users.command("delete")
@click.argument("user_id", type=int)
def delete_user(user_id):
    """Supprimer un collaborateur"""
    db = next(get_db())
    controller = UserController(db)
    
    success, message = controller.delete_user(user_id)
    
    if success:
        console.print(f"[bold green]{message}[/bold green]")
    else:
        console.print(f"[bold red]{message}[/bold red]")
        

# --- GROUPE CLIENTS ---
@cli.group()
def clients():
    """Gestion des clients (Réservé COMMERCIAL)"""
    pass

@clients.command("list")
def list_clients():
    """Lister tous les clients"""
    db = next(get_db())
    controller = ClientController(db)
    clients_list, error = controller.list_clients()

    if error:
        console.print(f"[bold red]{error}[/bold red]")
        return

    table = Table(title="Liste des Clients")
    table.add_column("ID", style="cyan")
    table.add_column("Nom complet", style="magenta")
    table.add_column("Email")
    table.add_column("Entreprise", style="green")
    table.add_column("Commercial Responsable", style="blue")

    for client in clients_list:
        commercial_name = client.commercial_contact.username if client.commercial_contact else "Aucun"
        table.add_row(str(client.id), client.full_name, client.email, client.company_name, commercial_name)

    console.print(table)

@clients.command("create")
@click.option("--full_name", prompt="Nom complet")
@click.option("--email", prompt="Email")
@click.option("--phone", prompt="Téléphone")
@click.option("--company", prompt="Nom de l'entreprise")
def create_client(full_name, email, phone, company):
    """Créer un client (Commercial uniquement)"""
    db = next(get_db())
    controller = ClientController(db)
    
    new_client, message = controller.create_client(full_name, email, phone, company)
    
    if new_client:
        console.print(f"[bold green]{message}[/bold green]")
    else:
        console.print(f"[bold red]{message}[/bold red]")

@clients.command("update")
@click.argument("client_id", type=int)
@click.option("--full_name", help="Nouveau nom")
@click.option("--email", help="Nouvel email")
@click.option("--phone", help="Nouveau téléphone")
@click.option("--company", help="Nouvelle entreprise")
def update_client(client_id, full_name, email, phone, company):
    """Mettre à jour un client (Responsable uniquement)"""
    db = next(get_db())
    controller = ClientController(db)
    
    updated_client, message = controller.update_client(
        client_id, full_name=full_name, email=email, phone=phone, company_name=company
    )
    
    if updated_client:
        console.print(f"[bold green]{message}[/bold green]")
    else:
        console.print(f"[bold red]{message}[/bold red]")


# --- GROUPE CONTRATS ---
@cli.group()
def contracts():
    """Gestion des contrats (Gestion & Commercial)"""
    pass

@contracts.command("list")
@click.option("--signed", is_flag=True, help="Filtrer uniquement les contrats SIGNÉS")
@click.option("--not-signed", is_flag=True, help="Filtrer uniquement les contrats NON SIGNÉS")
@click.option("--not-paid", is_flag=True, help="Filtrer les contrats NON PAYÉS (Reste > 0)")
def list_contracts(signed, not_signed, not_paid):
    """Lister les contrats (Filtres disponibles)"""
    db = next(get_db())
    controller = ContractController(db)
    
    # Logique des filtres
    filter_signed = None
    if signed: filter_signed = True
    if not_signed: filter_signed = False
    
    filter_paid = None
    if not_paid: filter_paid = False # On veut ceux qui ne sont PAS payés

    contracts_list, error = controller.list_contracts(filter_signed, filter_paid)

    if error:
        console.print(f"[bold red]{error}[/bold red]")
        return

    table = Table(title="Liste des Contrats")
    table.add_column("ID", style="cyan")
    table.add_column("Client", style="magenta")
    table.add_column("Total", justify="right")
    table.add_column("Reste à payer", justify="right", style="red")
    table.add_column("Statut", style="green")

    for contract in contracts_list:
        client_name = contract.client.full_name if contract.client else "Inconnu"
        # Affichage propre du statut
        status_display = "✅ Signé" if contract.status == "true" else "❌ Non signé"
        
        table.add_row(
            str(contract.id), 
            client_name, 
            str(contract.total_amount), 
            str(contract.remaining_amount), 
            status_display
        )

    console.print(table)

@contracts.command("create")
@click.option("--client_id", type=int, prompt="ID du Client")
@click.option("--amount", type=float, prompt="Montant Total")
@click.option("--remaining", type=float, prompt="Montant Restant")
def create_contract(client_id, amount, remaining):
    """Créer un contrat (Gestion uniquement)"""
    db = next(get_db())
    controller = ContractController(db)
    
    new_contract, message = controller.create_contract(client_id, amount, remaining)
    
    if new_contract:
        console.print(f"[bold green]{message}[/bold green]")
    else:
        console.print(f"[bold red]{message}[/bold red]")

@contracts.command("update")
@click.argument("contract_id", type=int)
@click.option("--amount", type=float, help="Nouveau montant total")
@click.option("--remaining", type=float, help="Nouveau montant restant")
@click.option("--signed", is_flag=True, help="Marquer comme SIGNÉ")
def update_contract(contract_id, amount, remaining, signed):
    """Modifier un contrat (Gestion ou Commercial resp.)"""
    db = next(get_db())
    controller = ContractController(db)
    
    # On gère le statut : si le flag --signed est mis, on passe status=True
    new_status = True if signed else None

    updated_contract, message = controller.update_contract(
        contract_id, total_amount=amount, remaining_amount=remaining, status=new_status
    )
    
    if updated_contract:
        console.print(f"[bold green]{message}[/bold green]")
    else:
        console.print(f"[bold red]{message}[/bold red]")

# --- GROUPE ÉVÉNEMENTS ---
@cli.group()
def events():
    """Gestion des événements (Commercial, Support, Gestion)"""
    pass

@events.command("list")
@click.option("--no-support", is_flag=True, help="Afficher les événements sans support assigné")
@click.option("--my-events", is_flag=True, help="Afficher uniquement MES événements (Support)")
def list_events(no_support, my_events):
    """Lister les événements"""
    db = next(get_db())
    controller = EventController(db)
    
    events_list, error = controller.list_events(filter_no_support=no_support, filter_my_events=my_events)

    if error:
        console.print(f"[bold red]{error}[/bold red]")
        return

    table = Table(title="Liste des Événements")
    table.add_column("ID", style="cyan")
    table.add_column("Contrat ID", style="magenta")
    table.add_column("Client")
    table.add_column("Date Début", style="green")
    table.add_column("Support", style="blue")
    table.add_column("Lieu")

    for event in events_list:
        client_name = event.contract.client.full_name if (event.contract and event.contract.client) else "Inconnu"
        support_name = event.support_contact.username if event.support_contact else "[red]Aucun[/red]"
        start_date = str(event.event_date_start) if event.event_date_start else "Non définie"
        
        table.add_row(
            str(event.id), 
            str(event.contract_id), 
            client_name, 
            start_date, 
            support_name,
            event.location or ""
        )

    console.print(table)

@events.command("create")
@click.option("--contract_id", type=int, prompt="ID du Contrat")
@click.option("--start", type=click.DateTime(), prompt="Date de début (YYYY-MM-DD HH:MM:SS)")
@click.option("--end", type=click.DateTime(), prompt="Date de fin (YYYY-MM-DD HH:MM:SS)")
@click.option("--location", prompt="Lieu")
@click.option("--attendees", type=int, prompt="Nombre de participants")
@click.option("--notes", prompt="Notes", default="")
def create_event(contract_id, start, end, location, attendees, notes):
    """Créer un événement (Commercial uniquement)"""
    db = next(get_db())
    controller = EventController(db)
    
    new_event, message = controller.create_event(contract_id, start, end, location, attendees, notes)
    
    if new_event:
        console.print(f"[bold green]{message}[/bold green]")
    else:
        console.print(f"[bold red]{message}[/bold red]")

@events.command("update")
@click.argument("event_id", type=int)
@click.option("--support_id", type=int, help="Assigner un membre support (Gestion uniquement)")
@click.option("--location", help="Nouveau lieu")
@click.option("--attendees", type=int, help="Nouveau nombre de participants")
@click.option("--notes", help="Mise à jour des notes")
def update_event(event_id, support_id, location, attendees, notes):
    """Modifier un événement (Support ou Gestion)"""
    db = next(get_db())
    controller = EventController(db)
    
    updated_event, message = controller.update_event(
        event_id, support_contact_id=support_id, location=location, attendees=attendees, notes=notes
    )
    
    if updated_event:
        console.print(f"[bold green]{message}[/bold green]")
    else:
        console.print(f"[bold red]{message}[/bold red]")

# --- COMMANDE DE TEST SENTRY (COMMENTÉE) ---
# @cli.command()
# def crash():
#     """Fait planter l'application pour tester Sentry"""
#     division_par_zero = 1 / 0


if __name__ == "__main__":
    cli()