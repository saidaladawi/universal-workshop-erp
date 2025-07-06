#!/bin/bash
# Dead Code Cleanup Script for Universal Workshop
# Safely removes empty and skeleton files

echo "Starting dead code cleanup..."

# Create backup directory
BACKUP_DIR="archives/dead_code_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Counter
REMOVED=0

# Find and remove empty __init__.py files
echo "Finding empty __init__.py files..."
while IFS= read -r file; do
    if [ -f "$file" ] && [ ! -s "$file" ]; then
        # Create backup
        mkdir -p "$BACKUP_DIR/$(dirname "$file")"
        cp "$file" "$BACKUP_DIR/$file"
        # Remove file
        rm "$file"
        ((REMOVED++))
        echo "Removed: $file"
    fi
done < <(find . -name "__init__.py" -type f)

# Remove other identified empty files
echo -e "\nRemoving other empty/skeleton files..."

# Empty session_manager.py
if [ -f "core/session_manager.py" ] && [ ! -s "core/session_manager.py" ]; then
    mkdir -p "$BACKUP_DIR/core"
    cp "core/session_manager.py" "$BACKUP_DIR/core/"
    rm "core/session_manager.py"
    ((REMOVED++))
    echo "Removed: core/session_manager.py"
fi

# Single space asset_optimization.py
if [ -f "shared_libraries/utils/asset_optimization.py" ]; then
    SIZE=$(wc -c < "shared_libraries/utils/asset_optimization.py")
    if [ "$SIZE" -le 2 ]; then
        mkdir -p "$BACKUP_DIR/shared_libraries/utils"
        cp "shared_libraries/utils/asset_optimization.py" "$BACKUP_DIR/shared_libraries/utils/"
        rm "shared_libraries/utils/asset_optimization.py"
        ((REMOVED++))
        echo "Removed: shared_libraries/utils/asset_optimization.py"
    fi
fi

# Remove .gitkeep files
find . -name ".gitkeep" -type f -exec rm {} \; -exec echo "Removed: {}" \;

echo -e "\n✅ Cleanup complete!"
echo "Total files removed: $REMOVED"
echo "Backup created at: $BACKUP_DIR"
echo -e "\nTo restore if needed:"
echo "cp -r $BACKUP_DIR/* ."