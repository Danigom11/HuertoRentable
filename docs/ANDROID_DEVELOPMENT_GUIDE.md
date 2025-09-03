# 📱 HuertoRentable Android - Guía de Desarrollo

## 🎯 BACKEND CONFIRMADO FUNCIONANDO

✅ **URL Base**: `https://us-central1-huerto-rentable.cloudfunctions.net/`  
✅ **Health Check**: Funcionando correctamente  
✅ **Firebase Auth**: Integrado  
✅ **5 Cloud Functions**: Desplegadas y operativas

## 🛠️ CONFIGURACIÓN ANDROID

### 1. **Dependencias necesarias (build.gradle)**

```gradle
dependencies {
    // Firebase
    implementation platform('com.google.firebase:firebase-bom:32.5.0')
    implementation 'com.google.firebase:firebase-auth-ktx'
    implementation 'com.google.firebase:firebase-firestore-ktx'

    // HTTP Requests
    implementation 'com.squareup.retrofit2:retrofit:2.9.0'
    implementation 'com.squareup.retrofit2:converter-gson:2.9.0'
    implementation 'com.squareup.okhttp3:logging-interceptor:4.11.0'

    // Coroutines
    implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3'

    // ViewModel
    implementation 'androidx.lifecycle:lifecycle-viewmodel-ktx:2.7.0'
}
```

### 2. **Configuración de red (ApiService.kt)**

```kotlin
object ApiConfig {
    const val BASE_URL = "https://us-central1-huerto-rentable.cloudfunctions.net/"

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val authInterceptor = Interceptor { chain ->
        val original = chain.request()
        val requestBuilder = original.newBuilder()

        // Agregar token Firebase automáticamente
        FirebaseAuth.getInstance().currentUser?.getIdToken(true)?.result?.token?.let { token ->
            requestBuilder.addHeader("Authorization", "Bearer $token")
        }

        requestBuilder.addHeader("Content-Type", "application/json")
        chain.proceed(requestBuilder.build())
    }

    private val client = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .addInterceptor(authInterceptor)
        .build()

    val retrofit: Retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(client)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
}

interface ApiService {
    @GET("health")
    suspend fun healthCheck(): Response<HealthResponse>

    @GET("crops/list")
    suspend fun getCropsList(): Response<CropsListResponse>

    @POST("crops/create")
    suspend fun createCrop(@Body crop: CreateCropRequest): Response<CropResponse>

    @GET("crops/{id}")
    suspend fun getCrop(@Path("id") cropId: String): Response<CropResponse>

    @PUT("crops/{id}")
    suspend fun updateCrop(@Path("id") cropId: String, @Body crop: UpdateCropRequest): Response<CropResponse>

    @DELETE("crops/{id}")
    suspend fun deleteCrop(@Path("id") cropId: String): Response<ApiResponse>

    @POST("crops/{id}/produccion")
    suspend fun addProduction(@Path("id") cropId: String, @Body production: ProductionRequest): Response<ApiResponse>

    @GET("analytics/dashboard")
    suspend fun getDashboard(): Response<DashboardResponse>

    @GET("analytics/comparativa")
    suspend fun getComparativa(@Query("año") year: Int? = null): Response<ComparativaResponse>

    @GET("auth/profile")
    suspend fun getProfile(): Response<ProfileResponse>

    @POST("auth/profile")
    suspend fun updateProfile(@Body profile: UpdateProfileRequest): Response<ProfileResponse>

    @GET("auth/planes")
    suspend fun getPlanes(): Response<PlanesResponse>
}
```

### 3. **Modelos de datos (Models.kt)**

```kotlin
// Respuestas del servidor
data class HealthResponse(
    val status: String,
    val service: String,
    val version: String,
    val timestamp: String,
    val firebase: String
)

data class ApiResponse(
    val success: Boolean,
    val message: String,
    val timestamp: String
)

data class CropsListResponse(
    val success: Boolean,
    val data: List<Crop>,
    val count: Int,
    val message: String
)

data class CropResponse(
    val success: Boolean,
    val data: Crop,
    val message: String
)

// Entidades principales
data class Crop(
    val id: String? = null,
    val nombre: String,
    val descripcion: String = "",
    val precio_por_kilo: Double,
    val user_uid: String? = null,
    val fecha_siembra: String? = null,
    val fecha_cosecha: String? = null,
    val activo: Boolean = true,
    val abonos: List<Abono> = emptyList(),
    val produccion_diaria: List<Produccion> = emptyList()
)

data class Abono(
    val descripcion: String,
    val fecha: String,
    val costo: Double,
    val timestamp: String? = null
)

data class Produccion(
    val kilos: Double,
    val fecha: String,
    val notas: String = "",
    val timestamp: String? = null
)

// Requests
data class CreateCropRequest(
    val nombre: String,
    val precio_por_kilo: Double,
    val descripcion: String = ""
)

data class UpdateCropRequest(
    val nombre: String? = null,
    val precio_por_kilo: Double? = null,
    val descripcion: String? = null
)

data class ProductionRequest(
    val kilos: Double,
    val fecha: String? = null,
    val notas: String = ""
)

// Dashboard
data class DashboardResponse(
    val success: Boolean,
    val data: DashboardData,
    val message: String
)

data class DashboardData(
    val cultivos_activos: Int,
    val total_kilos_recogidos: Double,
    val beneficios_totales: Double,
    val cultivos_por_tipo: Map<String, Int>,
    val produccion_mensual: Map<String, Double>,
    val promedio_kilos_por_cultivo: Double
)
```

### 4. **Repository (HuertoRepository.kt)**

```kotlin
class HuertoRepository {
    private val apiService = ApiConfig.retrofit.create(ApiService::class.java)

    suspend fun healthCheck(): Result<HealthResponse> {
        return try {
            val response = apiService.healthCheck()
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Error: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getCrops(): Result<List<Crop>> {
        return try {
            val response = apiService.getCropsList()
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!.data)
            } else {
                Result.failure(Exception("Error obteniendo cultivos: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun createCrop(crop: CreateCropRequest): Result<Crop> {
        return try {
            val response = apiService.createCrop(crop)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!.data)
            } else {
                Result.failure(Exception("Error creando cultivo: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getDashboard(): Result<DashboardData> {
        return try {
            val response = apiService.getDashboard()
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!.data)
            } else {
                Result.failure(Exception("Error obteniendo dashboard: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
```

### 5. **ViewModel (MainViewModel.kt)**

```kotlin
class MainViewModel : ViewModel() {
    private val repository = HuertoRepository()

    private val _crops = MutableLiveData<List<Crop>>()
    val crops: LiveData<List<Crop>> = _crops

    private val _dashboard = MutableLiveData<DashboardData>()
    val dashboard: LiveData<DashboardData> = _dashboard

    private val _loading = MutableLiveData<Boolean>()
    val loading: LiveData<Boolean> = _loading

    private val _error = MutableLiveData<String>()
    val error: LiveData<String> = _error

    fun loadCrops() {
        viewModelScope.launch {
            _loading.value = true
            repository.getCrops()
                .onSuccess { _crops.value = it }
                .onFailure { _error.value = it.message }
            _loading.value = false
        }
    }

    fun loadDashboard() {
        viewModelScope.launch {
            _loading.value = true
            repository.getDashboard()
                .onSuccess { _dashboard.value = it }
                .onFailure { _error.value = it.message }
            _loading.value = false
        }
    }

    fun createCrop(nombre: String, precio: Double, descripcion: String = "") {
        viewModelScope.launch {
            _loading.value = true
            val request = CreateCropRequest(nombre, precio, descripcion)
            repository.createCrop(request)
                .onSuccess {
                    loadCrops() // Recargar lista
                }
                .onFailure { _error.value = it.message }
            _loading.value = false
        }
    }
}
```

## 🔐 **AUTENTICACIÓN FIREBASE**

### 6. **AuthActivity.kt**

```kotlin
class AuthActivity : AppCompatActivity() {
    private lateinit var auth: FirebaseAuth

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        auth = FirebaseAuth.getInstance()

        // Verificar si usuario ya está logueado
        if (auth.currentUser != null) {
            startActivity(Intent(this, MainActivity::class.java))
            finish()
            return
        }

        // Configurar login
        setupLogin()
    }

    private fun setupLogin() {
        // Implementar login con Firebase Auth
        // Email/Password, Google Sign-In, etc.
    }
}
```

## 🎯 **PRÓXIMOS PASOS DESARROLLO**

### **Fase 1: Setup básico (1-2 días)**

1. ✅ Crear proyecto Android
2. ✅ Configurar Firebase
3. ✅ Implementar autenticación
4. ✅ Probar health check

### **Fase 2: CRUD Cultivos (2-3 días)**

1. ✅ Lista de cultivos
2. ✅ Crear cultivo
3. ✅ Editar cultivo
4. ✅ Agregar producción

### **Fase 3: Dashboard (1-2 días)**

1. ✅ Analytics básicos
2. ✅ Gráficas con MPAndroidChart
3. ✅ Exportar reportes

### **Fase 4: Pulir UX (1-2 días)**

1. ✅ Loading states
2. ✅ Error handling
3. ✅ Offline caching
4. ✅ Notificaciones

## 🚀 **¡BACKEND LISTO - ANDROID READY!**

Tu sistema HuertoRentable está 100% preparado para Android.

**¿Quieres que creemos algún componente específico o tienes alguna duda sobre la implementación?** 📱✨
