"""
Script de Deploy Completo para HuertoRentable
Despliega tanto el hosting como las Cloud Functions
"""
import os
import subprocess
import sys
from pathlib import Path

def ejecutar_comando(comando, descripcion):
    """Ejecutar comando y mostrar resultado"""
    print(f"\n🔄 {descripcion}...")
    try:
        result = subprocess.run(comando, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {descripcion} - Completado")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ Error en {descripcion}:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
        return False

def verificar_firebase_cli():
    """Verificar que Firebase CLI está instalado"""
    result = subprocess.run("firebase --version", shell=True, capture_output=True, text=True)
    return result.returncode == 0

def main():
    """Función principal de deploy"""
    print("🚀 Deploy de HuertoRentable - Firebase Hosting + Cloud Functions")
    print("=" * 60)
    
    # Verificar Firebase CLI
    if not verificar_firebase_cli():
        print("❌ Firebase CLI no está instalado o no se encuentra en PATH")
        print("📦 Instalando Firebase CLI...")
        if not ejecutar_comando("npm install -g firebase-tools", "Instalación de Firebase CLI"):
            print("💡 Instala Firebase CLI manualmente:")
            print("   npm install -g firebase-tools")
            return False
    
    # Paso 1: Build del proyecto
    print("\n📦 PASO 1: Build del proyecto")
    if not ejecutar_comando("python build.py", "Build de archivos estáticos"):
        return False
    
    # Paso 2: Instalar dependencias de Cloud Functions
    print("\n📦 PASO 2: Dependencias de Cloud Functions")
    os.chdir("functions")
    if not ejecutar_comando("npm install", "Instalación de dependencias"):
        return False
    os.chdir("..")
    
    # Paso 3: Deploy de Firestore Rules
    print("\n📦 PASO 3: Deploy de Firestore Rules")
    ejecutar_comando("firebase deploy --only firestore:rules", "Deploy de reglas de Firestore")
    
    # Paso 4: Deploy de Cloud Functions
    print("\n📦 PASO 4: Deploy de Cloud Functions")
    if not ejecutar_comando("firebase deploy --only functions", "Deploy de Cloud Functions"):
        print("⚠️  Error en Cloud Functions, continuando con hosting...")
    
    # Paso 5: Deploy de Hosting
    print("\n📦 PASO 5: Deploy de Firebase Hosting")
    if not ejecutar_comando("firebase deploy --only hosting", "Deploy de Firebase Hosting"):
        return False
    
    print("\n" + "=" * 60)
    print("🎉 DEPLOY COMPLETADO EXITOSAMENTE!")
    print("\n📱 Tu aplicación está disponible en:")
    print("   https://huerto-rentable.web.app")
    print("   https://huerto-rentable.firebaseapp.com")
    
    print("\n🔧 URLs de desarrollo:")
    print("   Cloud Functions: https://us-central1-huerto-rentable.cloudfunctions.net/")
    print("   Firestore: https://console.firebase.google.com/project/huerto-rentable/firestore")
    
    print("\n📊 Para verificar el deploy:")
    print("   firebase hosting:channel:list")
    print("   firebase functions:list")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Deploy completado sin errores")
            sys.exit(0)
        else:
            print("\n❌ Deploy completado con errores")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Deploy cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")
        sys.exit(1)
