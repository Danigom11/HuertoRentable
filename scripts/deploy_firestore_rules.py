#!/usr/bin/env python3
"""
Script para desplegar reglas de Firestore de forma segura
"""
import subprocess
import sys
import os
from pathlib import Path

def check_firebase_cli():
    """Verificar que Firebase CLI esté instalado"""
    try:
        result = subprocess.run(['firebase', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"✅ Firebase CLI detectado: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Firebase CLI no encontrado")
        print("📥 Instala Firebase CLI con: npm install -g firebase-tools")
        return False

def check_firebase_login():
    """Verificar que el usuario esté autenticado en Firebase"""
    try:
        result = subprocess.run(['firebase', 'projects:list'], 
                              capture_output=True, text=True, check=True)
        print("✅ Usuario autenticado en Firebase")
        return True
    except subprocess.CalledProcessError:
        print("❌ No estás autenticado en Firebase")
        print("🔐 Ejecuta: firebase login")
        return False

def validate_rules():
    """Validar sintaxis de las reglas localmente"""
    rules_file = Path("firestore.rules")
    if not rules_file.exists():
        print("❌ Archivo firestore.rules no encontrado")
        return False
    
    try:
        # Leer y validar estructura básica
        with open(rules_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificaciones básicas
        if "rules_version = '2'" not in content:
            print("❌ Version de reglas incorrecta")
            return False
        
        if "service cloud.firestore" not in content:
            print("❌ Declaración de servicio faltante")
            return False
        
        print("✅ Sintaxis básica de reglas validada")
        return True
        
    except Exception as e:
        print(f"❌ Error validando reglas: {e}")
        return False

def deploy_rules_dry_run():
    """Hacer dry run del despliegue"""
    try:
        print("🧪 Ejecutando dry run...")
        result = subprocess.run([
            'firebase', 'firestore:rules', 
            '--dry-run'
        ], capture_output=True, text=True, check=True)
        
        print("✅ Dry run exitoso")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ Error en dry run:")
        print(e.stderr)
        return False

def deploy_rules():
    """Desplegar las reglas a Firestore"""
    try:
        print("🚀 Desplegando reglas de Firestore...")
        result = subprocess.run([
            'firebase', 'deploy', '--only', 'firestore:rules'
        ], capture_output=True, text=True, check=True)
        
        print("✅ Reglas desplegadas exitosamente")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ Error desplegando reglas:")
        print(e.stderr)
        return False

def backup_current_rules():
    """Hacer backup de las reglas actuales"""
    try:
        print("💾 Haciendo backup de reglas actuales...")
        result = subprocess.run([
            'firebase', 'firestore:rules', 'get'
        ], capture_output=True, text=True, check=True)
        
        # Guardar backup
        backup_file = Path("firestore.rules.backup")
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        print(f"✅ Backup guardado en {backup_file}")
        return True
        
    except subprocess.CalledProcessError as e:
        print("⚠️ No se pudo hacer backup de reglas actuales")
        print(e.stderr)
        return False

def main():
    """Función principal"""
    print("🔒 Desplegador de Reglas de Firestore - HuertoRentable")
    print("=" * 60)
    
    # Verificaciones previas
    if not check_firebase_cli():
        sys.exit(1)
    
    if not check_firebase_login():
        sys.exit(1)
    
    if not validate_rules():
        sys.exit(1)
    
    # Hacer backup
    backup_current_rules()
    
    # Dry run
    if not deploy_rules_dry_run():
        print("❌ Dry run falló - no se desplegaron las reglas")
        sys.exit(1)
    
    # Confirmar despliegue
    response = input("\n¿Desplegar las reglas de seguridad? (y/N): ")
    if response.lower() != 'y':
        print("❌ Despliegue cancelado por el usuario")
        sys.exit(0)
    
    # Desplegar
    if deploy_rules():
        print("\n🎉 ¡Reglas de seguridad desplegadas exitosamente!")
        print("🔒 Tu base de datos Firestore ahora está protegida")
        print("\n📋 Reglas implementadas:")
        print("  • Aislamiento total por usuario (user_uid)")
        print("  • Verificación de autenticación Firebase en todas las operaciones")
        print("  • Protección contra acceso cruzado entre usuarios")
        print("  • Solo administradores pueden modificar configuración")
    else:
        print("\n❌ Error en el despliegue")
        print("💡 Puedes restaurar el backup con:")
        print("   firebase firestore:rules set firestore.rules.backup")
        sys.exit(1)

if __name__ == "__main__":
    main()
