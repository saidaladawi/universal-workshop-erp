module.exports = {
  branches: [
    'main',
    'master',
    {
      name: 'develop',
      prerelease: 'beta'
    }
  ],
  plugins: [
    // Analyze commits to determine version bump
    [
      '@semantic-release/commit-analyzer',
      {
        preset: 'angular',
        releaseRules: [
          { type: 'feat', release: 'minor' },
          { type: 'fix', release: 'patch' },
          { type: 'perf', release: 'patch' },
          { type: 'revert', release: 'patch' },
          { type: 'docs', release: false },
          { type: 'style', release: false },
          { type: 'chore', release: false },
          { type: 'refactor', release: 'patch' },
          { type: 'test', release: false },
          { breaking: true, release: 'major' }
        ],
        parserOpts: {
          noteKeywords: ['BREAKING CHANGE', 'BREAKING CHANGES']
        }
      }
    ],

    // Generate release notes
    [
      '@semantic-release/release-notes-generator',
      {
        preset: 'angular',
        parserOpts: {
          noteKeywords: ['BREAKING CHANGE', 'BREAKING CHANGES']
        },
        writerOpts: {
          commitsSort: ['subject', 'scope']
        },
        presetConfig: {
          types: [
            { type: 'feat', section: '✨ Features / الميزات الجديدة' },
            { type: 'fix', section: '🐛 Bug Fixes / إصلاح الأخطاء' },
            { type: 'perf', section: '⚡ Performance / تحسين الأداء' },
            { type: 'revert', section: '⏪ Reverts / التراجع' },
            { type: 'docs', section: '📚 Documentation / التوثيق', hidden: false },
            { type: 'style', section: '💄 Styles / التنسيق', hidden: true },
            { type: 'chore', section: '🔧 Chores / أعمال صيانة', hidden: true },
            { type: 'refactor', section: '♻️ Code Refactoring / إعادة هيكلة الكود' },
            { type: 'test', section: '✅ Tests / الاختبارات', hidden: true },
            { type: 'build', section: '👷 Build System / نظام البناء', hidden: true },
            { type: 'ci', section: '💚 CI/CD', hidden: true }
          ]
        }
      }
    ],

    // Update changelog
    [
      '@semantic-release/changelog',
      {
        changelogFile: 'CHANGELOG.md',
        changelogTitle: '# Universal Workshop ERP Changelog\n\n## نظام إدارة الورش الشامل - سجل التغييرات\n\nAll notable changes to this project will be documented in this file.\nجميع التغييرات المهمة في هذا المشروع سيتم توثيقها في هذا الملف.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),\nand this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n'
      }
    ],

    // Update package.json and other files
    [
      '@semantic-release/exec',
      {
        prepareCmd: 'echo "Updating version to ${nextRelease.version}"',
        publishCmd: 'echo "Publishing version ${nextRelease.version}"'
      }
    ],

    // Commit updated files
    [
      '@semantic-release/git',
      {
        assets: [
          'CHANGELOG.md',
          'apps/universal_workshop/universal_workshop/__init__.py',
          'apps/universal_workshop/setup.py',
          'package.json'
        ],
        message: 'chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}'
      }
    ],

    // Create GitHub release
    [
      '@semantic-release/github',
      {
        assets: [
          {
            path: 'releases/*.tar.gz',
            label: 'Installation Archives'
          }
        ],
        releaseBodyTemplate: `## Universal Workshop ERP v{{version}}
### نظام إدارة الورش الشامل

{{#each commits}}
{{#if breaking}}
### 💥 BREAKING CHANGES
{{#each breaking}}
- {{.}}
{{/each}}
{{/if}}
{{/each}}

### Changes / التغييرات
{{body}}

---

## Installation / التثبيت

### Quick Install / التثبيت السريع
\`\`\`bash
curl -fsSL https://github.com/saidaladawi/universal-workshop-erp/releases/download/v{{version}}/install.sh | bash
\`\`\`

### Docker Install / تثبيت Docker
\`\`\`bash
docker-compose up -d
\`\`\`

## Requirements / المتطلبات
- Ubuntu 20.04+ / أوبنتو 20.04 أو أحدث
- 4GB RAM minimum / 4 جيجابايت رام كحد أدنى
- Python 3.10+ / بايثون 3.10 أو أحدث
- MariaDB 10.6+ / ماريا دي بي 10.6 أو أحدث

## Support / الدعم
- 📧 Email: al.a.dawi@hotmail.com
- 📱 Phone: +968 95351993
- 🌐 GitHub: https://github.com/saidaladawi/universal-workshop-erp`
      }
    ]
  ]
}; 