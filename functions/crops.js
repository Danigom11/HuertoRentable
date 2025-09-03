/**
 * Módulo de gestión de cultivos para Cloud Functions
 * Migrado desde Flask con la misma lógica de seguridad
 */

const { FieldValue } = require("firebase-admin/firestore");

/**
 * Configurar todas las rutas de cultivos
 */
function setupRoutes(app, db) {
  // ============================================
  // OBTENER TODOS LOS CULTIVOS DEL USUARIO
  // ============================================
  app.get("/list", async (req, res) => {
    try {
      const userUid = req.user.uid;

      const cultivosRef = db.collection("cultivos");
      const snapshot = await cultivosRef
        .where("user_uid", "==", userUid)
        .where("activo", "==", true)
        .orderBy("fecha_siembra", "desc")
        .get();

      const cultivos = [];
      snapshot.forEach((doc) => {
        const data = doc.data();
        cultivos.push({
          id: doc.id,
          ...data,
          fecha_siembra: data.fecha_siembra?.toDate?.() || data.fecha_siembra,
          fecha_cosecha: data.fecha_cosecha?.toDate?.() || data.fecha_cosecha,
        });
      });

      return res.status(200).json({
        success: true,
        data: cultivos,
        count: cultivos.length,
        message: `${cultivos.length} cultivos encontrados`,
      });
    } catch (error) {
      console.error("Error obteniendo cultivos:", error);
      return res.status(500).json({
        error: "Error interno del servidor",
        code: "FETCH_ERROR",
      });
    }
  });

  // ============================================
  // CREAR NUEVO CULTIVO
  // ============================================
  app.post("/create", async (req, res) => {
    try {
      const userUid = req.user.uid;
      const { nombre, precio_por_kilo, descripcion } = req.body;

      // Validación de datos
      if (!nombre || !nombre.trim()) {
        return res.status(400).json({
          error: "El nombre del cultivo es obligatorio",
          code: "MISSING_NAME",
        });
      }

      const precio = parseFloat(precio_por_kilo) || 0;
      if (precio < 0) {
        return res.status(400).json({
          error: "El precio por kilo debe ser positivo",
          code: "INVALID_PRICE",
        });
      }

      // Crear documento del cultivo
      const cultivoData = {
        nombre: nombre.trim().toLowerCase(),
        descripcion: descripcion?.trim() || "",
        precio_por_kilo: precio,
        user_uid: userUid,
        fecha_siembra: FieldValue.serverTimestamp(),
        fecha_cosecha: null,
        activo: true,
        abonos: [],
        produccion_diaria: [],
        created_at: FieldValue.serverTimestamp(),
        updated_at: FieldValue.serverTimestamp(),
      };

      const docRef = await db.collection("cultivos").add(cultivoData);

      return res.status(201).json({
        success: true,
        data: {
          id: docRef.id,
          ...cultivoData,
        },
        message: `Cultivo "${nombre}" creado exitosamente`,
      });
    } catch (error) {
      console.error("Error creando cultivo:", error);
      return res.status(500).json({
        error: "Error interno del servidor",
        code: "CREATE_ERROR",
      });
    }
  });

  // ============================================
  // OBTENER CULTIVO ESPECÍFICO
  // ============================================
  app.get("/:cropId", async (req, res) => {
    try {
      const userUid = req.user.uid;
      const { cropId } = req.params;

      const doc = await db.collection("cultivos").doc(cropId).get();

      if (!doc.exists) {
        return res.status(404).json({
          error: "Cultivo no encontrado",
          code: "NOT_FOUND",
        });
      }

      const data = doc.data();

      // Verificar que el cultivo pertenece al usuario
      if (data.user_uid !== userUid) {
        return res.status(403).json({
          error: "No tienes permisos para acceder a este cultivo",
          code: "FORBIDDEN",
        });
      }

      return res.status(200).json({
        success: true,
        data: {
          id: doc.id,
          ...data,
          fecha_siembra: data.fecha_siembra?.toDate?.() || data.fecha_siembra,
          fecha_cosecha: data.fecha_cosecha?.toDate?.() || data.fecha_cosecha,
        },
        message: "Cultivo obtenido exitosamente",
      });
    } catch (error) {
      console.error("Error obteniendo cultivo:", error);
      return res.status(500).json({
        error: "Error interno del servidor",
        code: "FETCH_ERROR",
      });
    }
  });

  // ============================================
  // ACTUALIZAR CULTIVO
  // ============================================
  app.put("/:cropId", async (req, res) => {
    try {
      const userUid = req.user.uid;
      const { cropId } = req.params;
      const updates = req.body;

      // Verificar que el cultivo existe y pertenece al usuario
      const doc = await db.collection("cultivos").doc(cropId).get();

      if (!doc.exists) {
        return res.status(404).json({
          error: "Cultivo no encontrado",
          code: "NOT_FOUND",
        });
      }

      const data = doc.data();
      if (data.user_uid !== userUid) {
        return res.status(403).json({
          error: "No tienes permisos para modificar este cultivo",
          code: "FORBIDDEN",
        });
      }

      // Preparar datos de actualización
      const updateData = {
        updated_at: FieldValue.serverTimestamp(),
      };

      // Validar y agregar campos permitidos
      if (updates.nombre) {
        updateData.nombre = updates.nombre.trim().toLowerCase();
      }

      if (updates.descripcion !== undefined) {
        updateData.descripcion = updates.descripcion.trim();
      }

      if (updates.precio_por_kilo !== undefined) {
        const precio = parseFloat(updates.precio_por_kilo);
        if (precio < 0) {
          return res.status(400).json({
            error: "El precio por kilo debe ser positivo",
            code: "INVALID_PRICE",
          });
        }
        updateData.precio_por_kilo = precio;
      }

      // NO permitir cambiar user_uid por seguridad
      delete updates.user_uid;

      await db.collection("cultivos").doc(cropId).update(updateData);

      return res.status(200).json({
        success: true,
        message: "Cultivo actualizado exitosamente",
      });
    } catch (error) {
      console.error("Error actualizando cultivo:", error);
      return res.status(500).json({
        error: "Error interno del servidor",
        code: "UPDATE_ERROR",
      });
    }
  });

  // ============================================
  // ELIMINAR CULTIVO (SOFT DELETE)
  // ============================================
  app.delete("/:cropId", async (req, res) => {
    try {
      const userUid = req.user.uid;
      const { cropId } = req.params;

      // Verificar que el cultivo existe y pertenece al usuario
      const doc = await db.collection("cultivos").doc(cropId).get();

      if (!doc.exists) {
        return res.status(404).json({
          error: "Cultivo no encontrado",
          code: "NOT_FOUND",
        });
      }

      const data = doc.data();
      if (data.user_uid !== userUid) {
        return res.status(403).json({
          error: "No tienes permisos para eliminar este cultivo",
          code: "FORBIDDEN",
        });
      }

      // Soft delete - marcar como inactivo
      await db.collection("cultivos").doc(cropId).update({
        activo: false,
        deleted_at: FieldValue.serverTimestamp(),
        updated_at: FieldValue.serverTimestamp(),
      });

      return res.status(200).json({
        success: true,
        message: "Cultivo eliminado exitosamente",
      });
    } catch (error) {
      console.error("Error eliminando cultivo:", error);
      return res.status(500).json({
        error: "Error interno del servidor",
        code: "DELETE_ERROR",
      });
    }
  });

  // ============================================
  // AGREGAR PRODUCCIÓN DIARIA
  // ============================================
  app.post("/:cropId/produccion", async (req, res) => {
    try {
      const userUid = req.user.uid;
      const { cropId } = req.params;
      const { kilos, fecha, notas } = req.body;

      // Validar datos
      const kilosNum = parseFloat(kilos);
      if (!kilosNum || kilosNum <= 0) {
        return res.status(400).json({
          error: "Los kilos deben ser un número positivo",
          code: "INVALID_KILOS",
        });
      }

      // Verificar que el cultivo pertenece al usuario
      const doc = await db.collection("cultivos").doc(cropId).get();

      if (!doc.exists) {
        return res.status(404).json({
          error: "Cultivo no encontrado",
          code: "NOT_FOUND",
        });
      }

      const data = doc.data();
      if (data.user_uid !== userUid) {
        return res.status(403).json({
          error: "No tienes permisos para agregar producción a este cultivo",
          code: "FORBIDDEN",
        });
      }

      // Crear registro de producción
      const produccionEntry = {
        kilos: kilosNum,
        fecha: fecha ? new Date(fecha) : new Date(),
        notas: notas?.trim() || "",
        timestamp: FieldValue.serverTimestamp(),
      };

      // Agregar a la array de producción
      await db
        .collection("cultivos")
        .doc(cropId)
        .update({
          produccion_diaria: FieldValue.arrayUnion(produccionEntry),
          updated_at: FieldValue.serverTimestamp(),
        });

      return res.status(201).json({
        success: true,
        data: produccionEntry,
        message: "Producción registrada exitosamente",
      });
    } catch (error) {
      console.error("Error agregando producción:", error);
      return res.status(500).json({
        error: "Error interno del servidor",
        code: "ADD_PRODUCTION_ERROR",
      });
    }
  });

  // ============================================
  // AGREGAR ABONO
  // ============================================
  app.post("/:cropId/abono", async (req, res) => {
    try {
      const userUid = req.user.uid;
      const { cropId } = req.params;
      const { descripcion, fecha, costo } = req.body;

      // Validar datos
      if (!descripcion || !descripcion.trim()) {
        return res.status(400).json({
          error: "La descripción del abono es obligatoria",
          code: "MISSING_DESCRIPTION",
        });
      }

      // Verificar que el cultivo pertenece al usuario
      const doc = await db.collection("cultivos").doc(cropId).get();

      if (!doc.exists) {
        return res.status(404).json({
          error: "Cultivo no encontrado",
          code: "NOT_FOUND",
        });
      }

      const data = doc.data();
      if (data.user_uid !== userUid) {
        return res.status(403).json({
          error: "No tienes permisos para agregar abonos a este cultivo",
          code: "FORBIDDEN",
        });
      }

      // Crear registro de abono
      const abonoEntry = {
        descripcion: descripcion.trim(),
        fecha: fecha ? new Date(fecha) : new Date(),
        costo: parseFloat(costo) || 0,
        timestamp: FieldValue.serverTimestamp(),
      };

      // Agregar a la array de abonos
      await db
        .collection("cultivos")
        .doc(cropId)
        .update({
          abonos: FieldValue.arrayUnion(abonoEntry),
          updated_at: FieldValue.serverTimestamp(),
        });

      return res.status(201).json({
        success: true,
        data: abonoEntry,
        message: "Abono registrado exitosamente",
      });
    } catch (error) {
      console.error("Error agregando abono:", error);
      return res.status(500).json({
        error: "Error interno del servidor",
        code: "ADD_FERTILIZER_ERROR",
      });
    }
  });
}

module.exports = {
  setupRoutes,
};
