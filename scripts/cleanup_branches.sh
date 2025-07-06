#!/bin/bash
# Branch cleanup script for Universal Workshop ERP
# Keep recent and important backups, clean old development branches

set -e

echo "🧹 Universal Workshop ERP - Branch Cleanup Strategy"
echo "=================================================="

# Keep these critical backups (don't delete)
KEEP_BRANCHES=(
    "backup-full-20250704_1334"     # Latest full backup
    "deep-refactor-backup"          # Important refactor backup
    "develop"                       # Development branch
    "main"                          # Production branch
    "archive-pre-refactor-remote"   # Historical archive
)

# Safe to delete - old interim backups
DELETE_LOCAL=(
    "backup-before-cleanup-20250704_1107"
    "backup-before-cleanup-20250704_1132"
    "restore-from-backup"
    "recover-universal-workshop"
    "refactor-v2-integration"
    "v2-complete-refactor"
)

echo "🔍 Current local branches:"
git branch

echo -e "\n📦 Keeping important backup branches:"
for branch in "${KEEP_BRANCHES[@]}"; do
    if git show-ref --verify --quiet refs/heads/$branch; then
        echo "  ✅ $branch"
    fi
done

echo -e "\n🗑️  Branches to delete locally:"
for branch in "${DELETE_LOCAL[@]}"; do
    if git show-ref --verify --quiet refs/heads/$branch; then
        echo "  🔄 $branch"
        git branch -D "$branch" 2>/dev/null || echo "    ⚠️  Failed to delete $branch"
    else
        echo "  ➖ $branch (already deleted)"
    fi
done

echo -e "\n🌐 Remote branch cleanup:"
echo "Deleting old backup branches from remote..."
for branch in "${DELETE_LOCAL[@]}"; do
    if git ls-remote --heads origin "$branch" | grep -q "$branch"; then
        echo "  🔄 Deleting remote: $branch"
        git push origin --delete "$branch" 2>/dev/null || echo "    ⚠️  Failed to delete remote $branch"
    fi
done

echo -e "\n✅ Cleanup completed!"
echo "📊 Remaining branches:"
git branch

echo -e "\n💡 Recommendations:"
echo "1. Keep backup-full-20250704_1334 as your recovery point"
echo "2. Use 'develop' branch for future development"
echo "3. Create feature branches from 'develop'"
echo "4. Use release branches for version preparation"