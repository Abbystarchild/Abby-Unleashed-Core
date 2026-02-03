```kotlin
import io.ktor.application.*
import io.ktor.features.*
import io.ktor.gson.*
import io.ktor.http.*
import io.ktor.request.*
import io.ktor.response.*
import io.ktor.routing.*
import io.ktor.server.engine.*
import io.ktor.server.netty.*
import kotlinx.coroutines.*
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.util.*

// Data classes for request/response bodies
data class MeetupRequest(
    val userId: String,
    val meetupDate: String, // ISO format date string
    val location: String,
    val isEscortRequired: Boolean = false,
    val notes: String? = null
)

data class MeetupResponse(
    val id: