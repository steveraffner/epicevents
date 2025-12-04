# Epic Events CRM

Application CRM sécurisée en ligne de commande (CLI) pour la gestion des clients, contrats et événements d'Epic Events.

## 📋 Description

Ce projet permet de gérer le processus commercial complet d'une entreprise d'événementiel via une interface terminal sécurisée. Il respecte une architecture stricte de séparation des pouvoirs entre les départements :
* **Gestion (Management) :** Gère les collaborateurs et les contrats.
* **Commercial :** Gère les clients et crée les événements.
* **Support :** Gère le déroulement des événements.

## 🛠 Technologies

* **Langage :** Python 3.9+
* **Base de données :** PostgreSQL
* **ORM :** SQLAlchemy
* **Interface :** Click & Rich
* **Sécurité :** Argon2 (Hashage), JWT (Tokens), Gestion des permissions par rôle.

## 🚀 Installation

1.  **Cloner le projet :**
    ```bash
    git clone [https://github.com/VOTRE_USERNAME/epicevents.git](https://github.com/VOTRE_USERNAME/epicevents.git)
    cd epicevents
    ```

2.  **Créer et activer l'environnement virtuel :**
    * Mac/Linux :
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    * Windows :
        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```

3.  **Installer les dépendances :**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration (.env) :**
    Créez un fichier `.env` à la racine avec vos informations PostgreSQL :
    ```ini
    DB_HOST=localhost
    DB_NAME=epicevents_db
    DB_USER=votre_user_mac_ou_windows
    DB_PASSWORD=
    DB_PORT=5432
    SECRET_KEY=une_chaine_tres_longue_et_secrete
    ```

5.  **Initialisation de la Base de Données :**
    Assurez-vous que PostgreSQL est lancé, puis :
    ```bash
    # Créer la DB (si ce n'est pas déjà fait)
    createdb epicevents_db
    
    # Créer les tables
    python init_db.py
    ```

6.  **Créer le premier Administrateur :**
    Lancez ce script pour créer un utilisateur avec le rôle "Management" :
    ```bash
    python create_superuser.py
    ```

---

## 📖 Guide des Commandes

Toutes les commandes s'exécutent via `python epicevents.py`.

### 🔐 Authentification
* **Se connecter :**
    ```bash
    python epicevents.py login
    ```
* **Voir l'utilisateur connecté :**
    ```bash
    python epicevents.py whoami
    ```
* **Se déconnecter :**
    ```bash
    python epicevents.py logout
    ```

### 👥 Gestion des Collaborateurs (Users)
*Réservé au département GESTION.*

* **Lister les collaborateurs :**
    ```bash
    python epicevents.py users list
    ```
* **Créer un collaborateur :**
    ```bash
    python epicevents.py users create
    # Suivre les instructions interactives pour le rôle (management, commercial, support)
    ```
* **Modifier un collaborateur :**
    ```bash
    python epicevents.py users update [USER_ID] --role support --email nouveau@email.com
    ```
* **Supprimer un collaborateur :**
    ```bash
    python epicevents.py users delete [USER_ID]
    ```

### 💼 Gestion des Clients
*Création réservée aux COMMERCIAUX. Lecture pour tous.*

* **Lister les clients :**
    ```bash
    python epicevents.py clients list
    ```
* **Créer un client :**
    ```bash
    python epicevents.py clients create
    ```
* **Modifier un client (Seulement si vous en êtes le responsable) :**
    ```bash
    python epicevents.py clients update [CLIENT_ID] --phone "0600000000"
    ```

### 📝 Gestion des Contrats
*Création réservée à la GESTION.*

* **Lister les contrats :**
    ```bash
    python epicevents.py contracts list
    ```
    *Filtres disponibles :*
    * `--signed` : Voir uniquement les contrats signés.
    * `--not-paid` : Voir les contrats non soldés.
* **Créer un contrat :**
    ```bash
    python epicevents.py contracts create
    ```
* **Modifier un contrat :**
    ```bash
    python epicevents.py contracts update [CONTRACT_ID] --signed --amount 5000
    ```

### 🎉 Gestion des Événements
*Création réservée aux COMMERCIAUX (si contrat signé).*

* **Lister les événements :**
    ```bash
    python epicevents.py events list
    ```
    *Filtres disponibles :*
    * `--no-support` : Événements sans support (Utile pour la Gestion).
    * `--my-events` : Mes événements assignés (Utile pour le Support).
* **Créer un événement :**
    ```bash
    python epicevents.py events create
    ```
* **Modifier un événement :**
    * *Gestion :* Pour assigner un support.
        ```bash
        python epicevents.py events update [EVENT_ID] --support_id [USER_ID]
        ```
    * *Support :* Pour mettre à jour les notes/lieu.
        ```bash
        python epicevents.py events update [EVENT_ID] --notes "Traiteur OK"
        ```