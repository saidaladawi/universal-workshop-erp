#!/bin/bash
# GitHub workflow automation for Universal Workshop ERP

set -e

# Function to create feature branch and PR
create_feature() {
    local feature_name=$1
    local module=$2
    local description=$3
    
    echo "🚀 Creating feature: $feature_name"
    
    # Create and switch to feature branch
    git checkout develop
    git pull origin develop
    git checkout -b "feature/$module-$feature_name"
    
    echo "✨ Feature branch created: feature/$module-$feature_name"
    echo "💡 Next steps:"
    echo "1. Make your changes"
    echo "2. Run: git add . && git commit -m '✨ feat($module): $description'"
    echo "3. Run: git push origin feature/$module-$feature_name"
    echo "4. Run: gh pr create --base develop --title '$description'"
}

# Function to create hotfix
create_hotfix() {
    local issue_name=$1
    local description=$2
    
    echo "🔥 Creating hotfix: $issue_name"
    
    git checkout main
    git pull origin main
    git checkout -b "hotfix/$issue_name"
    
    echo "🚨 Hotfix branch created: hotfix/$issue_name"
    echo "💡 Next steps:"
    echo "1. Fix the critical issue"
    echo "2. Run: git add . && git commit -m '🐛 hotfix: $description'"
    echo "3. Run: git push origin hotfix/$issue_name"
    echo "4. Create PR to main: gh pr create --base main --title 'Hotfix: $description'"
}

# Function to create release
create_release() {
    local version=$1
    
    echo "📦 Creating release: v$version"
    
    git checkout develop
    git pull origin develop
    git checkout -b "release/v$version"
    
    # Update version in key files
    echo "📝 Update version in:"
    echo "  - apps/universal_workshop/hooks.py"
    echo "  - apps/universal_workshop/package.json"
    echo "  - apps/universal_workshop/frontend_v2/package.json"
    
    echo "🔖 Release branch created: release/v$version"
    echo "💡 Next steps:"
    echo "1. Update version numbers"
    echo "2. Update CHANGELOG.md"
    echo "3. Test thoroughly"
    echo "4. Run: ./scripts/finalize_release.sh v$version"
}

# Function to sync with remote
sync_repo() {
    echo "🔄 Syncing with remote repository..."
    
    git fetch origin
    git checkout main
    git pull origin main
    git checkout develop
    git pull origin develop
    
    echo "✅ Repository synced with remote"
    echo "📊 Recent commits on main:"
    git log --oneline -5 main
    echo "📊 Recent commits on develop:"
    git log --oneline -5 develop
}

# Function to check repository health
check_health() {
    echo "🏥 Repository Health Check"
    echo "=========================="
    
    # Check branch status
    echo "📋 Current branch: $(git branch --show-current)"
    echo "📋 Status: $(git status --porcelain | wc -l) uncommitted changes"
    
    # Check remote sync
    git fetch origin
    local behind=$(git rev-list --count HEAD..origin/$(git branch --show-current) 2>/dev/null || echo "0")
    local ahead=$(git rev-list --count origin/$(git branch --show-current)..HEAD 2>/dev/null || echo "0")
    
    echo "📋 Remote sync: $ahead commits ahead, $behind commits behind"
    
    # Check for large files
    echo "📋 Large files (>1MB):"
    find . -type f -size +1M -not -path './.git/*' | head -5
    
    # Check Arabic files
    echo "📋 Arabic files detected:"
    find . -name "*.py" -o -name "*.js" -o -name "*.vue" | xargs grep -l "[\u0600-\u06FF]" 2>/dev/null | head -5 || echo "  None found in current scan"
    
    echo "✅ Health check completed"
}

# Main script logic
case "$1" in
    "feature")
        if [ $# -lt 4 ]; then
            echo "Usage: $0 feature <name> <module> <description>"
            echo "Example: $0 feature barcode-scanner inventory 'Add barcode scanning to parts inventory'"
            exit 1
        fi
        create_feature "$2" "$3" "$4"
        ;;
    "hotfix")
        if [ $# -lt 3 ]; then
            echo "Usage: $0 hotfix <name> <description>"
            echo "Example: $0 hotfix vat-calculation 'Fix VAT calculation for services'"
            exit 1
        fi
        create_hotfix "$2" "$3"
        ;;
    "release")
        if [ $# -lt 2 ]; then
            echo "Usage: $0 release <version>"
            echo "Example: $0 release 2.1.0"
            exit 1
        fi
        create_release "$2"
        ;;
    "sync")
        sync_repo
        ;;
    "health")
        check_health
        ;;
    *)
        echo "Universal Workshop ERP - GitHub Workflow Helper"
        echo "=============================================="
        echo ""
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  feature <name> <module> <description>  Create feature branch and setup"
        echo "  hotfix <name> <description>            Create hotfix branch for critical issues"
        echo "  release <version>                      Create release branch"
        echo "  sync                                   Sync with remote repository"
        echo "  health                                 Check repository health"
        echo ""
        echo "Examples:"
        echo "  $0 feature mobile-ui mobile 'Enhance Arabic mobile interface'"
        echo "  $0 hotfix security-patch 'Fix authentication vulnerability'"
        echo "  $0 release 2.1.0"
        echo "  $0 sync"
        echo "  $0 health"
        ;;
esac