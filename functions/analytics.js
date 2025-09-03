/**
 * Módulo de analytics para Cloud Functions
 * Estadísticas y reportes para la app Android
 */

/**
 * Configurar todas las rutas de analytics
 */
function setupRoutes(app, db) {
  // ============================================
  // DASHBOARD PRINCIPAL - RESUMEN GENERAL
  // ============================================
  app.get("/dashboard", async (req, res) => {
    try {
      const userUid = req.user.uid;

      // Obtener todos los cultivos activos del usuario
      const cultivosSnapshot = await db
        .collection("cultivos")
        .where("user_uid", "==", userUid)
        .where("activo", "==", true)
        .get();

      let totalKilos = 0;
      let totalBeneficios = 0;
      let cultivosActivos = 0;
      let cultivosPorTipo = {};
      let produccionMensual = {};

      cultivosSnapshot.forEach((doc) => {
        const cultivo = doc.data();
        cultivosActivos++;

        // Contar cultivos por tipo
        const nombre = cultivo.nombre || "sin_nombre";
        cultivosPorTipo[nombre] = (cultivosPorTipo[nombre] || 0) + 1;

        // Calcular producción total y beneficios
        if (
          cultivo.produccion_diaria &&
          Array.isArray(cultivo.produccion_diaria)
        ) {
          cultivo.produccion_diaria.forEach((prod) => {
            const kilos = parseFloat(prod.kilos) || 0;
            totalKilos += kilos;
            totalBeneficios += kilos * (cultivo.precio_por_kilo || 0);

            // Agrupar por mes
            const fecha = prod.fecha?.toDate
              ? prod.fecha.toDate()
              : new Date(prod.fecha);
            const mesKey = `${fecha.getFullYear()}-${String(
              fecha.getMonth() + 1
            ).padStart(2, "0")}`;
            produccionMensual[mesKey] =
              (produccionMensual[mesKey] || 0) + kilos;
          });
        }
      });

      const resumen = {
        cultivos_activos: cultivosActivos,
        total_kilos_recogidos: Math.round(totalKilos * 100) / 100,
        beneficios_totales: Math.round(totalBeneficios * 100) / 100,
        cultivos_por_tipo: cultivosPorTipo,
        produccion_mensual: produccionMensual,
        promedio_kilos_por_cultivo:
          cultivosActivos > 0
            ? Math.round((totalKilos / cultivosActivos) * 100) / 100
            : 0,
      };

      return res.status(200).json({
        success: true,
        data: resumen,
        message: "Dashboard obtenido exitosamente",
      });
    } catch (error) {
      console.error("Error obteniendo dashboard:", error);
      return res.status(500).json({
        error: "Error interno del servidor",
        code: "DASHBOARD_ERROR",
      });
    }
  });

  // ============================================
  // PRODUCCIÓN POR CULTIVO
  // ============================================
  app.get("/produccion/:cropId", async (req, res) => {
    try {
      const userUid = req.user.uid;
      const { cropId } = req.params;
      const { periodo } = req.query; // 'mes', 'trimestre', 'año'

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
          error: "No tienes permisos para acceder a este cultivo",
          code: "FORBIDDEN",
        });
      }

      // Procesar datos de producción
      const produccionData = [];
      let totalKilos = 0;
      let totalBeneficios = 0;

      if (data.produccion_diaria && Array.isArray(data.produccion_diaria)) {
        data.produccion_diaria.forEach((prod) => {
          const kilos = parseFloat(prod.kilos) || 0;
          const fecha = prod.fecha?.toDate
            ? prod.fecha.toDate()
            : new Date(prod.fecha);
          const beneficio = kilos * (data.precio_por_kilo || 0);

          totalKilos += kilos;
          totalBeneficios += beneficio;

          produccionData.push({
            fecha: fecha.toISOString().split("T")[0],
            kilos: kilos,
            beneficio: Math.round(beneficio * 100) / 100,
            notas: prod.notas || "",
          });
        });
      }

      // Ordenar por fecha
      produccionData.sort((a, b) => new Date(a.fecha) - new Date(b.fecha));

      const analytics = {
        cultivo_id: cropId,
        cultivo_nombre: data.nombre,
        precio_por_kilo: data.precio_por_kilo || 0,
        total_kilos: Math.round(totalKilos * 100) / 100,
        total_beneficios: Math.round(totalBeneficios * 100) / 100,
        numero_cosechas: produccionData.length,
        promedio_kilos_por_cosecha:
          produccionData.length > 0
            ? Math.round((totalKilos / produccionData.length) * 100) / 100
            : 0,
        produccion_detallada: produccionData,
      };

      return res.status(200).json({
        success: true,
        data: analytics,
        message: "Analytics de producción obtenidos exitosamente",
      });
    } catch (error) {
      console.error("Error obteniendo analytics de producción:", error);
      return res.status(500).json({
        error: "Error interno del servidor",
        code: "PRODUCTION_ANALYTICS_ERROR",
      });
    }
  });

  // ============================================
  // COMPARATIVA ANUAL
  // ============================================
  app.get("/comparativa", async (req, res) => {
    try {
      const userUid = req.user.uid;
      const { año } = req.query;

      // Obtener todos los cultivos del usuario
      const cultivosSnapshot = await db
        .collection("cultivos")
        .where("user_uid", "==", userUid)
        .get();

      const añoActual = año ? parseInt(año) : new Date().getFullYear();
      const añoAnterior = añoActual - 1;

      let datosComparativa = {
        año_actual: {
          año: añoActual,
          total_kilos: 0,
          total_beneficios: 0,
          cultivos_por_mes: {},
          mejores_cultivos: {},
        },
        año_anterior: {
          año: añoAnterior,
          total_kilos: 0,
          total_beneficios: 0,
          cultivos_por_mes: {},
          mejores_cultivos: {},
        },
      };

      cultivosSnapshot.forEach((doc) => {
        const cultivo = doc.data();
        const nombreCultivo = cultivo.nombre || "sin_nombre";

        if (
          cultivo.produccion_diaria &&
          Array.isArray(cultivo.produccion_diaria)
        ) {
          cultivo.produccion_diaria.forEach((prod) => {
            const fecha = prod.fecha?.toDate
              ? prod.fecha.toDate()
              : new Date(prod.fecha);
            const año = fecha.getFullYear();
            const mes = fecha.getMonth() + 1;
            const kilos = parseFloat(prod.kilos) || 0;
            const beneficio = kilos * (cultivo.precio_por_kilo || 0);

            if (año === añoActual) {
              datosComparativa.año_actual.total_kilos += kilos;
              datosComparativa.año_actual.total_beneficios += beneficio;

              const mesKey = `mes_${mes}`;
              if (!datosComparativa.año_actual.cultivos_por_mes[mesKey]) {
                datosComparativa.año_actual.cultivos_por_mes[mesKey] = 0;
              }
              datosComparativa.año_actual.cultivos_por_mes[mesKey] += kilos;

              if (
                !datosComparativa.año_actual.mejores_cultivos[nombreCultivo]
              ) {
                datosComparativa.año_actual.mejores_cultivos[nombreCultivo] = 0;
              }
              datosComparativa.año_actual.mejores_cultivos[nombreCultivo] +=
                kilos;
            } else if (año === añoAnterior) {
              datosComparativa.año_anterior.total_kilos += kilos;
              datosComparativa.año_anterior.total_beneficios += beneficio;

              const mesKey = `mes_${mes}`;
              if (!datosComparativa.año_anterior.cultivos_por_mes[mesKey]) {
                datosComparativa.año_anterior.cultivos_por_mes[mesKey] = 0;
              }
              datosComparativa.año_anterior.cultivos_por_mes[mesKey] += kilos;

              if (
                !datosComparativa.año_anterior.mejores_cultivos[nombreCultivo]
              ) {
                datosComparativa.año_anterior.mejores_cultivos[
                  nombreCultivo
                ] = 0;
              }
              datosComparativa.año_anterior.mejores_cultivos[nombreCultivo] +=
                kilos;
            }
          });
        }
      });

      // Redondear números
      datosComparativa.año_actual.total_kilos =
        Math.round(datosComparativa.año_actual.total_kilos * 100) / 100;
      datosComparativa.año_actual.total_beneficios =
        Math.round(datosComparativa.año_actual.total_beneficios * 100) / 100;
      datosComparativa.año_anterior.total_kilos =
        Math.round(datosComparativa.año_anterior.total_kilos * 100) / 100;
      datosComparativa.año_anterior.total_beneficios =
        Math.round(datosComparativa.año_anterior.total_beneficios * 100) / 100;

      // Calcular porcentajes de crecimiento
      const crecimientoKilos =
        datosComparativa.año_anterior.total_kilos > 0
          ? Math.round(
              ((datosComparativa.año_actual.total_kilos -
                datosComparativa.año_anterior.total_kilos) /
                datosComparativa.año_anterior.total_kilos) *
                100
            )
          : 0;

      const crecimientoBeneficios =
        datosComparativa.año_anterior.total_beneficios > 0
          ? Math.round(
              ((datosComparativa.año_actual.total_beneficios -
                datosComparativa.año_anterior.total_beneficios) /
                datosComparativa.año_anterior.total_beneficios) *
                100
            )
          : 0;

      datosComparativa.crecimiento = {
        kilos_porcentaje: crecimientoKilos,
        beneficios_porcentaje: crecimientoBeneficios,
      };

      return res.status(200).json({
        success: true,
        data: datosComparativa,
        message: "Comparativa anual obtenida exitosamente",
      });
    } catch (error) {
      console.error("Error obteniendo comparativa:", error);
      return res.status(500).json({
        error: "Error interno del servidor",
        code: "COMPARATIVE_ERROR",
      });
    }
  });

  // ============================================
  // EXPORTAR DATOS (para reportes PDF)
  // ============================================
  app.get("/export", async (req, res) => {
    try {
      const userUid = req.user.uid;
      const { formato, periodo } = req.query; // formato: 'json', 'csv'

      // Obtener todos los cultivos del usuario con producción
      const cultivosSnapshot = await db
        .collection("cultivos")
        .where("user_uid", "==", userUid)
        .get();

      const datosExport = [];

      cultivosSnapshot.forEach((doc) => {
        const cultivo = doc.data();

        if (
          cultivo.produccion_diaria &&
          Array.isArray(cultivo.produccion_diaria)
        ) {
          cultivo.produccion_diaria.forEach((prod) => {
            const fecha = prod.fecha?.toDate
              ? prod.fecha.toDate()
              : new Date(prod.fecha);
            const kilos = parseFloat(prod.kilos) || 0;
            const beneficio = kilos * (cultivo.precio_por_kilo || 0);

            datosExport.push({
              cultivo_id: doc.id,
              cultivo_nombre: cultivo.nombre,
              fecha: fecha.toISOString().split("T")[0],
              kilos: kilos,
              precio_por_kilo: cultivo.precio_por_kilo || 0,
              beneficio: Math.round(beneficio * 100) / 100,
              notas: prod.notas || "",
              fecha_siembra:
                cultivo.fecha_siembra
                  ?.toDate?.()
                  ?.toISOString()
                  ?.split("T")[0] || "",
            });
          });
        }
      });

      // Ordenar por fecha
      datosExport.sort((a, b) => new Date(a.fecha) - new Date(b.fecha));

      if (formato === "csv") {
        // Convertir a CSV
        const headers = Object.keys(datosExport[0] || {});
        const csvContent = [
          headers.join(","),
          ...datosExport.map((row) =>
            headers.map((header) => `"${row[header] || ""}"`).join(",")
          ),
        ].join("\n");

        res.setHeader("Content-Type", "text/csv");
        res.setHeader(
          "Content-Disposition",
          'attachment; filename="huertorentable_export.csv"'
        );
        return res.status(200).send(csvContent);
      }

      return res.status(200).json({
        success: true,
        data: datosExport,
        count: datosExport.length,
        message: "Datos exportados exitosamente",
      });
    } catch (error) {
      console.error("Error exportando datos:", error);
      return res.status(500).json({
        error: "Error interno del servidor",
        code: "EXPORT_ERROR",
      });
    }
  });
}

module.exports = {
  setupRoutes,
};
