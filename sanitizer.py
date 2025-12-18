"""
Module de sanitisation et validation des inputs pour Epic Events CRM.
Ce module fournit des fonctions pour nettoyer et valider les données utilisateur
afin de prévenir les injections et assurer l'intégrité des données.
"""

import re
import html
from typing import Optional, Union


class InputSanitizer:
    """Classe pour sanitiser et valider les inputs utilisateur."""
    
    # Patterns de validation
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^[\d\s\-\+\(\)\.]{8,20}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,50}$')
    
    # Caractères dangereux à supprimer ou échapper
    DANGEROUS_CHARS = ['<', '>', '"', "'", '\\', '/', ';', '--', '/*', '*/', 'xp_', 'sp_']
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 255, allow_special: bool = False) -> str:
        """
        Nettoie une chaîne de caractères en supprimant les caractères dangereux.
        
        Args:
            value: La chaîne à nettoyer
            max_length: Longueur maximale autorisée
            allow_special: Si False, supprime les caractères spéciaux HTML
            
        Returns:
            Chaîne nettoyée
        """
        if not value or not isinstance(value, str):
            return ""
        
        # Supprimer les espaces en début/fin
        value = value.strip()
        
        # Limiter la longueur
        value = value[:max_length]
        
        # Échapper les caractères HTML si non autorisés
        if not allow_special:
            value = html.escape(value)
        
        # Supprimer les caractères null et autres caractères de contrôle
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
        
        # Vérifier les patterns d'injection SQL
        for dangerous in InputSanitizer.DANGEROUS_CHARS:
            if dangerous.lower() in value.lower():
                # Remplacer par des underscores
                value = re.sub(re.escape(dangerous), '_', value, flags=re.IGNORECASE)
        
        return value
    
    @staticmethod
    def validate_email(email: str) -> tuple[bool, Optional[str]]:
        """
        Valide une adresse email.
        
        Args:
            email: L'email à valider
            
        Returns:
            Tuple (est_valide, message_erreur)
        """
        if not email:
            return False, "L'email ne peut pas être vide."
        
        email = email.strip().lower()
        
        if len(email) > 255:
            return False, "L'email est trop long (max 255 caractères)."
        
        if not InputSanitizer.EMAIL_PATTERN.match(email):
            return False, "Format d'email invalide."
        
        return True, None
    
    @staticmethod
    def validate_phone(phone: str) -> tuple[bool, Optional[str]]:
        """
        Valide un numéro de téléphone.
        
        Args:
            phone: Le numéro à valider
            
        Returns:
            Tuple (est_valide, message_erreur)
        """
        if not phone:
            return True, None  # Le téléphone est optionnel
        
        phone = phone.strip()
        
        if not InputSanitizer.PHONE_PATTERN.match(phone):
            return False, "Format de téléphone invalide (8-20 caractères, chiffres et symboles autorisés: + - ( ) . espace)."
        
        return True, None
    
    @staticmethod
    def validate_username(username: str) -> tuple[bool, Optional[str]]:
        """
        Valide un nom d'utilisateur.
        
        Args:
            username: Le nom d'utilisateur à valider
            
        Returns:
            Tuple (est_valide, message_erreur)
        """
        if not username:
            return False, "Le nom d'utilisateur ne peut pas être vide."
        
        username = username.strip()
        
        if not InputSanitizer.USERNAME_PATTERN.match(username):
            return False, "Le nom d'utilisateur doit contenir 3-50 caractères alphanumériques, tirets ou underscores uniquement."
        
        return True, None
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, Optional[str]]:
        """
        Valide un mot de passe selon les critères de sécurité.
        
        Args:
            password: Le mot de passe à valider
            
        Returns:
            Tuple (est_valide, message_erreur)
        """
        if not password:
            return False, "Le mot de passe ne peut pas être vide."
        
        if len(password) < 8:
            return False, "Le mot de passe doit contenir au moins 8 caractères."
        
        if len(password) > 128:
            return False, "Le mot de passe est trop long (max 128 caractères)."
        
        # Vérifier la complexité
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            return False, "Le mot de passe doit contenir au moins une majuscule, une minuscule et un chiffre."
        
        return True, None
    
    @staticmethod
    def validate_amount(amount: Union[str, float, int]) -> tuple[bool, Optional[str], Optional[float]]:
        """
        Valide et convertit un montant financier.
        
        Args:
            amount: Le montant à valider
            
        Returns:
            Tuple (est_valide, message_erreur, valeur_convertie)
        """
        try:
            if isinstance(amount, str):
                # Supprimer les espaces et remplacer virgule par point
                amount = amount.strip().replace(',', '.')
            
            amount_float = float(amount)
            
            if amount_float < 0:
                return False, "Le montant ne peut pas être négatif.", None
            
            if amount_float > 999999999.99:
                return False, "Le montant est trop élevé.", None
            
            # Arrondir à 2 décimales
            amount_float = round(amount_float, 2)
            
            return True, None, amount_float
            
        except (ValueError, TypeError):
            return False, "Format de montant invalide.", None
    
    @staticmethod
    def validate_integer(value: Union[str, int], min_value: int = 0, max_value: int = 999999) -> tuple[bool, Optional[str], Optional[int]]:
        """
        Valide et convertit un entier.
        
        Args:
            value: La valeur à valider
            min_value: Valeur minimale autorisée
            max_value: Valeur maximale autorisée
            
        Returns:
            Tuple (est_valide, message_erreur, valeur_convertie)
        """
        try:
            if isinstance(value, str):
                value = value.strip()
            
            value_int = int(value)
            
            if value_int < min_value:
                return False, f"La valeur doit être au moins {min_value}.", None
            
            if value_int > max_value:
                return False, f"La valeur ne peut pas dépasser {max_value}.", None
            
            return True, None, value_int
            
        except (ValueError, TypeError):
            return False, "Format numérique invalide.", None
    
    @staticmethod
    def sanitize_sql_like(value: str) -> str:
        """
        Échappe les caractères spéciaux pour les requêtes SQL LIKE.
        
        Args:
            value: La chaîne à échapper
            
        Returns:
            Chaîne échappée
        """
        if not value:
            return ""
        
        # Échapper les wildcards SQL
        value = value.replace('\\', '\\\\')
        value = value.replace('%', r'\%')
        value = value.replace('_', r'\_')
        
        return value


def sanitize_input(value: str, field_type: str = "string", **kwargs) -> tuple[bool, Optional[str], any]:
    """
    Fonction principale pour sanitiser et valider un input selon son type.
    
    Args:
        value: La valeur à sanitiser
        field_type: Type de champ (string, email, phone, username, password, amount, integer)
        **kwargs: Arguments supplémentaires pour la validation
        
    Returns:
        Tuple (est_valide, message_erreur, valeur_sanitisée)
    """
    sanitizer = InputSanitizer()
    
    if field_type == "email":
        is_valid, error = sanitizer.validate_email(value)
        return is_valid, error, value.strip().lower() if is_valid else None
    
    elif field_type == "phone":
        is_valid, error = sanitizer.validate_phone(value)
        return is_valid, error, value.strip() if is_valid else None
    
    elif field_type == "username":
        is_valid, error = sanitizer.validate_username(value)
        return is_valid, error, value.strip() if is_valid else None
    
    elif field_type == "password":
        is_valid, error = sanitizer.validate_password(value)
        return is_valid, error, value if is_valid else None
    
    elif field_type == "amount":
        return sanitizer.validate_amount(value)
    
    elif field_type == "integer":
        min_val = kwargs.get('min_value', 0)
        max_val = kwargs.get('max_value', 999999)
        return sanitizer.validate_integer(value, min_val, max_val)
    
    else:  # string par défaut
        max_length = kwargs.get('max_length', 255)
        allow_special = kwargs.get('allow_special', False)
        sanitized = sanitizer.sanitize_string(value, max_length, allow_special)
        return True, None, sanitized
