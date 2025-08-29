"""
Servicio de almacenamiento local para usuarios invitados
Manejo de datos en localStorage del navegador
"""
import json
from typing import List, Dict, Optional

class LocalStorageService:
    """Servicio para simular operaciones de base de datos en localStorage"""
    
    @staticmethod
    def get_user_crops(user_uid: str) -> List[Dict]:
        """
        Obtener cultivos del usuario desde localStorage (simulado para invitados)
        
        Args:
            user_uid (str): UID del usuario invitado
            
        Returns:
            List[Dict]: Lista de cultivos del localStorage
        """
        # Esta función se ejecutará en JavaScript en el frontend
        # Aquí solo proporcionamos la estructura
        return []
    
    @staticmethod
    def create_crop(user_uid: str, crop_data: Dict) -> bool:
        """
        Crear cultivo en localStorage
        
        Args:
            user_uid (str): UID del usuario
            crop_data (Dict): Datos del cultivo
            
        Returns:
            bool: True si se creó exitosamente
        """
        # Esta función se maneja en el frontend con JavaScript
        return True
    
    @staticmethod
    def check_guest_limits(user_uid: str) -> bool:
        """
        Verificar límites para usuarios invitados (máximo 3 cultivos)
        
        Args:
            user_uid (str): UID del usuario invitado
            
        Returns:
            bool: True si puede crear más cultivos
        """
        # Esta verificación se hace en JavaScript
        return True
    
    @staticmethod
    def get_javascript_functions() -> str:
        """
        Retornar funciones JavaScript para manejo de localStorage
        
        Returns:
            str: Código JavaScript para manejar localStorage
        """
        return """
// Servicio de almacenamiento local para usuarios invitados
class LocalCropService {
    constructor() {
        this.storageKey = 'huerto_cultivos_local';
        this.maxCrops = 3;
    }
    
    // Obtener todos los cultivos del localStorage
    getUserCrops() {
        try {
            const data = localStorage.getItem(this.storageKey);
            return data ? JSON.parse(data) : [];
        } catch (error) {
            console.error('Error obteniendo cultivos locales:', error);
            return [];
        }
    }
    
    // Crear nuevo cultivo
    createCrop(cropData) {
        try {
            const crops = this.getUserCrops();
            
            // Verificar límites
            if (crops.length >= this.maxCrops) {
                throw new Error(`Máximo ${this.maxCrops} cultivos en modo invitado`);
            }
            
            // Crear cultivo con ID único
            const newCrop = {
                id: 'crop_' + Date.now(),
                nombre: cropData.nombre,
                fecha_siembra: new Date().toISOString(),
                fecha_cosecha: null,
                precio_por_kilo: parseFloat(cropData.precio || 0),
                abonos: [],
                produccion_diaria: [],
                activo: true,
                creado_en: new Date().toISOString()
            };
            
            crops.push(newCrop);
            localStorage.setItem(this.storageKey, JSON.stringify(crops));
            
            console.log('✅ Cultivo creado localmente:', newCrop.nombre);
            return true;
            
        } catch (error) {
            console.error('❌ Error creando cultivo local:', error);
            throw error;
        }
    }
    
    // Actualizar cultivo
    updateCrop(cropId, updateData) {
        try {
            const crops = this.getUserCrops();
            const cropIndex = crops.findIndex(c => c.id === cropId);
            
            if (cropIndex === -1) {
                throw new Error('Cultivo no encontrado');
            }
            
            crops[cropIndex] = { ...crops[cropIndex], ...updateData };
            localStorage.setItem(this.storageKey, JSON.stringify(crops));
            
            return true;
        } catch (error) {
            console.error('Error actualizando cultivo:', error);
            throw error;
        }
    }
    
    // Eliminar cultivo
    deleteCrop(cropId) {
        try {
            const crops = this.getUserCrops();
            const filteredCrops = crops.filter(c => c.id !== cropId);
            
            localStorage.setItem(this.storageKey, JSON.stringify(filteredCrops));
            return true;
        } catch (error) {
            console.error('Error eliminando cultivo:', error);
            throw error;
        }
    }
    
    // Obtener resumen de datos
    getCropsSummary() {
        const crops = this.getUserCrops();
        
        let totalKilos = 0;
        let totalBeneficios = 0;
        
        crops.forEach(crop => {
            const kilosCrop = crop.produccion_diaria.reduce((sum, p) => sum + (p.kilos || 0), 0);
            const beneficioCrop = kilosCrop * (crop.precio_por_kilo || 0);
            
            totalKilos += kilosCrop;
            totalBeneficios += beneficioCrop;
        });
        
        return {
            total_cultivos: crops.length,
            total_kilos: totalKilos,
            total_beneficios: totalBeneficios,
            limite_cultivos: this.maxCrops,
            cultivos_restantes: this.maxCrops - crops.length
        };
    }
    
    // Limpiar todos los datos (para testing)
    clearAllData() {
        localStorage.removeItem(this.storageKey);
        console.log('🗑️ Datos locales limpiados');
    }
    
    // Exportar datos para migración
    exportData() {
        return {
            cultivos: this.getUserCrops(),
            resumen: this.getCropsSummary(),
            exportado_en: new Date().toISOString()
        };
    }
}

// Inicializar servicio local
window.localCropService = new LocalCropService();
"""
