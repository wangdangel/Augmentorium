<?php
// UserRepository.php

namespace App\Repository;

require_once __DIR__ . '/../vendor/autoload.php';
include_once __DIR__ . '/../config/database.php';

use PDO;
use Monolog\Logger;
use Monolog\Handler\StreamHandler;
use Ramsey\Uuid\Uuid;

class UserRepository 
{
    private PDO $db;
    private Logger $logger;
    
    public function __construct(PDO $db) 
    {
        $this->db = $db;
        $this->logger = new Logger('user_repository');
        $this->logger->pushHandler(new StreamHandler(__DIR__ . '/../logs/app.log', Logger::INFO));
    }
    
    public function findById(string $id): ?array 
    {
        $stmt = $this->db->prepare('SELECT * FROM users WHERE id = :id');
        $stmt->execute(['id' => $id]);
        $this->logger->info('User lookup by ID: ' . $id);
        
        return $stmt->fetch(PDO::FETCH_ASSOC) ?: null;
    }
}