// server.go
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	
	"github.com/gorilla/mux"
	"github.com/joho/godotenv"
	"go.uber.org/zap"
)

type User struct {
	ID    int    `json:"id"`
	Name  string `json:"name"`
	Email string `json:"email"`
}

func main() {
	// Initialize logger
	logger, _ := zap.NewProduction()
	defer logger.Sync()
	
	// Load environment variables
	if err := godotenv.Load(); err != nil {
		logger.Fatal("Error loading .env file")
	}
	
	// Set up router
	r := mux.NewRouter()
	r.HandleFunc("/users", getUsers).Methods("GET")
	
	// Start server
	log.Fatal(http.ListenAndServe(":8080", r))
}

func getUsers(w http.ResponseWriter, r *http.Request) {
	users := []User{{ID: 1, Name: "John Doe", Email: "john@example.com"}}
	json.NewEncoder(w).Encode(users)
}