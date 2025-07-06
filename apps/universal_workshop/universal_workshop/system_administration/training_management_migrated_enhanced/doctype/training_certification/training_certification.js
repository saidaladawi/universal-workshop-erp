frappe.ui.form.on('Training Certification', {
	refresh: function (frm) {
		// Add custom buttons
		add_custom_buttons(frm);

		// Add certificate preview
		add_certificate_preview(frm);

		// Add verification section
		add_verification_section(frm);

		// Setup expiration alerts
		setup_expiration_alerts(frm);
	},

	onload: function (frm) {
		// Auto-generate certificate if not exists
		if (!frm.is_new() && !frm.doc.certificate_file) {
			auto_generate_certificate(frm);
		}
	}
});

function add_custom_buttons(frm) {
	if (!frm.is_new()) {
		// Download Certificate button
		frm.add_custom_button(__('Download Certificate'), function () {
			download_certificate(frm);
		}, __('Actions'));

		// Regenerate Certificate button (if user has permissions)
		if (frappe.user.has_role(['System Manager', 'Training Manager'])) {
			frm.add_custom_button(__('Regenerate Certificate'), function () {
				regenerate_certificate(frm);
			}, __('Actions'));
		}

		// Verify Certificate button
		frm.add_custom_button(__('Verify Certificate'), function () {
			verify_certificate_dialog(frm);
		}, __('Actions'));

		// Send Certificate button
		frm.add_custom_button(__('Send to User'), function () {
			send_certificate_email(frm);
		}, __('Actions'));
	}
}

function add_certificate_preview(frm) {
	if (frm.doc.certificate_file) {
		const preview_html = `
            <div class="certificate-preview" style="margin: 15px 0; padding: 20px; background: #f8f9fa; border-radius: 10px; border: 2px solid #ffd700;">
                <div style="text-align: center;">
                    <h4 style="color: #667eea; margin-bottom: 15px;">
                        <i class="fa fa-certificate" style="color: #ffd700;"></i> 
                        ${__('Certificate Preview')}
                    </h4>
                    <div style="background: white; padding: 20px; border-radius: 5px; margin: 10px 0;">
                        <h5>${frm.doc.module_title}</h5>
                        <p><strong>${__('Certificate Number')}:</strong> ${frm.doc.certificate_number}</p>
                        <p><strong>${__('Competency Level')}:</strong> ${__(frm.doc.competency_level)}</p>
                        <p><strong>${__('Score')}:</strong> ${frm.doc.quiz_score}%</p>
                        <p><strong>${__('Valid Until')}:</strong> ${frm.doc.valid_until}</p>
                    </div>
                    <button class="btn btn-primary btn-sm" onclick="window.open('${frm.doc.certificate_file}', '_blank')">
                        <i class="fa fa-external-link"></i> ${__('View Full Certificate')}
                    </button>
                </div>
            </div>
        `;

		frm.get_field('certificate_file').$wrapper.after(preview_html);
	}
}

function add_verification_section(frm) {
	const verification_html = `
        <div class="certificate-verification" style="margin: 15px 0; padding: 15px; background: #e8f5e8; border-radius: 5px; border-left: 4px solid #28a745;">
            <h6 style="color: #28a745; margin-bottom: 10px;">
                <i class="fa fa-shield"></i> ${__('Certificate Verification')}
            </h6>
            <div class="row">
                <div class="col-md-6">
                    <p><strong>${__('Verification Code')}:</strong></p>
                    <code style="background: white; padding: 5px 10px; border-radius: 3px; font-family: monospace;">
                        ${frm.doc.verification_code || __('Not Generated')}
                    </code>
                </div>
                <div class="col-md-6">
                    <p><strong>${__('Digital Signature')}:</strong></p>
                    <span class="text-success">
                        <i class="fa fa-check-circle"></i> ${__('Digitally Signed')}
                    </span>
                </div>
            </div>
            <div style="margin-top: 10px;">
                <small class="text-muted">
                    ${__('Use the verification code to authenticate this certificate on our verification portal.')}
                </small>
            </div>
        </div>
    `;

	frm.get_field('verification_code').$wrapper.after(verification_html);
}

function setup_expiration_alerts(frm) {
	if (frm.doc.valid_until) {
		const expiry_date = new Date(frm.doc.valid_until);
		const today = new Date();
		const days_until_expiry = Math.ceil((expiry_date - today) / (1000 * 60 * 60 * 24));

		let alert_html = '';
		let alert_class = '';

		if (days_until_expiry < 0) {
			alert_html = `<i class="fa fa-exclamation-triangle"></i> ${__('Certificate has expired {0} days ago', [Math.abs(days_until_expiry)])}`;
			alert_class = 'alert-danger';
		} else if (days_until_expiry <= 30) {
			alert_html = `<i class="fa fa-clock-o"></i> ${__('Certificate expires in {0} days', [days_until_expiry])}`;
			alert_class = 'alert-warning';
		} else if (days_until_expiry <= 60) {
			alert_html = `<i class="fa fa-info-circle"></i> ${__('Certificate expires in {0} days', [days_until_expiry])}`;
			alert_class = 'alert-info';
		}

		if (alert_html) {
			const expiry_alert = `
                <div class="alert ${alert_class}" style="margin: 15px 0;">
                    ${alert_html}
                </div>
            `;

			frm.get_field('valid_until').$wrapper.after(expiry_alert);
		}
	}
}

function download_certificate(frm) {
	if (frm.doc.certificate_file) {
		// Create a temporary link and click it
		const link = document.createElement('a');
		link.href = frm.doc.certificate_file;
		link.download = `Certificate_${frm.doc.certificate_number}.pdf`;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);

		frappe.show_alert({
			message: __('Certificate download started'),
			indicator: 'green'
		});
	} else {
		frappe.msgprint(__('Certificate file not found. Please regenerate the certificate.'));
	}
}

function regenerate_certificate(frm) {
	frappe.confirm(
		__('Are you sure you want to regenerate this certificate? The current certificate file will be replaced.'),
		function () {
			frappe.call({
				method: 'universal_workshop.training_management.doctype.training_certification.training_certification.regenerate_certificate',
				args: {
					certification_name: frm.doc.name
				},
				callback: function (r) {
					if (r.message && r.message.status === 'success') {
						frm.reload_doc();
						frappe.show_alert({
							message: __('Certificate regenerated successfully'),
							indicator: 'green'
						});
					}
				}
			});
		}
	);
}

function verify_certificate_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __('Verify Certificate'),
		fields: [
			{
				fieldtype: 'Data',
				fieldname: 'verification_code',
				label: __('Verification Code'),
				reqd: 1,
				default: frm.doc.verification_code
			},
			{
				fieldtype: 'Data',
				fieldname: 'certificate_number',
				label: __('Certificate Number'),
				reqd: 1,
				default: frm.doc.certificate_number
			}
		],
		primary_action_label: __('Verify'),
		primary_action: function (values) {
			frappe.call({
				method: 'universal_workshop.training_management.doctype.training_certification.training_certification.verify_certificate',
				args: {
					verification_code: values.verification_code,
					certificate_number: values.certificate_number
				},
				callback: function (r) {
					if (r.message) {
						if (r.message.valid) {
							frappe.msgprint({
								title: __('Certificate Valid'),
								message: __('This certificate is authentic and valid.') + '<br><br>' +
									'<strong>' + __('Details') + ':</strong><br>' +
									__('Module') + ': ' + r.message.module_title + '<br>' +
									__('User') + ': ' + r.message.user + '<br>' +
									__('Issued On') + ': ' + r.message.issued_on + '<br>' +
									__('Valid Until') + ': ' + r.message.valid_until,
								indicator: 'green'
							});
						} else {
							frappe.msgprint({
								title: __('Certificate Invalid'),
								message: __('This certificate could not be verified. It may be forged or expired.'),
								indicator: 'red'
							});
						}
					}
				}
			});
			dialog.hide();
		}
	});

	dialog.show();
}

function send_certificate_email(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __('Send Certificate'),
		fields: [
			{
				fieldtype: 'Data',
				fieldname: 'recipient_email',
				label: __('Recipient Email'),
				reqd: 1,
				default: frm.doc.user_email
			},
			{
				fieldtype: 'Small Text',
				fieldname: 'message',
				label: __('Additional Message'),
				default: __('Congratulations on completing your training! Please find your certificate attached.')
			}
		],
		primary_action_label: __('Send'),
		primary_action: function (values) {
			frappe.call({
				method: 'universal_workshop.training_management.doctype.training_certification.training_certification.send_certificate_email',
				args: {
					certification_name: frm.doc.name,
					recipient_email: values.recipient_email,
					message: values.message
				},
				callback: function (r) {
					if (r.message && r.message.status === 'success') {
						frappe.show_alert({
							message: __('Certificate sent successfully'),
							indicator: 'green'
						});
					}
				}
			});
			dialog.hide();
		}
	});

	dialog.show();
}

function auto_generate_certificate(frm) {
	// Only auto-generate if certificate doesn't exist and user has proper permissions
	if (frappe.user.has_role(['System Manager', 'Training Manager']) && !frm.doc.certificate_file) {
		frappe.call({
			method: 'generate_certificate_pdf',
			doc: frm.doc,
			callback: function (r) {
				if (r.message && r.message.status === 'success') {
					frm.reload_doc();
				}
			}
		});
	}
}
