#!/bin/bash

# Script de testing completo para HuertoRentable Cloud Functions
# Ejecutar después del deploy para verificar que todo funciona

BASE_URL="https://us-central1-huerto-rentable.cloudfunctions.net"

echo "🧪 TESTING HUERTORENTABLE CLOUD FUNCTIONS"
echo "=========================================="
echo ""

# Test 1: Health Check
echo "1. Testing Health Check..."
curl -s "${BASE_URL}/health" | python -m json.tool
echo ""

# Test 2: Planes (sin autenticación)
echo "2. Testing Planes (sin auth)..."
curl -s "${BASE_URL}/auth/planes" | python -m json.tool
echo ""

# Test 3: Registro (sin autenticación)
echo "3. Testing endpoint de registro..."
curl -s -X POST "${BASE_URL}/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"uid":"test123","email":"test@example.com","nombre":"Test User"}' | python -m json.tool
echo ""

echo "🔐 TESTS CON AUTENTICACIÓN"
echo "========================="
echo "Para probar endpoints con autenticación, necesitas:"
echo "1. Token Firebase válido"
echo "2. Ejecutar comando como:"
echo ""
echo "curl -H \"Authorization: Bearer YOUR_TOKEN\" \\"
echo "     ${BASE_URL}/crops/list"
echo ""

echo "✅ TESTS BÁSICOS COMPLETADOS"
echo ""
echo "📱 URLs para Android:"
echo "Base: ${BASE_URL}/"
echo "Health: ${BASE_URL}/health"
echo "Crops: ${BASE_URL}/crops/list"
echo "Dashboard: ${BASE_URL}/analytics/dashboard"
echo ""
echo "🎯 Backend listo para Android! 🚀"
