// Training Path Administration JavaScript
// Copyright (c) 2024, Universal Workshop and contributors

let dashboardData = {};
let enrollmentChart = null;
let trendsChart = null;

// Initialize the page
$(document).ready(function () {
    loadDashboardData();
    setupEventHandlers();
    loadRoles();
});

function loadDashboardData() {
    frappe.call({
        method: 'universal_workshop.www.training-path-admin.get_admin_dashboard_data',
        callback: function (r) {
            if (r.message) {
                dashboardData = r.message;
                updateOverviewStats();
                renderPathsByRole();
                renderCharts();
            }
        },
        error: function (err) {
            console.error('Error loading dashboard data:', err);
            frappe.msgprint('Error loading dashboard data. Please try again.');
        }
    });
}

function updateOverviewStats() {
    const overview = dashboardData.overview;
    $('#totalPaths').text(overview.total_paths);
    $('#totalEnrollments').text(overview.total_enrollments);
    $('#completionRate').text(overview.completion_rate + '%');
    $('#activeUsers').text(overview.active_users);
}

function renderPathsByRole() {
    const container = $('#pathsByRole');
    container.empty();

    // Group paths by role
    const pathsByRole = {};
    dashboardData.training_paths.forEach(path => {
        if (!pathsByRole[path.role]) {
            pathsByRole[path.role] = [];
        }
        pathsByRole[path.role].push(path);
    });

    Object.keys(pathsByRole).forEach(role => {
        const roleSection = $(`
            <div class="role-section">
                <div class="role-header">
                    <span>${role}</span>
                    <small class="text-muted">(${pathsByRole[role].length} paths)</small>
                </div>
            </div>
        `);

        pathsByRole[role].forEach(path => {
            const completionRate = path.total_enrolled > 0 ?
                (path.completed / path.total_enrolled * 100).toFixed(1) : 0;

            const statusClass = getStatusClass(completionRate);

            const pathItem = $(`
                <div class="path-item">
                    <div class="path-info">
                        <h6>${path.path_name}</h6>
                        <small class="text-muted">
                            ${path.difficulty_level || 'Not Set'} • 
                            ${path.estimated_duration_hours || 0}h • 
                            ${path.total_enrolled || 0} enrolled
                        </small>
                    </div>
                    <div class="path-stats">
                        <div class="progress-bar-container">
                            <div class="progress-bar-fill" style="width: ${completionRate}%"></div>
                        </div>
                        <small>${completionRate}% complete</small>
                    </div>
                    <div class="path-actions">
                        <button class="btn btn-sm btn-primary" onclick="viewPathDetails('${path.name}')">
                            View Details
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="editPath('${path.name}')">
                            Edit
                        </button>
                        <button class="btn btn-sm btn-success" onclick="enrollUsers('${path.name}')">
                            Enroll
                        </button>
                    </div>
                </div>
            `);

            roleSection.append(pathItem);
        });

        container.append(roleSection);
    });
}

function getStatusClass(rate) {
    if (rate >= 80) return 'status-completed';
    if (rate >= 40) return 'status-in-progress';
    return 'status-not-started';
}

function renderCharts() {
    renderEnrollmentByRoleChart();
    renderCompletionTrendsChart();
}

function renderEnrollmentByRoleChart() {
    const ctx = document.getElementById('enrollmentByRoleChart');
    if (!ctx) return;

    const data = dashboardData.paths_by_role;
    const labels = data.map(item => item.role);
    const enrollments = data.map(item => item.enrollment_count || 0);
    const completions = data.map(item => item.completed_count || 0);

    if (enrollmentChart) {
        enrollmentChart.destroy();
    }

    enrollmentChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Total Enrollments',
                    data: enrollments,
                    backgroundColor: '#007bff'
                },
                {
                    label: 'Completions',
                    data: completions,
                    backgroundColor: '#28a745'
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function renderCompletionTrendsChart() {
    const ctx = document.getElementById('completionTrendsChart');
    if (!ctx) return;

    const data = dashboardData.enrollment_trends;
    const labels = data.map(item => item.month);
    const enrollments = data.map(item => item.enrollments || 0);
    const completions = data.map(item => item.completions || 0);

    if (trendsChart) {
        trendsChart.destroy();
    }

    trendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'New Enrollments',
                    data: enrollments,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)'
                },
                {
                    label: 'Completions',
                    data: completions,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)'
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function setupEventHandlers() {
    // Create path form
    $('#createPathForm').on('submit', function (e) {
        e.preventDefault();
        createTrainingPath();
    });

    // Bulk enrollment form
    $('#bulkEnrollForm').on('submit', function (e) {
        e.preventDefault();
        bulkEnrollUsers();
    });

    // Enrollment criteria change
    $('#enrollmentCriteria').on('change', function () {
        updateCriteriaOptions();
    });
}

function loadRoles() {
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Role',
            fields: ['name'],
            filters: [['name', 'not in', ['Administrator', 'Guest', 'All']]]
        },
        callback: function (r) {
            if (r.message) {
                const roleSelect = $('#targetRole');
                roleSelect.empty();
                roleSelect.append('<option value="">Select Role</option>');
                r.message.forEach(role => {
                    roleSelect.append(`<option value="${role.name}">${role.name}</option>`);
                });
            }
        }
    });

    // Also load training paths for bulk enrollment
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Training Path',
            fields: ['name', 'path_name'],
            filters: [['is_active', '=', 1]]
        },
        callback: function (r) {
            if (r.message) {
                const pathSelect = $('#bulkTrainingPath');
                pathSelect.empty();
                pathSelect.append('<option value="">Select Training Path</option>');
                r.message.forEach(path => {
                    pathSelect.append(`<option value="${path.name}">${path.path_name}</option>`);
                });
            }
        }
    });
}

function openCreatePathModal() {
    $('#createPathModal').show();
}

function openBulkEnrollModal() {
    $('#bulkEnrollModal').show();
    updateCriteriaOptions();
}

function openRecommendationsModal() {
    frappe.call({
        method: 'universal_workshop.www.training-path-admin.get_role_recommendations',
        callback: function (r) {
            if (r.message) {
                displayRecommendations(r.message);
            }
        }
    });
}

function displayRecommendations(recommendations) {
    let html = '<h3>Training Path Recommendations</h3>';

    if (recommendations.length === 0) {
        html += '<p class="text-muted">No recommendations at this time. Your training paths are well configured!</p>';
    } else {
        recommendations.forEach(rec => {
            const priorityClass = rec.priority === 'high' ? 'danger' : rec.priority === 'medium' ? 'warning' : 'info';
            html += `
                <div class="alert alert-${priorityClass}">
                    <strong>${rec.type.replace('_', ' ').toUpperCase()}</strong><br>
                    ${rec.message}
                </div>
            `;
        });
    }

    frappe.msgprint({
        title: 'Recommendations',
        message: html,
        wide: true
    });
}

function closeModal(modalId) {
    $('#' + modalId).hide();
}

function createTrainingPath() {
    const formData = {
        path_name: $('#pathName').val(),
        path_name_ar: $('#pathNameAr').val(),
        role: $('#targetRole').val(),
        description: $('#description').val(),
        difficulty_level: $('#difficultyLevel').val(),
        mandatory_completion: $('#mandatoryCompletion').is(':checked') ? 1 : 0,
        auto_enrollment: $('#autoEnrollment').is(':checked') ? 1 : 0,
        enable_adaptive_learning: $('#enableAdaptiveLearning').is(':checked') ? 1 : 0,
        is_active: 1
    };

    frappe.call({
        method: 'universal_workshop.www.training-path-admin.create_training_path',
        args: {
            path_data: formData
        },
        callback: function (r) {
            if (r.message && r.message.status === 'success') {
                frappe.msgprint(r.message.message);
                closeModal('createPathModal');
                $('#createPathForm')[0].reset();
                loadDashboardData();
            }
        },
        error: function (err) {
            frappe.msgprint('Error creating training path: ' + err.message);
        }
    });
}

function bulkEnrollUsers() {
    const trainingPath = $('#bulkTrainingPath').val();
    const criteriaType = $('#enrollmentCriteria').val();
    const criteriaValue = getCriteriaValue();

    if (!trainingPath || !criteriaValue) {
        frappe.msgprint('Please fill all required fields');
        return;
    }

    frappe.call({
        method: 'universal_workshop.www.training-path-admin.bulk_enroll_users',
        args: {
            training_path: trainingPath,
            criteria_type: criteriaType,
            criteria_value: criteriaValue
        },
        callback: function (r) {
            if (r.message) {
                if (r.message.status === 'success') {
                    let message = r.message.message;
                    if (r.message.errors.length > 0) {
                        message += '<br><br>Errors:<br>' + r.message.errors.join('<br>');
                    }
                    frappe.msgprint(message);
                    closeModal('bulkEnrollModal');
                    $('#bulkEnrollForm')[0].reset();
                    loadDashboardData();
                } else {
                    frappe.msgprint('Error: ' + r.message.message);
                }
            }
        }
    });
}

function updateCriteriaOptions() {
    const criteriaType = $('#enrollmentCriteria').val();
    const container = $('#criteriaOptions');
    container.empty();

    if (criteriaType === 'by_role') {
        container.html(`
            <div class="form-group">
                <label for="selectedRole">Role</label>
                <select class="form-control" id="selectedRole" required>
                    <option value="">Select Role</option>
                </select>
            </div>
        `);

        // Load roles
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Role',
                fields: ['name']
            },
            callback: function (r) {
                if (r.message) {
                    const select = $('#selectedRole');
                    r.message.forEach(role => {
                        select.append(`<option value="${role.name}">${role.name}</option>`);
                    });
                }
            }
        });
    } else if (criteriaType === 'by_department') {
        container.html(`
            <div class="form-group">
                <label for="selectedDepartment">Department</label>
                <select class="form-control" id="selectedDepartment" required>
                    <option value="">Select Department</option>
                </select>
            </div>
        `);

        // Load departments
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Department',
                fields: ['name']
            },
            callback: function (r) {
                if (r.message) {
                    const select = $('#selectedDepartment');
                    r.message.forEach(dept => {
                        select.append(`<option value="${dept.name}">${dept.name}</option>`);
                    });
                }
            }
        });
    } else if (criteriaType === 'manual_select') {
        container.html(`
            <div class="form-group">
                <label for="selectedUsers">Users (comma-separated emails or usernames)</label>
                <textarea class="form-control" id="selectedUsers" rows="3" placeholder="user1@email.com, user2@email.com"></textarea>
            </div>
        `);
    }
}

function getCriteriaValue() {
    const criteriaType = $('#enrollmentCriteria').val();

    if (criteriaType === 'by_role') {
        return $('#selectedRole').val();
    } else if (criteriaType === 'by_department') {
        return $('#selectedDepartment').val();
    } else if (criteriaType === 'manual_select') {
        const users = $('#selectedUsers').val();
        return users.split(',').map(u => u.trim()).filter(u => u.length > 0);
    }

    return null;
}

function viewPathDetails(pathName) {
    frappe.call({
        method: 'universal_workshop.www.training-path-admin.get_path_enrollment_details',
        args: {
            training_path: pathName
        },
        callback: function (r) {
            if (r.message) {
                displayPathDetails(r.message);
            }
        }
    });
}

function displayPathDetails(data) {
    const path = data.path;
    const enrollments = data.enrollments;

    let enrollmentRows = '';
    enrollments.forEach(enrollment => {
        const statusClass = getStatusClass(enrollment.progress_percentage || 0);
        enrollmentRows += `
            <tr>
                <td>${enrollment.full_name || enrollment.user}</td>
                <td>${enrollment.email || ''}</td>
                <td>${enrollment.department || ''}</td>
                <td><span class="status-badge ${statusClass}">${enrollment.status}</span></td>
                <td>${(enrollment.progress_percentage || 0).toFixed(1)}%</td>
                <td>${enrollment.modules_completed || 0}/${enrollment.total_modules || 0}</td>
                <td>${enrollment.overall_competency_level || 'Not Assessed'}</td>
                <td>${(enrollment.total_time_spent_hours || 0).toFixed(1)}h</td>
                <td>${(enrollment.average_score || 0).toFixed(1)}%</td>
            </tr>
        `;
    });

    const html = `
        <h3>${path.path_name}</h3>
        <div class="row mb-3">
            <div class="col-md-6">
                <p><strong>Role:</strong> ${path.role}</p>
                <p><strong>Difficulty:</strong> ${path.difficulty_level || 'Not Set'}</p>
            </div>
            <div class="col-md-6">
                <p><strong>Duration:</strong> ${path.estimated_duration_hours || 0} hours</p>
                <p><strong>Total Enrolled:</strong> ${enrollments.length}</p>
            </div>
        </div>
        <p><strong>Description:</strong> ${path.description || 'No description provided'}</p>
        
        <h5>Enrollments</h5>
        <table class="enrollment-table">
            <thead>
                <tr>
                    <th>User</th>
                    <th>Email</th>
                    <th>Department</th>
                    <th>Status</th>
                    <th>Progress</th>
                    <th>Modules</th>
                    <th>Competency</th>
                    <th>Time Spent</th>
                    <th>Avg Score</th>
                </tr>
            </thead>
            <tbody>
                ${enrollmentRows || '<tr><td colspan="9" class="text-center">No enrollments found</td></tr>'}
            </tbody>
        </table>
    `;

    $('#pathDetailsContent').html(html);
    $('#pathDetailsModal').show();
}

function editPath(pathName) {
    frappe.set_route('Form', 'Training Path', pathName);
}

function enrollUsers(pathName) {
    $('#bulkTrainingPath').val(pathName);
    openBulkEnrollModal();
}

function exportPathsReport() {
    frappe.call({
        method: 'universal_workshop.www.training-path-admin.export_paths_report',
        callback: function (r) {
            if (r.message) {
                // The file download will be handled by Frappe automatically
                frappe.msgprint('Report exported successfully');
            }
        }
    });
}

// Close modals when clicking outside
$(window).on('click', function (event) {
    if ($(event.target).hasClass('modal')) {
        $(event.target).hide();
    }
});
