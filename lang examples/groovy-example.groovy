// ApiService.groovy
package com.example.service

import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import groovy.transform.CompileStatic

import org.springframework.stereotype.Service
import org.springframework.beans.factory.annotation.Value
import com.google.common.cache.CacheBuilder

import com.example.model.User
import com.example.exception.ApiException

@Service
@CompileStatic
class ApiService {
    
    @Value('${api.base.url}')
    private String baseUrl
    
    private final JsonSlurper jsonSlurper = new JsonSlurper()
    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build()
    
    List<User> getUsers() {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("${baseUrl}/users"))
                .header("Content-Type", "application/json")
                .GET()
                .build()
                
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString())
            
            if (response.statusCode() == 200) {
                def data = jsonSlurper.parseText(response.body())
                return data.collect { new User(id: it.id, name: it.name, email: it.email) }
            } else {
                throw new ApiException("Failed to fetch users: ${response.statusCode()}")
            }
        } catch (Exception e) {
            throw new ApiException("Error accessing API: ${e.message}")
        }
    }
}