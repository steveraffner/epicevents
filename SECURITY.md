# Guide de Sécurité - Epic Events CRM

## Vue d'ensemble

Ce document explique en détail les mesures de sécurité implémentées dans Epic Events CRM et comment elles protègent l'application contre les principales menaces.

## Table des Matières

1. [Architecture de Sécurité](#architecture-de-sécurité)
2. [Authentification et Mots de Passe](#authentification-et-mots-de-passe)
3. [Protection contre les Injections SQL](#protection-contre-les-injections-sql)
4. [Protection contre les Attaques XSS](#protection-contre-les-attaques-xss)
5. [Contrôle d'Accès](#contrôle-daccès)
6. [Tests de Sécurité](#tests-de-sécurité)
7. [Recommandations de Déploiement](#recommandations-de-déploiement)

---

## Architecture de Sécurité

```
┌─────────────────────────────────────────────────────────────┐
│                    Utilisateur (CLI)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
           ┌───────────────────────┐
           │  Sanitisation Input   │ ← sanitizer.py
           │  (validation + escape)│
           └───────────┬───────────┘
                       │
                       ▼
           ┌───────────────────────┐
           │  Authentification JWT │ ← utils.py
           │  (token validation)   │
           └───────────┬───────────┘
                       │
                       ▼
           ┌───────────────────────┐
           │  Contrôle d'Accès     │ ← controllers.py
           │  (RBAC par rôle)      │
           └───────────┬───────────┘
                       │
                       ▼
           ┌───────────────────────┐
           │  ORM SQLAlchemy       │ ← models.py
           │  (requêtes paramétrées)│
           └───────────┬───────────┘
                       │
                       ▼
           ┌───────────────────────┐
           │  Base PostgreSQL      │
           │  (données hashées)    │
           └───────────────────────┘
```

---

## Authentification et Mots de Passe

### 1. Hashage avec Argon2

**Problème résolu** : Stockage sécurisé des mots de passe

**Implémentation** :
- Algorithme : **Argon2id** (winner du Password Hashing Competition 2015)
- Bibliothèque : `argon2-cffi`
- Salt automatique et unique pour chaque mot de passe
- Paramètres optimisés pour la sécurité

**Code** ([utils.py](utils.py)) :
```python
from argon2 import PasswordHasher

ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)  # Génère automatiquement le salt

def verify_password(hashed_password: str, plain_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
```

**Pourquoi Argon2 ?**
- Résistant aux attaques GPU/ASIC (mémoire intensive)
- Protection contre les attaques par rainbow tables (salt unique)
- Recommandé par l'OWASP et le NIST
- Bien plus sûr que MD5, SHA1, ou même bcrypt

**Tests** :
```bash
pytest test_security.py::TestPasswordHashing -v
```
✅ Vérifie que les hashs sont différents même pour le même mot de passe  
✅ Vérifie qu'on ne peut pas retrouver le mot de passe original  
✅ Vérifie la vérification correcte des mots de passe

---

### 2. Tokens JWT (JSON Web Tokens)

**Problème résolu** : Authentification stateless et sécurisée

**Implémentation** :
- Algorithme : **HS256** (HMAC-SHA256)
- Bibliothèque : `PyJWT`
- Durée de vie : 24 heures (configurable)
- Stockage local : `.session` (jamais commité)

**Code** ([utils.py](utils.py)) :
```python
import jwt
from datetime import datetime, timedelta

def create_access_token(data: dict, expires_delta: int = 24) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token expiré
    except jwt.InvalidTokenError:
        return None  # Token invalide
```

**Avantages** :
- Pas besoin de session serveur (stateless)
- Signature cryptographique (impossible à falsifier sans la clé)
- Expiration automatique
- Contient les infos utilisateur (id, role) sans requête DB

**Tests** :
```bash
pytest test_security.py::TestJWTTokens -v
```
✅ Création et validation de tokens  
✅ Rejet des tokens expirés  
✅ Rejet des tokens invalides

---

## Protection contre les Injections SQL

### 1. ORM SQLAlchemy

**Problème résolu** : Injections SQL classiques

**Implémentation** :
- Toutes les requêtes passent par l'ORM SQLAlchemy
- **Aucune requête SQL brute** dans le code
- Requêtes paramétrées automatiques

**Exemple sûr** :
```python
# ✅ SÉCURISÉ - SQLAlchemy échappe automatiquement
user = db.query(User).filter(User.username == username).first()

# ❌ DANGEREUX - Ne JAMAIS faire ça
# query = f"SELECT * FROM users WHERE username = '{username}'"
```

**Pourquoi c'est sûr ?**
- SQLAlchemy utilise des requêtes préparées (prepared statements)
- Les valeurs sont passées séparément de la requête
- Impossible d'injecter du SQL dans les valeurs

---

### 2. Sanitisation des Inputs

**Problème résolu** : Injections SQL avancées, caractères malveillants

**Implémentation** ([sanitizer.py](sanitizer.py)) :

```python
class InputSanitizer:
    # Caractères dangereux détectés
    DANGEROUS_CHARS = ['<', '>', '"', "'", '\\', '/', ';', '--', '/*', '*/', 'xp_', 'sp_']
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        # 1. Strip des espaces
        value = value.strip()
        
        # 2. Limitation de longueur (buffer overflow)
        value = value[:max_length]
        
        # 3. Échappement HTML
        value = html.escape(value)
        
        # 4. Suppression des caractères de contrôle
        value = ''.join(char for char in value if ord(char) >= 32)
        
        # 5. Remplacement des patterns dangereux
        for dangerous in DANGEROUS_CHARS:
            value = re.sub(re.escape(dangerous), '_', value, flags=re.IGNORECASE)
        
        return value
```

**Tests d'injection SQL** :
```bash
pytest test_security.py::TestSecurityIntegration::test_sql_injection_prevention -v
```

**Exemples d'attaques bloquées** :
```python
# Entrée malveillante
malicious = "'; DROP TABLE users; --"

# Après sanitisation
sanitized = "'; DROP TABLE users; __"  # '--' remplacé par '__'
```

---

## Protection contre les Attaques XSS

**Problème résolu** : Injection de scripts malveillants

**Implémentation** :
- Échappement HTML avec `html.escape()`
- Conversion des balises en entités HTML

**Exemple** :
```python
# Entrée malveillante
xss_input = "<script>alert('XSS')</script>"

# Après sanitisation
sanitized = "&lt;script&gt;alert('XSS')&lt;/script&gt;"
```

**Résultat** :
- Le navigateur affiche le texte au lieu d'exécuter le script
- Impossible d'injecter du JavaScript

**Tests XSS** :
```bash
pytest test_security.py::TestSecurityIntegration::test_xss_prevention -v
```

---

## Contrôle d'Accès

### Architecture RBAC (Role-Based Access Control)

**Implémentation** : 3 rôles avec permissions strictes

```
┌─────────────┬──────────┬────────────┬─────────┬──────────┐
│             │  Users   │  Clients   │ Contracts│  Events  │
├─────────────┼──────────┼────────────┼─────────┼──────────┤
│ MANAGEMENT  │  CRUD    │  Read      │  CRUD   │  Update  │
│ COMMERCIAL  │  Read    │  CRUD*     │  Read   │  Create* │
│ SUPPORT     │  Read    │  Read      │  Read   │  Update* │
└─────────────┴──────────┴────────────┴─────────┴──────────┘

* Restrictions :
  - Commercial : Seulement ses propres clients et événements
  - Support : Seulement les événements qui lui sont assignés
```

### Vérifications de Permissions

**Code** ([controllers.py](controllers.py)) :

```python
class ClientController:
    def update_client(self, client_id, **kwargs):
        current_user = session.get_current_user_info()
        
        # 1. Vérification du rôle
        if current_user['role'] != "commercial":
            return None, "Seuls les COMMERCIAUX peuvent modifier des clients."
        
        # 2. Récupération du client
        client = self.db.query(Client).filter(Client.id == client_id).first()
        
        # 3. Vérification de propriété
        if client.commercial_contact_id != current_user['id']:
            return None, "Vous ne pouvez modifier que VOS propres clients."
        
        # 4. Autorisation accordée
        # ... mise à jour ...
```

**Principe de moindre privilège** :
- Chaque rôle n'a accès qu'aux données dont il a besoin
- Vérification systématique à chaque opération
- Isolation complète entre les commerciaux (ne voient que leurs clients)

---

## Tests de Sécurité

### Suite de Tests Complète

Le fichier [test_security.py](test_security.py) contient **40+ tests** couvrant tous les aspects de sécurité.

### Lancer les Tests

```bash
# Installation
pip install pytest pytest-cov

# Tous les tests de sécurité
pytest test_security.py -v

# Avec rapport de couverture
pytest test_security.py --cov=. --cov-report=html

# Tests spécifiques
pytest test_security.py::TestPasswordHashing -v
pytest test_security.py::TestJWTTokens -v
pytest test_security.py::TestInputSanitization -v
```

### Catégories de Tests

#### 1. Tests de Hashage (TestPasswordHashing)
✅ Création de hashs Argon2  
✅ Unicité des hashs (salt)  
✅ Vérification correcte des mots de passe  
✅ Impossible de retrouver le mot de passe original

#### 2. Tests JWT (TestJWTTokens)
✅ Création de tokens  
✅ Décodage de tokens valides  
✅ Rejet de tokens invalides  
✅ Rejet de tokens expirés  
✅ Présence de l'expiration

#### 3. Tests de Sanitisation (TestInputSanitization)
✅ Nettoyage de chaînes basiques  
✅ Échappement HTML  
✅ Protection SQL injection  
✅ Limitation de longueur  
✅ Suppression des espaces  
✅ Validation emails valides/invalides  
✅ Validation usernames  
✅ Validation passwords (complexité)  
✅ Validation montants  
✅ Échappement SQL LIKE

#### 4. Tests d'Intégration (TestSecurityIntegration)
✅ Workflow complet d'authentification  
✅ Workflow d'enregistrement utilisateur  
✅ Prévention injections SQL  
✅ Prévention attaques XSS

### Exemple de Sortie

```
test_security.py::TestPasswordHashing::test_hash_password_creates_hash PASSED
test_security.py::TestPasswordHashing::test_different_passwords_different_hashes PASSED
test_security.py::TestPasswordHashing::test_same_password_different_hashes_salt PASSED
test_security.py::TestPasswordHashing::test_verify_password_correct PASSED
test_security.py::TestPasswordHashing::test_verify_password_incorrect PASSED
...

================================== 42 passed in 2.34s ==================================
```

---

## Recommandations de Déploiement

### Configuration Sécurisée

#### 1. Variables d'Environnement

```bash
# ✅ FAIRE : Utiliser .env (jamais commité)
cp .env.example .env
nano .env  # Éditer avec vos vraies valeurs

# ❌ NE PAS FAIRE : Hardcoder dans le code
SECRET_KEY = "ma_cle_en_dur"  # DANGER !
```

#### 2. Générer une SECRET_KEY Forte

```bash
# Générer une clé aléatoire de 64 bytes
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Exemple de sortie :
# kL9mN2pQ8rS5tU7vW1xY3zA4bC6dE9fG0hI2jK4lM6nO8pQ1rS3tU5vW7xY9zA2bC4dE6fG8h
```

#### 3. Sécurité PostgreSQL

```sql
-- Créer un utilisateur dédié avec privilèges limités
CREATE USER epicevents_user WITH PASSWORD 'strong_password_here';
CREATE DATABASE epicevents_db OWNER epicevents_user;

-- Révoquer les privilèges par défaut
REVOKE ALL ON DATABASE epicevents_db FROM PUBLIC;

-- Accorder uniquement les privilèges nécessaires
GRANT CONNECT ON DATABASE epicevents_db TO epicevents_user;
GRANT ALL PRIVILEGES ON DATABASE epicevents_db TO epicevents_user;
```

#### 4. Firewall et Réseau

```bash
# Limiter l'accès PostgreSQL aux IPs locales uniquement
# Dans postgresql.conf :
listen_addresses = 'localhost'

# Dans pg_hba.conf :
local   epicevents_db   epicevents_user   scram-sha-256
host    epicevents_db   epicevents_user   127.0.0.1/32   scram-sha-256
```

### Checklist de Sécurité

Avant de déployer en production :

- [ ] `.env` configuré avec des valeurs uniques
- [ ] `SECRET_KEY` générée aléatoirement (64+ bytes)
- [ ] Mots de passe DB forts (16+ caractères)
- [ ] PostgreSQL accessible uniquement en local
- [ ] `.env` dans `.gitignore` (ne JAMAIS commiter)
- [ ] Tests de sécurité passent (100%)
- [ ] Sentry configuré pour le monitoring
- [ ] Logs d'accès activés
- [ ] Backups réguliers configurés
- [ ] Certificats SSL si accès distant

### Monitoring avec Sentry

```python
# Les événements de sécurité sont loggés automatiquement
sentry_sdk.capture_message(f"Nouveau collaborateur créé : {username}", level="info")
sentry_sdk.capture_message(f"Contrat {contract_id} SIGNÉ !", level="info")
```

**Configurer Sentry** :
1. Créer un compte sur [sentry.io](https://sentry.io)
2. Créer un projet Python
3. Copier le DSN dans `.env` :
   ```
   SENTRY_DSN=https://xxx@sentry.io/yyy
   ```

---

## Résumé des Protections

| Menace                  | Protection                          | Statut |
|------------------------|-------------------------------------|--------|
| Mots de passe volés    | Hashage Argon2 + Salt              | ✅     |
| Tokens falsifiés       | Signature JWT (HS256)              | ✅     |
| Injections SQL         | ORM + Sanitisation                 | ✅     |
| Attaques XSS           | Échappement HTML                   | ✅     |
| Accès non autorisés    | RBAC (contrôle par rôle)          | ✅     |
| Buffer overflow        | Limitation longueur inputs         | ✅     |
| Brute force            | Hashage lent (Argon2)             | ✅     |
| Session hijacking      | Token expiration (24h)             | ✅     |
| Secrets exposés        | .env + .gitignore                  | ✅     |
| Anomalies non détectées| Monitoring Sentry                  | ✅     |

---

## Ressources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Argon2 Specification](https://github.com/P-H-C/phc-winner-argon2)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/14/faq/security.html)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
