#!/usr/bin/env python3
"""
Script para gerar licenças de teste.
Uso: python scripts/generate_test_license.py [quantidade]
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.infrastructure.db.database import SessionLocal
from app.infrastructure.repositories.license_repository import LicenseRepository
from app.domain.models.license import LicenseType

def generate_test_licenses(count: int = 1):
    """Gera licenças de teste"""
    db: Session = SessionLocal()
    license_repo = LicenseRepository(db)
    
    try:
        print(f"Gerando {count} licença(s) de teste...")
        
        for i in range(count):
            license_data = {
                "license_type": LicenseType.PRO,
                "purchase_email": f"test{i+1}@example.com",
                "purchase_platform": "test",
                "purchase_transaction_id": f"TEST-{i+1:04d}"
            }
            
            license = license_repo.create(license_data)
            print(f"✅ Licença {i+1}: {license.license_key}")
        
        print(f"\n🎉 {count} licença(s) gerada(s) com sucesso!")
        print("\nVocê pode usar essas chaves para testar o registro de usuários.")
        
    except Exception as e:
        print(f"❌ Erro ao gerar licenças: {e}")
    finally:
        db.close()

def main():
    """Função principal"""
    count = 1
    
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
            if count <= 0:
                raise ValueError("Quantidade deve ser maior que zero")
        except ValueError as e:
            print(f"❌ Erro: {e}")
            print("Uso: python scripts/generate_test_license.py [quantidade]")
            sys.exit(1)
    
    generate_test_licenses(count)

if __name__ == "__main__":
    main()
