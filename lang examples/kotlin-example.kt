// UserRepository.kt
package com.example.repository

import java.time.LocalDateTime
import kotlin.collections.List

import org.jetbrains.exposed.sql.transactions.transaction
import retrofit2.Retrofit
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

import com.example.model.User
import com.example.service.ApiService

class UserRepository(
    private val apiService: ApiService,
    private val userDao: UserDao
) {
    suspend fun getUsers(): List<User> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getUsers()
            if (response.isSuccessful) {
                val users = response.body() ?: emptyList()
                // Cache users in local database
                saveUsers(users)
                users
            } else {
                // Fallback to local cache
                getUsersFromDatabase()
            }
        } catch (e: Exception) {
            getUsersFromDatabase()
        }
    }
    
    private fun saveUsers(users: List<User>) = transaction {
        users.forEach { userDao.insert(it) }
    }
}