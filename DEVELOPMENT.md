# Universal Workshop ERP - Development Guide

## 🚀 Quick Start Development Workflow

### Daily Development Commands

```bash
# 1. Start new feature
./scripts/github_workflow.sh feature mobile-ui mobile "Enhance Arabic mobile interface"

# 2. Make changes and commit
git add .
git commit -m "✨ feat(mobile): Add Arabic RTL support for mobile forms"

# 3. Push and create PR
git push origin feature/mobile-mobile-ui
gh pr create --base develop --title "Mobile: Enhance Arabic mobile interface"

# 4. After PR approval, clean up
git checkout develop
git pull origin develop
git branch -d feature/mobile-mobile-ui
```

### Repository Management

```bash
# Check repository health
./scripts/repo_analytics.sh

# Clean up old branches
./scripts/cleanup_branches.sh

# Sync with remote
./scripts/github_workflow.sh sync
```

## 🌳 Branch Strategy

### Branch Types & Purpose

- **main**: Production-ready code (protected)
- **develop**: Integration branch for next release
- **feature/[module]-[name]**: New feature development
- **hotfix/[name]**: Critical production fixes
- **release/v[version]**: Release preparation

### Module-Based Feature Branches

```bash
# Workshop management features
git checkout -b feature/workshop-service-scheduling

# Billing system enhancements
git checkout -b feature/billing-vat-compliance

# Arabic/Mobile improvements
git checkout -b feature/mobile-arabic-forms

# Inventory management
git checkout -b feature/inventory-barcode-scanning
```

## 📝 Commit Message Standards

### Format: `<type>(<scope>): <description>`

#### Types:
- `✨ feat`: New feature
- `🐛 fix`: Bug fix
- `📝 docs`: Documentation
- `🎨 style`: Formatting, no code change
- `♻️ refactor`: Code restructuring
- `🔒 security`: Security improvements
- `🌐 arabic`: Arabic/RTL specific changes
- `📱 mobile`: Mobile interface changes
- `🧪 test`: Adding tests
- `🔧 chore`: Maintenance tasks

#### Scopes (ERP Modules):
- `workshop`: Workshop management
- `billing`: Billing and invoicing
- `inventory`: Parts and inventory
- `mobile`: Mobile interface
- `arabic`: Arabic/RTL features
- `customer`: Customer management
- `vehicle`: Vehicle registry
- `api`: API endpoints
- `security`: Security features

#### Examples:
```bash
✨ feat(workshop): Add vehicle inspection workflow
🐛 fix(billing): Resolve Omani VAT calculation error
🌐 arabic(mobile): Improve RTL layout for forms
📱 mobile(inventory): Add barcode scanner interface
🔒 security(api): Implement rate limiting
```

## 🧪 Testing Strategy

### Test Categories

```bash
# Unit tests
pytest apps/universal_workshop/universal_workshop/ -m "not integration"

# Integration tests
pytest apps/universal_workshop/universal_workshop/ -m integration

# Arabic language tests
pytest apps/universal_workshop/universal_workshop/ -m arabic

# Security tests
pytest apps/universal_workshop/universal_workshop/ -m security

# Performance tests
pytest apps/universal_workshop/universal_workshop/ -m performance
```

### Pre-commit Testing

The pre-commit hook automatically runs:
- ✅ Arabic text encoding validation
- ✅ Sensitive data detection
- ✅ Python code quality (Ruff)
- ✅ File size checks
- ✅ Console.log detection

## 🔄 Release Process

### 1. Create Release Branch
```bash
./scripts/github_workflow.sh release 2.1.0
```

### 2. Update Version Numbers
```bash
# Update in these files:
- apps/universal_workshop/hooks.py
- apps/universal_workshop/package.json
- apps/universal_workshop/frontend_v2/package.json
```

### 3. Finalize Release
```bash
# Test thoroughly
bench run-tests --app universal_workshop

# Merge to main
git checkout main
git merge --no-ff release/v2.1.0
git tag -a v2.1.0 -m "Release v2.1.0: Enhanced Mobile Arabic Interface"
git push origin main --tags

# Merge back to develop
git checkout develop
git merge --no-ff release/v2.1.0
git push origin develop
```

## 🚨 Hotfix Process

### Critical Production Issues

```bash
# Create hotfix
./scripts/github_workflow.sh hotfix security-patch "Fix authentication vulnerability"

# Make fix
git add .
git commit -m "🔒 hotfix(security): Fix session validation vulnerability"

# Deploy immediately
git checkout main
git merge --no-ff hotfix/security-patch
git tag -a v2.0.1 -m "Hotfix v2.0.1: Security patch"
git push origin main --tags

# Merge to develop
git checkout develop
git merge --no-ff hotfix/security-patch
git push origin develop
```

## 📊 Monitoring & Analytics

### Repository Health Checks
```bash
# Daily health check
./scripts/repo_analytics.sh

# Weekly cleanup
./scripts/cleanup_branches.sh
```

### Development Metrics
- Track commits per module
- Monitor Arabic content coverage
- Test coverage reports
- Performance benchmarks

## 🔐 Security Guidelines

### Sensitive Data Protection
- ❌ Never commit passwords, API keys, or secrets
- ✅ Use environment variables for configuration
- ✅ Template files (.env.template) for environment setup
- ✅ Pre-commit hooks scan for sensitive patterns

### Arabic Content Security
- ✅ Ensure UTF-8 encoding for all Arabic text
- ✅ Validate RTL layout security
- ✅ Test Arabic input sanitization

## 🌐 Internationalization (i18n)

### Arabic Language Development
```bash
# Find Arabic content
git arabic-files

# Check Arabic commits
git arabic-commits

# Test Arabic features
pytest -m arabic
```

### RTL Development Guidelines
- Use CSS logical properties (`margin-inline-start` vs `margin-left`)
- Test on RTL and LTR layouts
- Validate number formatting (Arabic vs Western numerals)
- Ensure proper text alignment

## 🛠️ Tools & Automation

### Git Aliases (Already configured)
```bash
# Module-specific aliases
git workshop feature-name    # Creates feature/workshop-feature-name
git billing enhancement      # Creates feature/billing-enhancement
git mobile ui-improvement    # Creates feature/mobile-ui-improvement

# Quick commits
git feat workshop "Add service scheduling"
git fix billing "Resolve VAT calculation"
git arabic mobile "Improve RTL forms"
```

### Automation Scripts
- `./scripts/github_workflow.sh` - Feature/hotfix/release management
- `./scripts/repo_analytics.sh` - Repository metrics
- `./scripts/cleanup_branches.sh` - Branch maintenance

## 📚 Additional Resources

- [Frappe Framework Documentation](https://frappeframework.com/docs)
- [ERPNext Developer Guide](https://docs.erpnext.com/docs/v15/user/manual/en/setting-up/articles/developing-erpnext)
- [Arabic RTL Best Practices](docs/arabic-development.md)
- [Mobile Development Guidelines](docs/mobile-development.md)

---

## 🤝 Team Collaboration

### Code Review Process
1. ✅ Technical accuracy (business logic)
2. ✅ Arabic language validation (by Arabic speaker)
3. ✅ Security review (for sensitive operations)
4. ✅ Mobile compatibility (responsive design)
5. ✅ Test coverage verification

### Communication
- Use GitHub Issues for bug reports
- Use GitHub Discussions for feature planning
- Tag reviewers based on expertise:
  - `@arabic-reviewer` for RTL/Arabic changes
  - `@security-team` for security-related PRs
  - `@mobile-expert` for mobile interface changes

This development guide ensures consistent, professional, and scalable development for the Universal Workshop ERP system.