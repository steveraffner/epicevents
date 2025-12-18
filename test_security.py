"""
Tests de sécurité pour Epic Events CRM.
Ce module teste les mécanismes de sécurité implémentés dans l'application.
"""

import pytest
import jwt
from datetime import datetime, timedelta
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import os

# Définir une SECRET_KEY de test si elle n'existe pas
os.environ.setdefault('SECRET_KEY', 'test_secret_key_for_testing_only_not_for_production_use')

# Import des modules à tester
from utils import hash_password, verify_password, create_access_token, decode_token
from sanitizer import InputSanitizer, sanitize_input


class TestPasswordHashing:
    """Tests pour le hashage des mots de passe avec Argon2."""
    
    def test_hash_password_creates_hash(self):
        """Vérifie que le hashage crée bien un hash."""
        password = "MonMotDePasse123"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 50  # Les hashs Argon2 sont longs
        assert hashed.startswith('$argon2')  # Format Argon2
    
    def test_different_passwords_different_hashes(self):
        """Vérifie que deux mots de passe différents donnent des hashs différents."""
        password1 = "Password123"
        password2 = "Password456"
        
        hash1 = hash_password(password1)
        hash2 = hash_password(password2)
        
        assert hash1 != hash2
    
    def test_same_password_different_hashes_salt(self):
        """Vérifie que le même mot de passe donne des hashs différents (salt)."""
        password = "SamePassword123"
        
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Les hashs doivent être différents à cause du salt
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Vérifie que la vérification fonctionne avec le bon mot de passe."""
        password = "CorrectPassword123"
        hashed = hash_password(password)
        
        assert verify_password(hashed, password) is True
    
    def test_verify_password_incorrect(self):
        """Vérifie que la vérification échoue avec un mauvais mot de passe."""
        password = "CorrectPassword123"
        wrong_password = "WrongPassword456"
        hashed = hash_password(password)
        
        assert verify_password(hashed, wrong_password) is False
    
    def test_password_never_stored_plaintext(self):
        """Vérifie qu'on ne peut pas retrouver le mot de passe original."""
        password = "SecretPassword123"
        hashed = hash_password(password)
        
        # Le hash ne doit pas contenir le mot de passe en clair
        assert password not in hashed


class TestJWTTokens:
    """Tests pour les tokens JWT."""
    
    def test_create_token(self):
        """Vérifie qu'un token est bien créé."""
        data = {"user_id": 1, "username": "testuser", "role": "commercial"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20
    
    def test_decode_valid_token(self):
        """Vérifie qu'un token valide peut être décodé."""
        data = {"user_id": 1, "username": "testuser", "role": "commercial"}
        token = create_access_token(data)
        
        decoded = decode_token(token)
        
        assert decoded is not None
        assert decoded["user_id"] == 1
        assert decoded["username"] == "testuser"
        assert decoded["role"] == "commercial"
        assert "exp" in decoded  # Doit contenir une expiration
    
    def test_decode_invalid_token(self):
        """Vérifie qu'un token invalide retourne None."""
        invalid_token = "invalid.token.here"
        decoded = decode_token(invalid_token)
        
        assert decoded is None
    
    def test_decode_expired_token(self):
        """Vérifie qu'un token expiré retourne None."""
        data = {"user_id": 1, "username": "testuser"}
        
        # Créer un token déjà expiré
        secret_key = os.getenv("SECRET_KEY", "test_secret_key")
        expire = datetime.utcnow() - timedelta(hours=1)  # Expiré il y a 1h
        to_encode = data.copy()
        to_encode.update({"exp": expire})
        expired_token = jwt.encode(to_encode, secret_key, algorithm="HS256")
        
        decoded = decode_token(expired_token)
        
        assert decoded is None
    
    def test_token_contains_expiration(self):
        """Vérifie que le token contient bien une date d'expiration."""
        data = {"user_id": 1}
        token = create_access_token(data, expires_delta=24)
        decoded = decode_token(token)
        
        assert "exp" in decoded
        exp_timestamp = decoded["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        now = datetime.utcnow()
        
        # L'expiration doit être dans le futur
        assert exp_datetime > now
        # Et environ 24h dans le futur
        delta = exp_datetime - now
        assert 23 <= delta.total_seconds() / 3600 <= 25  # Entre 23 et 25h


class TestInputSanitization:
    """Tests pour la sanitisation des inputs."""
    
    def test_sanitize_basic_string(self):
        """Vérifie la sanitisation d'une chaîne basique."""
        value = "Hello World"
        sanitized = InputSanitizer.sanitize_string(value)
        
        assert sanitized == "Hello World"
    
    def test_sanitize_removes_html(self):
        """Vérifie que les balises HTML sont échappées."""
        value = "<script>alert('XSS')</script>"
        sanitized = InputSanitizer.sanitize_string(value)
        
        assert "<script>" not in sanitized
        assert "&lt;script&gt;" in sanitized or sanitized != value
    
    def test_sanitize_removes_sql_injection(self):
        """Vérifie que les tentatives d'injection SQL sont neutralisées."""
        value = "test'; DROP TABLE users;--"
        sanitized = InputSanitizer.sanitize_string(value)
        
        # Les caractères dangereux doivent être remplacés
        assert "DROP TABLE" not in sanitized or "--" not in sanitized
    
    def test_sanitize_max_length(self):
        """Vérifie que la longueur maximale est respectée."""
        value = "A" * 1000
        sanitized = InputSanitizer.sanitize_string(value, max_length=100)
        
        assert len(sanitized) <= 100
    
    def test_sanitize_strips_whitespace(self):
        """Vérifie que les espaces en début/fin sont supprimés."""
        value = "  test  "
        sanitized = InputSanitizer.sanitize_string(value)
        
        assert sanitized == "test"
    
    def test_validate_email_valid(self):
        """Vérifie la validation d'un email valide."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "first+last@company.org"
        ]
        
        for email in valid_emails:
            is_valid, error = InputSanitizer.validate_email(email)
            assert is_valid is True, f"Email {email} devrait être valide"
            assert error is None
    
    def test_validate_email_invalid(self):
        """Vérifie la validation d'emails invalides."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user name@example.com",
            "user@domain",
        ]
        
        for email in invalid_emails:
            is_valid, error = InputSanitizer.validate_email(email)
            assert is_valid is False, f"Email {email} devrait être invalide"
            assert error is not None
    
    def test_validate_username_valid(self):
        """Vérifie la validation d'un nom d'utilisateur valide."""
        valid_usernames = [
            "john_doe",
            "user123",
            "test-user",
            "ABC"
        ]
        
        for username in valid_usernames:
            is_valid, error = InputSanitizer.validate_username(username)
            assert is_valid is True, f"Username {username} devrait être valide"
            assert error is None
    
    def test_validate_username_invalid(self):
        """Vérifie la validation de noms d'utilisateur invalides."""
        invalid_usernames = [
            "ab",  # Trop court
            "user name",  # Espaces
            "user@name",  # Caractère non autorisé
            "A" * 100,  # Trop long
            "",  # Vide
        ]
        
        for username in invalid_usernames:
            is_valid, error = InputSanitizer.validate_username(username)
            assert is_valid is False, f"Username {username} devrait être invalide"
            assert error is not None
    
    def test_validate_password_valid(self):
        """Vérifie la validation d'un mot de passe valide."""
        valid_passwords = [
            "Password123",
            "MySecureP@ssw0rd",
            "Test1234",
        ]
        
        for password in valid_passwords:
            is_valid, error = InputSanitizer.validate_password(password)
            assert is_valid is True, f"Password {password} devrait être valide"
            assert error is None
    
    def test_validate_password_invalid(self):
        """Vérifie la validation de mots de passe invalides."""
        invalid_passwords = [
            "short",  # Trop court
            "alllowercase123",  # Pas de majuscule
            "ALLUPPERCASE123",  # Pas de minuscule
            "NoNumbers",  # Pas de chiffre
        ]
        
        for password in invalid_passwords:
            is_valid, error = InputSanitizer.validate_password(password)
            assert is_valid is False, f"Password devrait être invalide"
            assert error is not None
    
    def test_validate_amount_valid(self):
        """Vérifie la validation d'un montant valide."""
        valid_amounts = [
            ("100.50", 100.50),
            ("1000", 1000.0),
            (1234.56, 1234.56),
            ("999999", 999999.0),
        ]
        
        for amount, expected in valid_amounts:
            is_valid, error, value = InputSanitizer.validate_amount(amount)
            assert is_valid is True
            assert error is None
            assert value == expected
    
    def test_validate_amount_invalid(self):
        """Vérifie la validation de montants invalides."""
        invalid_amounts = [
            "-100",  # Négatif
            "not_a_number",  # Pas un nombre
            "999999999999",  # Trop grand
        ]
        
        for amount in invalid_amounts:
            is_valid, error, value = InputSanitizer.validate_amount(amount)
            assert is_valid is False
            assert error is not None
            assert value is None
    
    def test_sanitize_sql_like(self):
        """Vérifie l'échappement des caractères LIKE SQL."""
        value = "test_%value"
        sanitized = InputSanitizer.sanitize_sql_like(value)
        
        assert r"\%" in sanitized
        assert r"\_" in sanitized


class TestSecurityIntegration:
    """Tests d'intégration pour la sécurité globale."""
    
    def test_password_workflow(self):
        """Teste le workflow complet de gestion de mot de passe."""
        # 1. Valider le mot de passe
        password = "SecurePass123"
        is_valid, error = InputSanitizer.validate_password(password)
        assert is_valid is True
        
        # 2. Hasher le mot de passe
        hashed = hash_password(password)
        assert hashed != password
        
        # 3. Vérifier le mot de passe
        assert verify_password(hashed, password) is True
        assert verify_password(hashed, "WrongPass123") is False
    
    def test_user_registration_security(self):
        """Teste la sécurité lors de l'enregistrement d'un utilisateur."""
        # Données d'entrée potentiellement dangereuses
        username = "user<script>alert('xss')</script>"
        email = "test@example.com"
        password = "Password123"
        
        # Sanitisation
        username_valid, error, username_clean = sanitize_input(username, "username")
        assert username_valid is False  # Doit être invalide à cause des caractères spéciaux
        
        # Email valide
        email_valid, error, email_clean = sanitize_input(email, "email")
        assert email_valid is True
        
        # Mot de passe valide et hashé
        pwd_valid, error, pwd_clean = sanitize_input(password, "password")
        assert pwd_valid is True
        hashed = hash_password(password)
        assert hashed != password
    
    def test_sql_injection_prevention(self):
        """Teste la prévention des injections SQL."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--",
        ]
        
        for malicious in malicious_inputs:
            sanitized = InputSanitizer.sanitize_string(malicious)
            # Les caractères dangereux doivent être neutralisés
            assert "--" not in sanitized or ";" not in sanitized
    
    def test_xss_prevention(self):
        """Teste la prévention des attaques XSS."""
        xss_attempts = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
        ]
        
        for xss in xss_attempts:
            sanitized = InputSanitizer.sanitize_string(xss)
            # Les balises HTML doivent être échappées
            assert "<script>" not in sanitized
            assert "<img" not in sanitized or "&lt;" in sanitized


# Configuration pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
