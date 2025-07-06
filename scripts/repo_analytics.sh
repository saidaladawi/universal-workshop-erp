#!/bin/bash
# Repository analytics for Universal Workshop ERP

echo "📊 Universal Workshop ERP - Repository Analytics"
echo "==============================================="

# Code statistics
echo "📝 Code Statistics:"
echo "==================="
find apps/universal_workshop -name "*.py" 2>/dev/null | wc -l | xargs echo "Python files:"
find apps/universal_workshop -name "*.js" 2>/dev/null | wc -l | xargs echo "JavaScript files:"
find apps/universal_workshop -name "*.vue" 2>/dev/null | wc -l | xargs echo "Vue.js files:"
find apps/universal_workshop -name "*.json" -path "*/doctype/*" 2>/dev/null | wc -l | xargs echo "DocType definitions:"

# Module breakdown
echo -e "\n🏗️  Module Structure:"
echo "==================="
for module in apps/universal_workshop/universal_workshop/*/; do
    if [ -d "$module" ]; then
        module_name=$(basename "$module")
        py_files=$(find "$module" -name "*.py" | wc -l)
        js_files=$(find "$module" -name "*.js" | wc -l)
        echo "$module_name: $py_files Python, $js_files JavaScript files"
    fi
done | sort

# Arabic content analysis
echo -e "\n🌐 Arabic Content Analysis:"
echo "========================="
arabic_py=$(find apps/universal_workshop -name "*.py" 2>/dev/null | xargs grep -l "[\u0600-\u06FF]" 2>/dev/null | wc -l || echo 0)
arabic_js=$(find apps/universal_workshop -name "*.js" 2>/dev/null | xargs grep -l "[\u0600-\u06FF]" 2>/dev/null | wc -l || echo 0)
echo "Files with Arabic content: $arabic_py Python, $arabic_js JavaScript"

# Recent development activity
echo -e "\n📈 Development Activity (Last 30 days):"
echo "======================================"
git log --since="30 days ago" --oneline | wc -l | xargs echo "Commits:"
git log --since="30 days ago" --format="%an" | sort | uniq -c | sort -rn | head -5

# Branch analysis
echo -e "\n🌳 Branch Analysis:"
echo "=================="
echo "Total branches: $(git branch -a | wc -l)"
echo "Local branches: $(git branch | wc -l)"
echo "Remote branches: $(git branch -r | wc -l)"

# Feature development tracking
echo -e "\n✨ Feature Development:"
echo "====================="
git log --grep="feat" --oneline --since="30 days ago" | wc -l | xargs echo "Feature commits (30 days):"
git log --grep="fix" --oneline --since="30 days ago" | wc -l | xargs echo "Bug fix commits (30 days):"
git log --grep="arabic" --oneline --since="30 days ago" | wc -l | xargs echo "Arabic-related commits (30 days):"

# File size analysis
echo -e "\n📦 Repository Size Analysis:"
echo "========================="
du -sh apps/universal_workshop 2>/dev/null | xargs echo "Universal Workshop app size:" || echo "Universal Workshop app size: Directory not found"
du -sh .git 2>/dev/null | xargs echo "Git repository size:" || echo "Git repository size: Not in git directory"

# Top contributors
echo -e "\n👥 Top Contributors (All Time):"
echo "============================="
git log --format="%an" | sort | uniq -c | sort -rn | head -10

# Test coverage info
echo -e "\n🧪 Testing Information:"
echo "====================="
find apps/universal_workshop -name "test_*.py" 2>/dev/null | wc -l | xargs echo "Test files:"
if [ -f "test_results/pytest_report.json" ]; then
    echo "Latest test results available in test_results/"
fi

echo -e "\n✅ Analytics completed!"
echo "💡 Use these metrics to track development progress and identify areas for improvement."