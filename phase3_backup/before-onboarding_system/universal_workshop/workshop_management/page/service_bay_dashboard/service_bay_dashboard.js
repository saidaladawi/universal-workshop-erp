// Service Bay Dashboard JavaScript
// Copyright (c) 2025, Said Al-Adawi and contributors

frappe.pages['service-bay-dashboard'].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Service Bay Dashboard',
        single_column: true
    });

    // Add refresh button
    page.add_menu_item(__('Refresh Dashboard'), function () {
        refreshDashboard();
    });

    // Add capacity planning button  
    page.add_menu_item(__('Capacity Planning'), function () {
        showCapacityPlanning();
    });

    // Initialize dashboard
    initializeDashboard(page);
};

function initializeDashboard(page) {
    // Load Chart.js if not already loaded
    if (typeof Chart === 'undefined') {
        frappe.require('/assets/frappe/js/lib/chart.min.js', function () {
            setupDashboard(page);
        });
    } else {
        setupDashboard(page);
    }
}

function setupDashboard(page) {
    // Get dashboard container
    const container = page.main;

    // Add dashboard HTML
    container.html(`
		<div class="service-bay-dashboard">
			<!-- Summary Cards -->
			<div class="row dashboard-summary">
				<div class="col-md-2">
					<div class="dashboard-card">
						<div class="card-content">
							<h3 id="total-bays">-</h3>
							<p>Total Bays<br><small>مجموع الأقسام</small></p>
						</div>
					</div>
				</div>
				<div class="col-md-2">
					<div class="dashboard-card">
						<div class="card-content">
							<h3 id="occupied-bays">-</h3>
							<p>Occupied<br><small>مشغولة</small></p>
						</div>
					</div>
				</div>
				<div class="col-md-2">
					<div class="dashboard-card">
						<div class="card-content">
							<h3 id="utilization-rate">-</h3>
							<p>Utilization<br><small>نسبة الاستخدام</small></p>
						</div>
					</div>
				</div>
				<div class="col-md-2">
					<div class="dashboard-card">
						<div class="card-content">
							<h3 id="today-orders">-</h3>
							<p>Today's Orders<br><small>طلبات اليوم</small></p>
						</div>
					</div>
				</div>
				<div class="col-md-2">
					<div class="dashboard-card">
						<div class="card-content">
							<h3 id="completed-orders">-</h3>
							<p>Completed<br><small>مكتملة</small></p>
						</div>
					</div>
				</div>
				<div class="col-md-2">
					<div class="dashboard-card">
						<div class="card-content">
							<h3 id="pending-qc">-</h3>
							<p>Pending QC<br><small>فحص الجودة</small></p>
						</div>
					</div>
				</div>
			</div>

			<!-- Bay Status Grid -->
			<div class="row mt-4">
				<div class="col-12">
					<div class="frappe-card">
						<div class="frappe-card-head">
							<h5>Real-time Bay Status - الحالة المباشرة للأقسام</h5>
						</div>
						<div class="frappe-card-body">
							<div id="bay-status-grid" class="bay-grid">
								<!-- Bay status cards will be populated -->
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Charts and Alerts -->
			<div class="row mt-4">
				<div class="col-md-8">
					<div class="frappe-card">
						<div class="frappe-card-head">
							<h5>Weekly Performance - الأداء الأسبوعي</h5>
						</div>
						<div class="frappe-card-body">
							<canvas id="performance-chart" width="400" height="200"></canvas>
						</div>
					</div>
				</div>
				<div class="col-md-4">
					<div class="frappe-card">
						<div class="frappe-card-head">
							<h5>Alerts - التنبيهات</h5>
						</div>
						<div class="frappe-card-body">
							<div id="alerts-container">
								<!-- Alerts will be populated -->
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Bay Details Table -->
			<div class="row mt-4">
				<div class="col-12">
					<div class="frappe-card">
						<div class="frappe-card-head">
							<h5>Bay Details - تفاصيل الأقسام</h5>
						</div>
						<div class="frappe-card-body">
							<div id="bay-details-table">
								<!-- Table will be populated -->
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	`);

    // Add custom styles
    addDashboardStyles();

    // Load initial data
    loadDashboardData();

    // Set up auto-refresh
    setInterval(loadDashboardData, 30000); // Refresh every 30 seconds
}

function addDashboardStyles() {
    const style = document.createElement('style');
    style.textContent = `
		.service-bay-dashboard {
			padding: 15px;
		}

		.dashboard-card {
			background: #fff;
			border: 1px solid #d1d8dd;
			border-radius: 6px;
			margin-bottom: 15px;
			border-left: 4px solid #5e64ff;
		}

		.dashboard-card .card-content {
			padding: 15px;
			text-align: center;
		}

		.dashboard-card h3 {
			color: #5e64ff;
			margin-bottom: 5px;
			font-size: 24px;
			font-weight: 600;
		}

		.dashboard-card p {
			margin: 0;
			color: #8d99a6;
			font-size: 12px;
			line-height: 1.4;
		}

		.bay-grid {
			display: grid;
			grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
			gap: 15px;
		}

		.bay-card {
			border: 2px solid #e9ecef;
			border-radius: 8px;
			padding: 15px;
			text-align: center;
			transition: all 0.3s;
			background: #fff;
		}

		.bay-card.available {
			border-color: #28a745;
			background-color: #f8fff9;
		}

		.bay-card.occupied {
			border-color: #ffc107;
			background-color: #fffef5;
		}

		.bay-card.full {
			border-color: #dc3545;
			background-color: #fff5f5;
		}

		.bay-card h6 {
			margin-bottom: 8px;
			font-weight: 600;
		}

		.alert-item {
			border-left: 4px solid;
			padding: 10px;
			margin-bottom: 10px;
			border-radius: 4px;
			font-size: 12px;
		}

		.alert-item.warning {
			border-left-color: #ffc107;
			background-color: #fff3cd;
		}

		.alert-item.error {
			border-left-color: #dc3545;
			background-color: #f8d7da;
		}

		.alert-item.info {
			border-left-color: #17a2b8;
			background-color: #d1ecf1;
		}

		.dashboard-summary {
			margin-bottom: 20px;
		}

		.frappe-card {
			background: #fff;
			border: 1px solid #d1d8dd;
			border-radius: 6px;
			margin-bottom: 20px;
		}

		.frappe-card-head {
			padding: 15px 20px;
			border-bottom: 1px solid #d1d8dd;
			background: #f5f7fa;
		}

		.frappe-card-head h5 {
			margin: 0;
			font-size: 14px;
			font-weight: 600;
		}

		.frappe-card-body {
			padding: 20px;
		}
	`;
    document.head.appendChild(style);
}

function loadDashboardData() {
    frappe.call({
        method: 'universal_workshop.workshop_management.utils.bay_monitoring.get_service_bay_dashboard',
        callback: function (r) {
            if (r.message) {
                updateDashboard(r.message);
            }
        },
        error: function () {
            frappe.msgprint(__('Failed to load dashboard data'));
        }
    });
}

function updateDashboard(data) {
    // Update summary cards
    updateSummaryCards(data.summary);

    // Update bay status
    updateBayStatus();

    // Update alerts
    updateAlerts();

    // Update bay details table
    updateBayDetailsTable(data.bays);

    // Update charts
    updatePerformanceChart();
}

function updateSummaryCards(summary) {
    document.getElementById('total-bays').textContent = summary.total_bays || 0;
    document.getElementById('occupied-bays').textContent = summary.current_occupied || 0;
    document.getElementById('utilization-rate').textContent = (summary.overall_utilization || 0).toFixed(1) + '%';
    document.getElementById('today-orders').textContent = summary.today_orders || 0;
    document.getElementById('completed-orders').textContent = summary.completed_today || 0;
    document.getElementById('pending-qc').textContent = summary.pending_qc || 0;
}

function updateBayStatus() {
    frappe.call({
        method: 'universal_workshop.workshop_management.utils.bay_monitoring.get_real_time_bay_status',
        callback: function (r) {
            if (r.message) {
                renderBayStatus(r.message);
            }
        }
    });
}

function renderBayStatus(bays) {
    const container = document.getElementById('bay-status-grid');
    let html = '';

    bays.forEach(bay => {
        const statusClass = bay.status.toLowerCase();
        const statusBadge = statusClass === 'available' ? 'success' :
            statusClass === 'occupied' ? 'warning' : 'danger';

        html += `
			<div class="bay-card ${statusClass}" onclick="viewBayDetails('${bay.bay_id}')">
				<h6>${bay.bay_code}</h6>
				<p style="margin-bottom: 8px;">${bay.bay_name}</p>
				<span class="badge badge-${statusBadge}">
					${bay.status}
				</span>
				<p style="margin-top: 8px; margin-bottom: 0;">
					<small>${bay.current_occupancy}/${bay.max_vehicles} vehicles</small>
				</p>
				<p style="margin: 4px 0 0 0;">
					<small>Utilization: ${(bay.utilization_rate || 0).toFixed(1)}%</small>
				</p>
			</div>
		`;
    });

    container.innerHTML = html;
}

function updateAlerts() {
    frappe.call({
        method: 'universal_workshop.workshop_management.utils.bay_monitoring.get_capacity_alerts',
        callback: function (r) {
            if (r.message) {
                renderAlerts(r.message);
            }
        }
    });
}

function renderAlerts(alerts) {
    const container = document.getElementById('alerts-container');
    let html = '';

    if (alerts.length === 0) {
        html = '<p style="color: #8d99a6; text-align: center; margin: 20px 0;">No alerts at this time</p>';
    } else {
        alerts.forEach(alert => {
            html += `
				<div class="alert-item ${alert.severity}">
					<strong>${alert.title}</strong><br>
					<span>${alert.message}</span>
					<br><small style="color: #6c757d;">${alert.recommendation}</small>
				</div>
			`;
        });
    }

    container.innerHTML = html;
}

function updateBayDetailsTable(bays) {
    const container = document.getElementById('bay-details-table');

    let html = `
		<table class="table table-striped">
			<thead>
				<tr>
					<th>Bay Code<br><small>رمز القسم</small></th>
					<th>Bay Name<br><small>اسم القسم</small></th>
					<th>Type<br><small>النوع</small></th>
					<th>Occupancy<br><small>الإشغال</small></th>
					<th>Utilization<br><small>الاستخدام</small></th>
					<th>Avg Time<br><small>متوسط الوقت</small></th>
					<th>Actions<br><small>الإجراءات</small></th>
				</tr>
			</thead>
			<tbody>
	`;

    bays.forEach(bay => {
        const utilizationColor = bay.utilization_rate > 90 ? 'danger' :
            bay.utilization_rate > 70 ? 'warning' : 'success';
        const occupancyColor = bay.current_occupancy >= bay.max_vehicles ? 'danger' : 'success';

        html += `
			<tr>
				<td><strong>${bay.bay_code}</strong></td>
				<td>
					${bay.bay_name}
					${bay.bay_name_ar ? `<br><small style="color: #8d99a6;">${bay.bay_name_ar}</small>` : ''}
				</td>
				<td>
					<span class="badge badge-secondary">${bay.bay_type}</span>
				</td>
				<td>
					<span class="badge badge-${occupancyColor}">
						${bay.current_occupancy}/${bay.max_vehicles}
					</span>
				</td>
				<td>
					<div class="progress" style="height: 20px;">
						<div class="progress-bar bg-${utilizationColor}" 
							 style="width: ${bay.utilization_rate || 0}%">
							${(bay.utilization_rate || 0).toFixed(1)}%
						</div>
					</div>
				</td>
				<td>${(bay.average_service_time || 0).toFixed(1)}h</td>
				<td>
					<button class="btn btn-sm btn-primary" onclick="viewBaySchedule('${bay.name}')">
						<i class="fa fa-calendar"></i> Schedule
					</button>
				</td>
			</tr>
		`;
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

function updatePerformanceChart() {
    frappe.call({
        method: 'universal_workshop.workshop_management.utils.bay_monitoring.get_weekly_performance',
        callback: function (r) {
            if (r.message) {
                renderPerformanceChart(r.message);
            }
        }
    });
}

function renderPerformanceChart(data) {
    const ctx = document.getElementById('performance-chart').getContext('2d');

    // Destroy existing chart if it exists
    if (window.performanceChart) {
        window.performanceChart.destroy();
    }

    window.performanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.day_name),
            datasets: [{
                label: 'Total Orders',
                data: data.map(d => d.total_orders),
                borderColor: '#5e64ff',
                backgroundColor: 'rgba(94, 100, 255, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: 'Completed Orders',
                data: data.map(d => d.completed_orders),
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function viewBayDetails(bayId) {
    frappe.set_route('Form', 'Service Bay', bayId);
}

function viewBaySchedule(bayId) {
    // Create and show modal dialog
    const d = new frappe.ui.Dialog({
        title: __('Bay Schedule'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'schedule_content'
            }
        ],
        size: 'large'
    });

    // Load schedule data
    frappe.call({
        method: 'universal_workshop.workshop_management.doctype.service_bay.service_bay.get_bay_schedule',
        args: { bay_id: bayId },
        callback: function (r) {
            if (r.message) {
                showBayScheduleContent(d, r.message);
            }
        }
    });

    d.show();
}

function showBayScheduleContent(dialog, scheduleData) {
    let html = `
		<div style="padding: 15px;">
			<h6>${scheduleData.bay_info.bay_name} (${scheduleData.bay_info.bay_code})</h6>
			<p><strong>Operating Hours:</strong> ${scheduleData.bay_info.operating_hours}</p>
			<p><strong>Current Utilization:</strong> ${scheduleData.utilization_rate}%</p>
			
			<h6 style="margin-top: 20px;">Scheduled Orders:</h6>
	`;

    if (scheduleData.scheduled_orders.length === 0) {
        html += '<p style="color: #8d99a6;">No orders scheduled</p>';
    } else {
        html += '<table class="table table-sm table-striped">';
        html += '<thead><tr><th>Order</th><th>Customer</th><th>Time</th><th>Status</th></tr></thead><tbody>';

        scheduleData.scheduled_orders.forEach(order => {
            html += `
				<tr>
					<td><a href="/app/service-order/${order.name}">${order.name}</a></td>
					<td>${order.customer}</td>
					<td>${order.service_start_time || 'TBD'}</td>
					<td><span class="badge badge-primary">${order.status}</span></td>
				</tr>
			`;
        });

        html += '</tbody></table>';
    }

    html += '<h6 style="margin-top: 20px;">Available Slots:</h6>';
    if (scheduleData.available_slots.length === 0) {
        html += '<p style="color: #8d99a6;">No available slots</p>';
    } else {
        scheduleData.available_slots.forEach(slot => {
            html += `<span class="badge badge-success" style="margin-right: 5px; margin-bottom: 5px;">${slot.start_time} - ${slot.end_time}</span>`;
        });
    }

    html += '</div>';

    dialog.fields_dict.schedule_content.$wrapper.html(html);
}

function refreshDashboard() {
    loadDashboardData();
    frappe.show_alert({
        message: __('Dashboard refreshed'),
        indicator: 'green'
    });
}

function showCapacityPlanning() {
    frappe.set_route('query-report', 'Service Bay Capacity Planning');
} 