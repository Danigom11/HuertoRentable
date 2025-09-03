/**
 * Módulo de autenticación para Cloud Functions
 * Gestión de usuarios y perfiles
 */

/**
 * Configurar todas las rutas de autenticación
 */
function setupRoutes(app, db, admin) {
  // ============================================
  // CREAR O ACTUALIZAR PERFIL DE USUARIO
  // ============================================
  app.post("/profile", async (req, res) => {
    try {
      // Esta ruta necesita autenticación, pero se maneja en index.js
      // Aquí el usuario ya está verificado y disponible en req.user

      const userUid = req.user.uid;
      const { nombre, apellidos, telefono, ubicacion, plan_seleccionado } =
        req.body;

      // Validar datos mínimos
      if (!nombre || !nombre.trim()) {
        return res.status(400).json({
          error: "El nombre es obligatorio",
          code: "MISSING_NAME",
        });
      }

      // Datos del perfil
      const perfilData = {
        uid: userUid,
        email: req.user.email,
        nombre: nombre.trim(),
        apellidos: apellidos?.trim() || "",
        telefono: telefono?.trim() || "",
        ubicacion: ubicacion?.trim() || "",
        plan_seleccionado: plan_seleccionado || "gratuito",
        email_verified: req.user.emailVerified,
        created_at: admin.firestore.FieldValue.serverTimestamp(),
        updated_at: admin.firestore.FieldValue.serverTimestamp(),
        ultimo_acceso: admin.firestore.FieldValue.serverTimestamp(),
      };

      // Crear o actualizar documento del usuario
      await db
        .collection("usuarios")
        .doc(userUid)
        .set(perfilData, { merge: true });

      return res.status(200).json({
        success: true,
        data: perfilData,
        message: "Perfil actualizado exitosamente",
      });
    } catch (error) {
      console.error("Error actualizando perfil:", error);
      return res.status(500).json({
        error: "Error interno del servidor",
        code: "PROFILE_UPDATE_ERROR",
      });
    }
  });

  // ============================================
  // OBTENER PERFIL DE USUARIO
  // ============================================
  app.get("/profile", async (req, res) => {
    try {
      const userUid = req.user.uid;

      const doc = await db.collection("usuarios").doc(userUid).get();

      if (!doc.exists) {
        // Usuario no tiene perfil aún, devolver datos básicos
        return res.status(200).json({
          success: true,
          data: {
            uid: userUid,
            email: req.user.email,
            email_verified: req.user.emailVerified,
            nombre: "",
            apellidos: "",
            telefono: "",
            ubicacion: "",
            plan_seleccionado: "gratuito",
            perfil_completo: false,
          },
          message: "Perfil básico obtenido",
        });
      }

      const perfil = doc.data();

      // Actualizar último acceso
      await db.collection("usuarios").doc(userUid).update({
        ultimo_acceso: admin.firestore.FieldValue.serverTimestamp(),
      });

      return res.status(200).json({
        success: true,
        data: {
          ...perfil,
          perfil_completo: !!(perfil.nombre && perfil.apellidos),
        },
        message: "Perfil obtenido exitosamente",
      });
    } catch (error) {
      console.error("Error obteniendo perfil:", error);
      return res.status(500).json({
        error: "Error interno del servidor",
        code: "PROFILE_FETCH_ERROR",
      });
    }
  });

  // ============================================
  // OBTENER PLANES DISPONIBLES
  // ============================================
  app.get("/planes", async (req, res) => {
    try {
      const planesSnapshot = await db.collection("planes").get();

      const planes = [];
      planesSnapshot.forEach((doc) => {
        planes.push({
          id: doc.id,
          ...doc.data(),
        });
      });

      // Si no hay planes en la base de datos, devolver planes por defecto
      if (planes.length === 0) {
        const planesDefault = [
          {
            id: "gratuito",
            nombre: "Plan Gratuito",
            descripcion: "Perfecto para empezar",
            precio: 0,
            caracteristicas: [
              "Hasta 5 cultivos",
              "Estadísticas básicas",
              "Soporte por email",
            ],
            limite_cultivos: 5,
            activo: true,
          },
          {
            id: "premium",
            nombre: "Plan Premium",
            descripcion: "Para huertos profesionales",
            precio: 9.99,
            caracteristicas: [
              "Cultivos ilimitados",
              "Analytics avanzados",
              "Reportes PDF",
              "Soporte prioritario",
            ],
            limite_cultivos: -1, // Ilimitado
            activo: true,
          },
        ];

        return res.status(200).json({
          success: true,
          data: planesDefault,
          message: "Planes por defecto obtenidos",
        });
      }

      return res.status(200).json({
        success: true,
        data: planes,
        message: "Planes obtenidos exitosamente",
      });
    } catch (error) {
      console.error("Error obteniendo planes:", error);
      return res.status(500).json({
        error: "Error interno del servidor",
        code: "PLANS_FETCH_ERROR",
      });
    }
  });

  // ============================================
  // VERIFICAR LÍMITES DEL PLAN
  // ============================================
  app.get("/limits", async (req, res) => {
    try {
      const userUid = req.user.uid;

      // Obtener perfil del usuario
      const perfilDoc = await db.collection("usuarios").doc(userUid).get();
      const perfil = perfilDoc.exists
        ? perfilDoc.data()
        : { plan_seleccionado: "gratuito" };

      // Contar cultivos activos
      const cultivosSnapshot = await db
        .collection("cultivos")
        .where("user_uid", "==", userUid)
        .where("activo", "==", true)
        .get();

      const cultivosActivos = cultivosSnapshot.size;

      // Obtener límites del plan
      const planDoc = await db
        .collection("planes")
        .doc(perfil.plan_seleccionado)
        .get();
      let limiteCultivos = 5; // Límite por defecto para plan gratuito

      if (planDoc.exists) {
        const planData = planDoc.data();
        limiteCultivos =
          planData.limite_cultivos === -1 ? 999999 : planData.limite_cultivos;
      }

      const limites = {
        plan_actual: perfil.plan_seleccionado,
        cultivos_activos: cultivosActivos,
        limite_cultivos: limiteCultivos,
        puede_crear_cultivo: cultivosActivos < limiteCultivos,
        cultivos_restantes: Math.max(0, limiteCultivos - cultivosActivos),
      };

      return res.status(200).json({
        success: true,
        data: limites,
        message: "Límites del plan obtenidos",
      });
    } catch (error) {
      console.error("Error obteniendo límites:", error);
      return res.status(500).json({
        error: "Error interno del servidor",
        code: "LIMITS_FETCH_ERROR",
      });
    }
  });

  // ============================================
  // ACTUALIZAR PLAN DEL USUARIO
  // ============================================
  app.post("/upgrade-plan", async (req, res) => {
    try {
      const userUid = req.user.uid;
      const { nuevo_plan, payment_method_id } = req.body;

      // Validar que el plan existe
      const planDoc = await db.collection("planes").doc(nuevo_plan).get();

      if (!planDoc.exists) {
        return res.status(400).json({
          error: "Plan no válido",
          code: "INVALID_PLAN",
        });
      }

      const planData = planDoc.data();

      // Para planes de pago, aquí integrarías con Stripe/PayPal
      // Por ahora solo actualizamos el plan

      await db.collection("usuarios").doc(userUid).update({
        plan_seleccionado: nuevo_plan,
        fecha_upgrade: admin.firestore.FieldValue.serverTimestamp(),
        updated_at: admin.firestore.FieldValue.serverTimestamp(),
      });

      return res.status(200).json({
        success: true,
        data: {
          nuevo_plan: nuevo_plan,
          nombre_plan: planData.nombre,
          precio: planData.precio,
        },
        message: "Plan actualizado exitosamente",
      });
    } catch (error) {
      console.error("Error actualizando plan:", error);
      return res.status(500).json({
        error: "Error interno del servidor",
        code: "PLAN_UPDATE_ERROR",
      });
    }
  });

  // ============================================
  // ELIMINAR CUENTA DE USUARIO
  // ============================================
  app.delete("/account", async (req, res) => {
    try {
      const userUid = req.user.uid;
      const { confirmacion } = req.body;

      if (confirmacion !== "ELIMINAR_CUENTA") {
        return res.status(400).json({
          error: "Confirmación requerida para eliminar la cuenta",
          code: "CONFIRMATION_REQUIRED",
        });
      }

      // Marcar todos los cultivos como eliminados
      const batch = db.batch();

      const cultivosSnapshot = await db
        .collection("cultivos")
        .where("user_uid", "==", userUid)
        .get();

      cultivosSnapshot.forEach((doc) => {
        batch.update(doc.ref, {
          activo: false,
          deleted_at: admin.firestore.FieldValue.serverTimestamp(),
          deleted_by_user: true,
        });
      });

      // Marcar perfil como eliminado (soft delete)
      const userRef = db.collection("usuarios").doc(userUid);
      batch.update(userRef, {
        cuenta_eliminada: true,
        fecha_eliminacion: admin.firestore.FieldValue.serverTimestamp(),
        activo: false,
      });

      await batch.commit();

      // En producción, también eliminarías el usuario de Firebase Auth
      // await admin.auth().deleteUser(userUid);

      return res.status(200).json({
        success: true,
        message: "Cuenta eliminada exitosamente",
      });
    } catch (error) {
      console.error("Error eliminando cuenta:", error);
      return res.status(500).json({
        error: "Error interno del servidor",
        code: "ACCOUNT_DELETE_ERROR",
      });
    }
  });

  // ============================================
  // RUTA DE REGISTRO INICIAL (sin autenticación)
  // ============================================
  app.post("/register", async (req, res) => {
    try {
      // Esta ruta NO requiere autenticación previa
      // Se llama después de crear el usuario en Firebase Auth desde la app

      const { uid, email, nombre, plan_inicial } = req.body;

      if (!uid || !email) {
        return res.status(400).json({
          error: "UID y email son obligatorios",
          code: "MISSING_REQUIRED_FIELDS",
        });
      }

      // Verificar que el usuario existe en Firebase Auth
      try {
        await admin.auth().getUser(uid);
      } catch (authError) {
        return res.status(400).json({
          error: "Usuario no válido en Firebase Auth",
          code: "INVALID_USER",
        });
      }

      // Crear perfil inicial
      const perfilData = {
        uid: uid,
        email: email,
        nombre: nombre?.trim() || "",
        apellidos: "",
        telefono: "",
        ubicacion: "",
        plan_seleccionado: plan_inicial || "gratuito",
        email_verified: false,
        created_at: admin.firestore.FieldValue.serverTimestamp(),
        updated_at: admin.firestore.FieldValue.serverTimestamp(),
        ultimo_acceso: admin.firestore.FieldValue.serverTimestamp(),
        activo: true,
        perfil_completo: false,
      };

      await db.collection("usuarios").doc(uid).set(perfilData);

      return res.status(201).json({
        success: true,
        data: perfilData,
        message: "Usuario registrado exitosamente",
      });
    } catch (error) {
      console.error("Error en registro:", error);
      return res.status(500).json({
        error: "Error interno del servidor",
        code: "REGISTER_ERROR",
      });
    }
  });
}

module.exports = {
  setupRoutes,
};
