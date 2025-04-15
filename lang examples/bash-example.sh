#!/bin/bash
# backup.sh

source ~/.bashrc
source ./config.sh
. ./utils.sh

# Import libraries
command -v jq >/dev/null 2>&1 || { echo "jq is required but not installed. Aborting."; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "aws-cli is required but not installed. Aborting."; exit 1; }
command -v curl >/dev/null 2>&1 || { echo "curl is required but not installed. Aborting."; exit 1; }

# Configuration
BACKUP_DIR="${BACKUP_ROOT:-/var/backups}/$(date +%Y-%m-%d)"
LOG_FILE="/var/log/backup-$(date +%Y-%m-%d).log"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Function to perform database backup
backup_database() {
    local db_name="$1"
    echo "Backing up database: $db_name" | tee -a "$LOG_FILE"
    pg_dump -U "$DB_USER" "$db_name" | gzip > "$BACKUP_DIR/$db_name.sql.gz"
    aws s3 cp "$BACKUP_DIR/$db_name.sql.gz" "s3://$S3_BUCKET/backups/"
}

# Main execution
backup_database "myapp_production"