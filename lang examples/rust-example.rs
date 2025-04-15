// user_service.rs
use std::env;
use std::collections::HashMap;
use std::error::Error;

use reqwest::Client;
use serde::{Deserialize, Serialize};
use log::{info, error};

#[derive(Debug, Serialize, Deserialize)]
pub struct User {
    id: u32,
    name: String,
    email: String,
}

pub struct UserService {
    client: Client,
    api_url: String,
}

impl UserService {
    pub fn new() -> Self {
        let api_url = env::var("API_URL").unwrap_or_else(|_| "https://api.example.com".to_string());
        
        UserService {
            client: Client::new(),
            api_url,
        }
    }
    
    pub async fn get_users(&self) -> Result<Vec<User>, Box<dyn Error>> {
        info!("Fetching all users");
        let response = self.client.get(&format!("{}/users", self.api_url))
            .send()
            .await?;
            
        let users = response.json::<Vec<User>>().await?;
        Ok(users)
    }
}