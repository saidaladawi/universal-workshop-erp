// API Performance Dashboard JavaScript
$(document).ready(function () {
    loadDashboardData();

    // Auto-refresh every 30 seconds
    setInterval(loadDashboardData, 30000);
});

function loadDashboardData() {
    frappe.call({
        method: 'universal_workshop.vehicle_management.live_api_test.get_api_performance_dashboard',
        callback: function (r) {
            if (r.message && !r.message.error) {
                updateStatusCards(r.message.current_status);
                updateLastSyncTime(r.message.last_sync_time);
            } else {
                showError('Failed to load dashboard data: ' + (r.message?.error || 'Unknown error'));
            }
        },
        error: function (xhr) {
            showError('Connection error while loading dashboard data');
        }
    });
}

function updateStatusCards(status) {
    // Update NHTSA API status
    const nhtsaStatus = $('#nhtsa-status');
    const nhtsaCheck = $('#nhtsa-last-check');

    if (status.nhtsa_status === 'online') {
        nhtsaStatus.html('<span class="badge badge-success">Online</span>');
    } else if (status.nhtsa_status === 'error') {
        nhtsaStatus.html('<span class="badge badge-warning">Error</span>');
    } else {
        nhtsaStatus.html('<span class="badge badge-danger">Offline</span>');
    }

    nhtsaCheck.text('Last checked: ' + new Date().toLocaleTimeString());

    // Update Local Fallback status
    const localStatus = $('#local-status');
    const localCount = $('#local-count');

    if (status.local_fallback_status === 'available') {
        localStatus.html('<span class="badge badge-success">Available</span>');

        // Get count of local makes
        frappe.call({
            method: 'frappe.client.get_count',
            args: {
                doctype: 'Vehicle Make'
            },
            callback: function (r) {
                if (r.message) {
                    localCount.text('Records: ' + r.message);
                }
            }
        });
    } else if (status.local_fallback_status === 'empty') {
        localStatus.html('<span class="badge badge-warning">Empty</span>');
        localCount.text('Records: 0');
    } else {
        localStatus.html('<span class="badge badge-danger">Error</span>');
        localCount.text('Records: Unknown');
    }

    // Update Arabic Support status
    updateArabicStatus();
}

function updateArabicStatus() {
    frappe.call({
        method: 'frappe.client.get_count',
        args: {
            doctype: 'Vehicle Make',
            filters: [['make_name_ar', '!=', '']]
        },
        callback: function (r) {
            const arabicStatus = $('#arabic-status');
            const arabicCoverage = $('#arabic-coverage');

            if (r.message > 0) {
                arabicStatus.html('<span class="badge badge-success">Active</span>');

                // Calculate coverage percentage
                frappe.call({
                    method: 'frappe.client.get_count',
                    args: {
                        doctype: 'Vehicle Make'
                    },
                    callback: function (total) {
                        if (total.message > 0) {
                            const percentage = Math.round((r.message / total.message) * 100);
                            arabicCoverage.text('Coverage: ' + percentage + '%');
                        }
                    }
                });
            } else {
                arabicStatus.html('<span class="badge badge-warning">Limited</span>');
                arabicCoverage.text('Coverage: 0%');
            }
        },
        error: function () {
            $('#arabic-status').html('<span class="badge badge-danger">Error</span>');
            $('#arabic-coverage').text('Coverage: Unknown');
        }
    });
}

function updateLastSyncTime(lastSync) {
    if (lastSync) {
        const syncDate = new Date(lastSync);
        const timeAgo = getTimeAgo(syncDate);
        $('.last-sync-time').text('Last sync: ' + timeAgo);
    } else {
        $('.last-sync-time').text('Last sync: Never');
    }
}

function runLiveTests() {
    // Show progress modal
    $('#testProgressModal').modal('show');

    // Reset progress
    $('.progress-bar').css('width', '0%');
    $('#test-progress-log').html('<p>Initializing comprehensive API tests...</p>');

    // Start the tests
    frappe.call({
        method: 'universal_workshop.vehicle_management.live_api_test.run_live_api_tests',
        callback: function (r) {
            if (r.message) {
                displayTestResults(r.message);
                updateProgress(100, 'Tests completed successfully!');

                // Hide modal after 2 seconds
                setTimeout(function () {
                    $('#testProgressModal').modal('hide');
                }, 2000);

                // Refresh dashboard data
                loadDashboardData();
            } else {
                updateProgress(100, 'Tests failed. Please check the logs.');
            }
        },
        error: function (xhr) {
            updateProgress(100, 'Error running tests: ' + xhr.responseText);
        }
    });

    // Simulate progress updates
    simulateProgress();
}

function simulateProgress() {
    const tests = [
        'Testing API connectivity...',
        'Checking data quality...',
        'Testing fallback mechanisms...',
        'Analyzing cache performance...',
        'Running concurrent tests...',
        'Checking GCC coverage...',
        'Validating Arabic translations...',
        'Generating recommendations...'
    ];

    let currentTest = 0;
    const progressInterval = setInterval(function () {
        if (currentTest < tests.length) {
            const progress = ((currentTest + 1) / tests.length) * 90; // Up to 90%
            updateProgress(progress, tests[currentTest]);
            currentTest++;
        } else {
            clearInterval(progressInterval);
        }
    }, 2000);
}

function updateProgress(percentage, message) {
    $('.progress-bar').css('width', percentage + '%');
    $('#test-progress-log').append('<p><small class="text-muted">' + new Date().toLocaleTimeString() + '</small> ' + message + '</p>');

    // Scroll to bottom
    const log = document.getElementById('test-progress-log');
    log.scrollTop = log.scrollHeight;
}

function displayTestResults(results) {
    // Update performance metrics
    const metricsHtml = generateMetricsHtml(results);
    $('#performance-metrics').html(metricsHtml);

    // Update test results
    const resultsHtml = generateResultsHtml(results);
    $('#test-results').html(resultsHtml);

    // Update recommendations
    const recommendationsHtml = generateRecommendationsHtml(results.optimization_recommendations);
    $('#recommendations').html(recommendationsHtml);
}

function generateMetricsHtml(results) {
    let html = '<div class="row">';

    // Overall Health Score
    const healthScore = results.overall_health_score || 0;
    const healthClass = healthScore >= 80 ? 'success' : healthScore >= 60 ? 'warning' : 'danger';

    html += `
        <div class="col-md-3">
            <div class="metric-card card">
                <div class="card-body text-center">
                    <div class="metric-value text-${healthClass}">${healthScore}</div>
                    <small class="text-muted">Overall Health Score</small>
                </div>
            </div>
        </div>
    `;

    // API Response Times
    if (results.api_status) {
        Object.keys(results.api_status).forEach(api => {
            const status = results.api_status[api];
            const responseTime = status.response_time || 0;
            const timeClass = responseTime < 3000 ? 'success' : responseTime < 5000 ? 'warning' : 'danger';

            html += `
                <div class="col-md-3">
                    <div class="metric-card card">
                        <div class="card-body text-center">
                            <div class="metric-value text-${timeClass}">${responseTime}ms</div>
                            <small class="text-muted">${api} Response Time</small>
                        </div>
                    </div>
                </div>
            `;
        });
    }

    html += '</div>';

    // Additional metrics
    if (results.performance_metrics) {
        html += '<div class="row mt-3">';

        // Cache performance
        const cache = results.performance_metrics.cache;
        if (cache) {
            html += `
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">Cache Performance</div>
                        <div class="card-body">
                            <p>Hit Time: ${cache.cache_hit_time || 0}ms</p>
                            <p>Miss Time: ${cache.cache_miss_time || 0}ms</p>
                            <p>Improvement: ${cache.performance_improvement || 0}%</p>
                        </div>
                    </div>
                </div>
            `;
        }

        // GCC Coverage
        const gcc = results.performance_metrics.gcc_coverage;
        if (gcc) {
            html += `
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">GCC Market Coverage</div>
                        <div class="card-body">
            `;

            Object.keys(gcc).forEach(make => {
                const coverage = gcc[make];
                if (coverage.coverage_percentage !== undefined) {
                    html += `<p>${make}: ${coverage.coverage_percentage}%</p>`;
                }
            });

            html += '</div></div></div>';
        }

        // Arabic Quality
        const arabic = results.performance_metrics.arabic_translations;
        if (arabic) {
            html += `
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">Arabic Translations</div>
                        <div class="card-body">
                            <p>Quality Score: ${arabic.quality_percentage || 0}%</p>
                            <p>Makes with Arabic: ${arabic.makes_with_arabic || 0}</p>
                            <p>Total Tested: ${arabic.total_makes_tested || 0}</p>
                        </div>
                    </div>
                </div>
            `;
        }

        html += '</div>';
    }

    return html;
}

function generateResultsHtml(results) {
    let html = '<div class="table-responsive">';
    html += '<table class="table table-striped">';
    html += '<thead><tr><th>Test</th><th>Status</th><th>Details</th></tr></thead><tbody>';

    if (results.tests_performed) {
        results.tests_performed.forEach(test => {
            html += `
                <tr>
                    <td>${test}</td>
                    <td><span class="badge badge-success">Completed</span></td>
                    <td>Test executed successfully</td>
                </tr>
            `;
        });
    }

    if (results.errors && results.errors.length > 0) {
        results.errors.forEach(error => {
            html += `
                <tr>
                    <td>Error</td>
                    <td><span class="badge badge-danger">Failed</span></td>
                    <td>${error}</td>
                </tr>
            `;
        });
    }

    html += '</tbody></table></div>';

    return html;
}

function generateRecommendationsHtml(recommendations) {
    if (!recommendations || recommendations.length === 0) {
        return '<p class="text-muted">No optimization recommendations at this time.</p>';
    }

    let html = '';

    recommendations.forEach(rec => {
        const priorityClass = 'recommendation-' + rec.priority;
        html += `
            <div class="recommendation-item ${priorityClass}">
                <h6>
                    <span class="badge badge-${rec.priority === 'high' ? 'danger' : rec.priority === 'medium' ? 'warning' : 'success'}">${rec.priority.toUpperCase()}</span>
                    ${rec.category.replace('_', ' ').toUpperCase()}
                </h6>
                <p><strong>Issue:</strong> ${rec.description}</p>
                <p><strong>Suggestion:</strong> ${rec.suggestion}</p>
            </div>
        `;
    });

    return html;
}

function getTimeAgo(date) {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return days + ' day' + (days > 1 ? 's' : '') + ' ago';
    if (hours > 0) return hours + ' hour' + (hours > 1 ? 's' : '') + ' ago';
    if (minutes > 0) return minutes + ' minute' + (minutes > 1 ? 's' : '') + ' ago';
    return 'Just now';
}

function showError(message) {
    frappe.msgprint({
        title: 'Error',
        message: message,
        indicator: 'red'
    });
} 