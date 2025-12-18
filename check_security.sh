#!/bin/bash

# Script de vérification de la sécurité Epic Events CRM
# Usage: ./check_security.sh

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║         🔒 VÉRIFICATION DE SÉCURITÉ - EPIC EVENTS CRM 🔒            ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Compteurs
passed=0
failed=0

echo "📋 Vérification des fichiers de sécurité..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Vérifier les fichiers essentiels
files_to_check=(
    "sanitizer.py"
    "test_security.py"
    ".env.example"
    "SECURITY.md"
    "database_schema.md"
    ".gitignore"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   ${GREEN}✓${NC} $file existe"
        ((passed++))
    else
        echo -e "   ${RED}✗${NC} $file manquant"
        ((failed++))
    fi
done

echo ""
echo "📦 Vérification des dépendances Python..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Vérifier les packages Python
packages=(
    "pytest"
    "argon2-cffi"
    "pyjwt"
    "sqlalchemy"
)

for package in "${packages[@]}"; do
    if python3 -c "import ${package//-/_}" 2>/dev/null; then
        echo -e "   ${GREEN}✓${NC} $package installé"
        ((passed++))
    else
        echo -e "   ${YELLOW}⚠${NC} $package non installé (pip install $package)"
        ((failed++))
    fi
done

echo ""
echo "🧪 Exécution des tests de sécurité..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Lancer les tests
if [ -f "test_security.py" ]; then
    if pytest test_security.py -q --tb=no 2>/dev/null; then
        echo -e "   ${GREEN}✓${NC} Tous les tests de sécurité passent"
        ((passed++))
    else
        echo -e "   ${RED}✗${NC} Certains tests échouent"
        ((failed++))
        echo ""
        echo "   Pour plus de détails: pytest test_security.py -v"
    fi
else
    echo -e "   ${RED}✗${NC} Fichier test_security.py introuvable"
    ((failed++))
fi

echo ""
echo "🔐 Vérification de la configuration..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Vérifier .env
if [ -f ".env" ]; then
    echo -e "   ${GREEN}✓${NC} Fichier .env existe"
    
    # Vérifier SECRET_KEY
    if grep -q "SECRET_KEY=" .env; then
        secret_key=$(grep "SECRET_KEY=" .env | cut -d '=' -f2)
        if [ ${#secret_key} -gt 30 ]; then
            echo -e "   ${GREEN}✓${NC} SECRET_KEY configurée (${#secret_key} caractères)"
            ((passed++))
        else
            echo -e "   ${YELLOW}⚠${NC} SECRET_KEY trop courte (${#secret_key} caractères)"
            echo "      Générez une clé forte: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            ((failed++))
        fi
    else
        echo -e "   ${RED}✗${NC} SECRET_KEY non configurée dans .env"
        ((failed++))
    fi
else
    echo -e "   ${YELLOW}⚠${NC} Fichier .env n'existe pas"
    echo "      Copiez .env.example: cp .env.example .env"
    ((failed++))
fi

# Vérifier .gitignore
if [ -f ".gitignore" ]; then
    if grep -q "^\.env$" .gitignore; then
        echo -e "   ${GREEN}✓${NC} .env est dans .gitignore"
        ((passed++))
    else
        echo -e "   ${RED}✗${NC} .env n'est pas dans .gitignore (DANGER !)"
        ((failed++))
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 RÉSULTAT FINAL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

total=$((passed + failed))
percentage=$((passed * 100 / total))

echo ""
echo "   Vérifications réussies: ${GREEN}$passed${NC}"
echo "   Vérifications échouées: ${RED}$failed${NC}"
echo "   Score de sécurité:      $percentage%"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "   ${GREEN}✓ Excellente sécurité ! Toutes les vérifications passent.${NC}"
    exit 0
elif [ $percentage -ge 80 ]; then
    echo -e "   ${YELLOW}⚠ Bonne sécurité, mais quelques améliorations possibles.${NC}"
    exit 1
else
    echo -e "   ${RED}✗ Attention ! Des problèmes de sécurité ont été détectés.${NC}"
    exit 2
fi
