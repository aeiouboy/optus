#!/bin/bash

# Cleanup script for scraping results
echo "🧹 Cleaning up scraping results..."

SCRAPING_DIR="/Users/tachongrak/Projects/Optus/apps/output/scraping"
TODAY_DIR="$SCRAPING_DIR/2025-11-22"

# Create a backup directory for important results
BACKUP_DIR="$SCRAPING_DIR/backups/$(date +%Y-%m-%d_%H-%M-%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Backing up important results..."

# Keep only the largest/most recent results and remove duplicates
if [ -d "$TODAY_DIR" ]; then
    echo "📊 Found $(ls "$TODAY_DIR" | wc -l) result folders for today"
    
    # Keep the 2 largest result folders (to preserve the most comprehensive data)
    cd "$TODAY_DIR"
    
    # Sort folders by size and keep only the 2 largest
    ls -1 | while read folder; do
        if [ -d "$folder" ]; then
            size=$(du -s "$folder" | cut -f1)
            echo "$size $folder"
        fi
    done | sort -nr | tail -n +3 | cut -d' ' -f2- > /tmp/folders_to_remove
    
    # Remove small/duplicate folders
    while read folder; do
        if [ -n "$folder" ] && [ -d "$folder" ]; then
            echo "🗑️  Removing: $folder ($(du -sh "$folder" | cut -f1))"
            rm -rf "$folder"
        fi
    done < /tmp/folders_to_remove
    
    # Keep the remaining 2 largest folders
    echo "✅ Kept $(ls "$TODAY_DIR" | wc -l) result folders"
fi

# Clean up old empty directories
echo "🧹 Cleaning up empty directories..."
find "$SCRAPING_DIR" -type d -empty -delete

# Show final result
echo "📈 Final scraping directory size: $(du -sh "$SCRAPING_DIR" | cut -f1)"
echo "✅ Cleanup complete!"

