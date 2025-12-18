# Epic Events CRM

Application CRM sécurisée en ligne de commande (CLI) pour la gestion des clients, contrats et événements d'Epic Events.

## Description

Ce projet permet de gérer le processus commercial complet d'une entreprise d'événementiel via une interface terminal sécurisée. Il respecte une architecture stricte de séparation des pouvoirs entre les départements :
* **Gestion (Management) :** Gère les collaborateurs et les contrats.
* **Commercial :** Gère les clients et crée les événements.
* **Support :** Gère le déroulement des événements.

## Technologies

* **Langage :** Python 3.9+
* **Base de données :** PostgreSQL
* **ORM :** SQLAlchemy
* **Interface :** Click & Rich
* **Sécurité :** Argon2 (Hashage), JWT (Tokens), Gestion des permissions par rôle.

## Installation

1.  **Cloner le projet :**
    ```bash
    git clone [https://github.com/steveraffner/epicevents.git](https://github.com/steveraffner/epicevents.git)
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

## Guide des Commandes

Toutes les commandes s'exécutent via `python epicevents.py`.

### Authentification
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

### Gestion des Collaborateurs (Users)
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

### Gestion des Clients
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

### Gestion des Contrats
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

### Gestion des Événements
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
### Test & Monitoring (Sentry)

L'application est connectée à Sentry pour le suivi des erreurs.

Pour tester manuellement la remontée d'une erreur critique :
1. Ouvrez le fichier `epicevents.py`.
2. Décommentez les lignes de la commande `crash` (supprimez les `#`).
3. Lancez la commande :
   ```bash
   python epicevents.py crash
4. Vérifiez le dashboard Sentry pour voir l'alerte ZeroDivisionError.

---

## Sécurité

### Mesures de Sécurité Implémentées

Epic Events CRM intègre plusieurs niveaux de sécurité pour protéger les données et prévenir les attaques :

#### 1. **Hashage des mots de passe (Argon2)**
- Les mots de passe ne sont **jamais stockés en clair** dans la base de données
- Utilisation d'**Argon2**, l'algorithme de hashage recommandé (winner du Password Hashing Competition)
- Chaque mot de passe est hashé avec un **salt unique** automatique
- Protection contre les attaques par force brute et rainbow tables

#### 2. **Authentification JWT (JSON Web Tokens)**
- Système de tokens sécurisés pour l'authentification
- Tokens signés cryptographiquement avec une clé secrète
- Durée de validité limitée (24h par défaut)
- Validation automatique de l'expiration et de la signature

#### 3. **Sanitisation des Inputs**
Le module `sanitizer.py` protège contre plusieurs types d'attaques :
- **Injections SQL** : Suppression/échappement des caractères dangereux (`, `, `--`, etc.)
- **Attaques XSS** : Échappement des balises HTML (`<script>`, `<img>`, etc.)
- **Validation stricte** : Format email, téléphone, username, montants
- **Limitation de longueur** : Prévention des attaques par buffer overflow

#### 4. **Contrôle d'accès par rôle (RBAC)**
- Séparation stricte des permissions par département :
  - **Management** : Gestion des utilisateurs et contrats
  - **Commercial** : Gestion des clients et événements
  - **Support** : Gestion des événements assignés
- Vérification des permissions à chaque opération
- Isolation des données (un commercial ne peut modifier que ses clients)

#### 5. **Protection de la base de données**
- Utilisation d'un **ORM (SQLAlchemy)** pour éviter les injections SQL
- Requêtes paramétrées automatiques
- Validation des entrées avant insertion en base

### Schéma de la Base de Données

Consultez le fichier [database_schema.md](database_schema.md) pour visualiser :
- Le diagramme Mermaid complet de la base de données
- Les relations entre les tables
- Les contraintes et règles de gestion

### Tests de Sécurité

Le projet inclut une suite complète de tests de sécurité avec pytest :

```bash
# Installer pytest si nécessaire
pip install pytest

# Lancer tous les tests de sécurité
pytest test_security.py -v

# Lancer uniquement les tests de hashage
pytest test_security.py::TestPasswordHashing -v

# Lancer uniquement les tests JWT
pytest test_security.py::TestJWTTokens -v

# Lancer uniquement les tests de sanitisation
pytest test_security.py::TestInputSanitization -v
```

Les tests couvrent :
- ✅ Hashage Argon2 et vérification des mots de passe
- ✅ Création, validation et expiration des tokens JWT
- ✅ Sanitisation et validation des inputs
- ✅ Protection contre les injections SQL
- ✅ Protection contre les attaques XSS
- ✅ Validation des emails, usernames, montants
- ✅ Workflows complets d'authentification

### Configuration Sécurisée

1. **Fichier .env.example** : Un template de configuration est fourni
   ```bash
   # Créer votre fichier .env à partir du template
   cp .env.example .env
   ```

2. **Générer une SECRET_KEY forte** :
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

3. **Le fichier .env ne doit JAMAIS être commité** (il est dans `.gitignore`)

### Bonnes Pratiques

- ✅ Mots de passe hashés avec Argon2 (jamais en clair)
- ✅ Tokens JWT avec expiration (24h)
- ✅ Validation et sanitisation de tous les inputs utilisateur
- ✅ Contrôle d'accès basé sur les rôles (RBAC)
- ✅ ORM pour éviter les injections SQL
- ✅ Monitoring avec Sentry pour détecter les anomalies
- ✅ Tests automatisés de sécurité
- ✅ Template .env pour éviter l'exposition de secrets

---

## Tests

### Lancer les Tests

```bash
# Installation de pytest
pip install pytest

# Tous les tests
pytest -v

# Tests de sécurité uniquement
pytest test_security.py -v

# Tests avec rapport de couverture (si pytest-cov installé)
pytest --cov=. --cov-report=html
```
