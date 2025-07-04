/**
 * Order Conversion Workflow Frontend
 * Handles UI for converting Service Estimates to Sales Orders, Work Orders, Purchase Orders
 * Supports Arabic RTL interface and real-time validation
 */

class OrderConversionWorkflowUI {
    constructor(estimate_name) {
        this.estimate_name = estimate_name;
        this.conversion_options = null;
        this.is_arabic = frappe.boot.lang === "ar";
        this.estimate_data = null;
        this.init();
    }

    async init() {
        await this.loadConversionOptions();
        this.setupEventHandlers();
    }

    async loadConversionOptions() {
        try {
            const response = await frappe.call({
                method: "universal_workshop.sales_service.order_conversion_workflow.get_conversion_options",
                args: {
                    estimate_name: this.estimate_name
                }
            });

            this.conversion_options = response.message;
            this.estimate_data = response.message.estimate_data;
            this.renderConversionButtons();
        } catch (error) {
            console.error("Failed to load conversion options:", error);
            frappe.msgprint(__("Failed to load conversion options"));
        }
    }

    renderConversionButtons() {
        const wrapper = $("[data-fieldname=\"conversion_actions\"]");
        if (!wrapper.length) return;

        wrapper.empty();

        const buttonContainer = $(`
            <div class="conversion-buttons ${this.is_arabic ? "rtl-layout" : ""}" 
                 style="margin: 15px 0; display: flex; gap: 10px; flex-wrap: wrap;">
            </div>
        `);

        // Sales Order Button
        if (this.conversion_options.can_convert_to_sales_order) {
            const soButton = this.createConversionButton(
                "sales-order",
                this.is_arabic ? "تحويل إلى أمر بيع" : "Convert to Sales Order",
                "primary",
                "fa-shopping-cart"
            );
            buttonContainer.append(soButton);
        }

        // Work Order Button
        if (this.conversion_options.can_convert_to_work_order) {
            const woButton = this.createConversionButton(
                "work-order",
                this.is_arabic ? "تحويل إلى أمر عمل" : "Convert to Work Order",
                "success",
                "fa-wrench"
            );
            buttonContainer.append(woButton);
        }

        // Purchase Order Button
        if (this.conversion_options.can_convert_to_purchase_order) {
            const poButton = this.createConversionButton(
                "purchase-order",
                this.is_arabic ? "تحويل إلى أمر شراء" : "Convert to Purchase Order",
                "warning",
                "fa-shopping-bag"
            );
            buttonContainer.append(poButton);
        }

        // Multi-Convert Button
        const multiButton = this.createConversionButton(
            "multi-convert",
            this.is_arabic ? "تحويل متعدد" : "Multi Convert",
            "info",
            "fa-random"
        );
        buttonContainer.append(multiButton);

        wrapper.append(buttonContainer);
    }

    createConversionButton(type, label, color, icon) {
        return $(`
            <button class="btn btn-${color} conversion-btn" 
                    data-conversion-type="${type}"
                    style="min-width: 140px;">
                <i class="fa ${icon}"></i>
                <span style="margin-${this.is_arabic ? "right" : "left"}: 5px;">${label}</span>
            </button>
        `);
    }

    setupEventHandlers() {
        $(document).on("click", ".conversion-btn", (e) => {
            const type = $(e.currentTarget).data("conversion-type");
            this.handleConversion(type);
        });
    }

    async handleConversion(type) {
        switch (type) {
            case "sales-order":
                await this.showSalesOrderDialog();
                break;
            case "work-order":
                await this.showWorkOrderDialog();
                break;
            case "purchase-order":
                await this.showPurchaseOrderDialog();
                break;
            case "multi-convert":
                await this.showMultiConvertDialog();
                break;
        }
    }

    async showSalesOrderDialog() {
        const dialog = new frappe.ui.Dialog({
            title: this.is_arabic ? "تحويل إلى أمر بيع" : "Convert to Sales Order",
            fields: [
                {
                    fieldtype: "Check",
                    fieldname: "include_parts",
                    label: this.is_arabic ? "تضمين القطع" : "Include Parts",
                    default: 1
                },
                {
                    fieldtype: "Check",
                    fieldname: "include_labor",
                    label: this.is_arabic ? "تضمين العمالة" : "Include Labor",
                    default: 1
                },
                {
                    fieldtype: "HTML",
                    fieldname: "preview",
                    label: this.is_arabic ? "معاينة" : "Preview"
                }
            ],
            primary_action_label: this.is_arabic ? "تحويل" : "Convert",
            primary_action: async (values) => {
                try {
                    frappe.show_progress(
                        this.is_arabic ? "جاري التحويل..." : "Converting...",
                        50
                    );

                    const response = await frappe.call({
                        method: "universal_workshop.sales_service.order_conversion_workflow.convert_estimate_to_sales_order",
                        args: {
                            estimate_name: this.estimate_name,
                            include_parts: values.include_parts,
                            include_labor: values.include_labor
                        }
                    });

                    frappe.hide_progress();

                    if (response.message.status === "success") {
                        const message = this.is_arabic ?
                            response.message.message_ar :
                            response.message.message;

                        frappe.show_alert({
                            message: message,
                            indicator: "green"
                        });

                        // Navigate to Sales Order
                        setTimeout(() => {
                            frappe.set_route("Form", "Sales Order", response.message.sales_order);
                        }, 1500);

                        dialog.hide();
                        this.refreshEstimateForm();
                    } else {
                        const error_msg = this.is_arabic ?
                            response.message.message_ar :
                            response.message.message;
                        frappe.msgprint(error_msg);
                    }

                } catch (error) {
                    frappe.hide_progress();
                    console.error("Conversion error:", error);
                    frappe.msgprint(
                        this.is_arabic ?
                            "فشل في التحويل" :
                            "Conversion failed"
                    );
                }
            }
        });

        // Update preview when checkboxes change
        dialog.get_field("include_parts").$input.on("change", () => {
            this.updateSalesOrderPreview(dialog);
        });

        dialog.get_field("include_labor").$input.on("change", () => {
            this.updateSalesOrderPreview(dialog);
        });

        dialog.show();
        this.updateSalesOrderPreview(dialog);
    }

    updateSalesOrderPreview(dialog) {
        const values = dialog.get_values();
        let items = [];

        if (values.include_parts && this.conversion_options.has_parts) {
            items.push(this.is_arabic ? "القطع والمواد" : "Parts & Materials");
        }

        if (values.include_labor && this.conversion_options.has_labor) {
            items.push(this.is_arabic ? "العمالة والخدمات" : "Labor & Services");
        }

        const previewHtml = `
            <div class="conversion-preview ${this.is_arabic ? "rtl-layout" : ""}">
                <h6>${this.is_arabic ? "سيتم تضمين:" : "Will include:"}</h6>
                <ul>
                    ${items.map(item => `<li>${item}</li>`).join("")}
                </ul>
                ${items.length === 0 ?
                `<p class="text-muted">${this.is_arabic ? "لم يتم اختيار عناصر" : "No items selected"}</p>` :
                ""
            }
            </div>
        `;

        dialog.get_field("preview").$wrapper.html(previewHtml);
    }

    async showWorkOrderDialog() {
        const dialog = new frappe.ui.Dialog({
            title: this.is_arabic ? "تحويل إلى أمر عمل" : "Convert to Work Order",
            fields: [
                {
                    fieldtype: "Link",
                    fieldname: "manufacturing_item",
                    label: this.is_arabic ? "صنف التصنيع" : "Manufacturing Item",
                    options: "Item",
                    description: this.is_arabic ?
                        "اختر الصنف المراد تصنيعه أو تركيبه" :
                        "Select the item to be manufactured or assembled"
                },
                {
                    fieldtype: "HTML",
                    fieldname: "work_info",
                    label: this.is_arabic ? "معلومات العمل" : "Work Information"
                }
            ],
            primary_action_label: this.is_arabic ? "تحويل" : "Convert",
            primary_action: async (values) => {
                try {
                    frappe.show_progress(
                        this.is_arabic ? "جاري التحويل..." : "Converting...",
                        50
                    );

                    const response = await frappe.call({
                        method: "universal_workshop.sales_service.order_conversion_workflow.convert_estimate_to_work_order",
                        args: {
                            estimate_name: this.estimate_name,
                            manufacturing_item: values.manufacturing_item
                        }
                    });

                    frappe.hide_progress();

                    if (response.message.status === "success") {
                        const message = this.is_arabic ?
                            response.message.message_ar :
                            response.message.message;

                        frappe.show_alert({
                            message: message,
                            indicator: "green"
                        });

                        // Navigate to Work Order
                        setTimeout(() => {
                            frappe.set_route("Form", "Work Order", response.message.work_order);
                        }, 1500);

                        dialog.hide();
                        this.refreshEstimateForm();
                    } else {
                        const error_msg = this.is_arabic ?
                            response.message.message_ar :
                            response.message.message;
                        frappe.msgprint(error_msg);
                    }

                } catch (error) {
                    frappe.hide_progress();
                    console.error("Conversion error:", error);
                    frappe.msgprint(
                        this.is_arabic ?
                            "فشل في التحويل" :
                            "Conversion failed"
                    );
                }
            }
        });

        // Show work information
        const workInfoHtml = `
            <div class="work-order-info ${this.is_arabic ? "rtl-layout" : ""}">
                <div class="row">
                    <div class="col-md-6">
                        <strong>${this.is_arabic ? "نوع الخدمة:" : "Service Type:"}</strong>
                        <span>${this.estimate_data?.service_type || "N/A"}</span>
                    </div>
                    <div class="col-md-6">
                        <strong>${this.is_arabic ? "الساعات المقدرة:" : "Estimated Hours:"}</strong>
                        <span>${this.estimate_data?.estimated_hours || "N/A"}</span>
                    </div>
                </div>
            </div>
        `;

        dialog.get_field("work_info").$wrapper.html(workInfoHtml);
        dialog.show();
    }

    async showPurchaseOrderDialog() {
        const suppliers = this.conversion_options.available_suppliers || [];

        const dialog = new frappe.ui.Dialog({
            title: this.is_arabic ? "تحويل إلى أمر شراء" : "Convert to Purchase Order",
            fields: [
                {
                    fieldtype: "Select",
                    fieldname: "supplier",
                    label: this.is_arabic ? "المورد" : "Supplier",
                    options: [""].concat(suppliers),
                    description: this.is_arabic ?
                        "اختر المورد أو اتركه فارغاً للمورد الافتراضي" :
                        "Select supplier or leave empty for default"
                },
                {
                    fieldtype: "HTML",
                    fieldname: "parts_preview",
                    label: this.is_arabic ? "القطع المطلوبة" : "Required Parts"
                }
            ],
            primary_action_label: this.is_arabic ? "تحويل" : "Convert",
            primary_action: async (values) => {
                try {
                    frappe.show_progress(
                        this.is_arabic ? "جاري التحويل..." : "Converting...",
                        50
                    );

                    const response = await frappe.call({
                        method: "universal_workshop.sales_service.order_conversion_workflow.convert_estimate_to_purchase_order",
                        args: {
                            estimate_name: this.estimate_name,
                            supplier: values.supplier,
                            parts_only: true
                        }
                    });

                    frappe.hide_progress();

                    if (response.message.status === "success") {
                        const message = this.is_arabic ?
                            response.message.message_ar :
                            response.message.message;

                        frappe.show_alert({
                            message: message,
                            indicator: "green"
                        });

                        // Navigate to Purchase Order
                        setTimeout(() => {
                            frappe.set_route("Form", "Purchase Order", response.message.purchase_order);
                        }, 1500);

                        dialog.hide();
                        this.refreshEstimateForm();
                    } else {
                        const error_msg = this.is_arabic ?
                            response.message.message_ar :
                            response.message.message;
                        frappe.msgprint(error_msg);
                    }

                } catch (error) {
                    frappe.hide_progress();
                    console.error("Conversion error:", error);
                    frappe.msgprint(
                        this.is_arabic ?
                            "فشل في التحويل" :
                            "Conversion failed"
                    );
                }
            }
        });

        // Show parts requiring procurement
        const partsHtml = this.renderPartsPreview();
        dialog.get_field("parts_preview").$wrapper.html(partsHtml);

        dialog.show();
    }

    renderPartsPreview() {
        const parts = this.conversion_options.parts_requiring_procurement || [];

        if (parts.length === 0) {
            return `<p class="text-muted">${this.is_arabic ? "لا توجد قطع تحتاج للشراء" : "No parts require procurement"}</p>`;
        }

        let html = `
            <div class="parts-preview ${this.is_arabic ? "rtl-layout" : ""}">
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>${this.is_arabic ? "القطعة" : "Part"}</th>
                            <th>${this.is_arabic ? "الكمية" : "Qty"}</th>
                            <th>${this.is_arabic ? "السعر" : "Rate"}</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        parts.forEach(part => {
            const partName = this.is_arabic && part.item_name_ar ?
                part.item_name_ar :
                part.item_name;

            html += `
                <tr>
                    <td>${partName}</td>
                    <td>${part.qty}</td>
                    <td>${frappe.format(part.rate, { fieldtype: "Currency" })}</td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        return html;
    }

    async showMultiConvertDialog() {
        const dialog = new frappe.ui.Dialog({
            title: this.is_arabic ? "تحويل متعدد" : "Multi Conversion",
            size: "large",
            fields: [
                {
                    fieldtype: "Section Break",
                    label: this.is_arabic ? "خيارات التحويل" : "Conversion Options"
                },
                {
                    fieldtype: "Check",
                    fieldname: "create_sales_order",
                    label: this.is_arabic ? "إنشاء أمر بيع" : "Create Sales Order",
                    default: 1
                },
                {
                    fieldtype: "Check",
                    fieldname: "create_work_order",
                    label: this.is_arabic ? "إنشاء أمر عمل" : "Create Work Order",
                    depends_on: "eval:doc.create_sales_order"
                },
                {
                    fieldtype: "Check",
                    fieldname: "create_purchase_order",
                    label: this.is_arabic ? "إنشاء أمر شراء" : "Create Purchase Order"
                },
                {
                    fieldtype: "Column Break"
                },
                {
                    fieldtype: "HTML",
                    fieldname: "conversion_summary",
                    label: this.is_arabic ? "ملخص التحويل" : "Conversion Summary"
                }
            ],
            primary_action_label: this.is_arabic ? "تحويل الكل" : "Convert All",
            primary_action: async (values) => {
                try {
                    frappe.show_progress(
                        this.is_arabic ? "جاري التحويل المتعدد..." : "Multi-converting...",
                        25
                    );

                    const response = await frappe.call({
                        method: "universal_workshop.sales_service.order_conversion_workflow.convert_to_multiple_orders",
                        args: {
                            estimate_name: this.estimate_name,
                            conversion_config: values
                        }
                    });

                    frappe.hide_progress();

                    if (response.message.status === "success") {
                        const message = this.is_arabic ?
                            "تم إنجاز التحويل المتعدد بنجاح" :
                            "Multi-conversion completed successfully";

                        frappe.show_alert({
                            message: message,
                            indicator: "green"
                        });

                        dialog.hide();
                        this.refreshEstimateForm();
                    } else {
                        frappe.msgprint(response.message.message);
                    }

                } catch (error) {
                    frappe.hide_progress();
                    console.error("Multi-conversion error:", error);
                    frappe.msgprint(
                        this.is_arabic ?
                            "فشل في التحويل المتعدد" :
                            "Multi-conversion failed"
                    );
                }
            }
        });

        dialog.show();
    }

    refreshEstimateForm() {
        if (cur_frm && cur_frm.doctype === "Service Estimate" && cur_frm.doc.name === this.estimate_name) {
            cur_frm.reload_doc();
        }
    }
}

// Global function to initialize conversion workflow
window.initOrderConversionWorkflow = function (estimate_name) {
    return new OrderConversionWorkflowUI(estimate_name);
};

// Auto-initialize for Service Estimate forms
frappe.ui.form.on("Service Estimate", {
    refresh: function (frm) {
        if (frm.doc.name && frm.doc.status === "Approved" && !frm.doc.converted_to_service_order) {
            // Initialize conversion workflow
            frm.conversion_workflow = new OrderConversionWorkflowUI(frm.doc.name);

            // Add conversion section to form
            if (!frm.fields_dict.conversion_actions) {
                frm.add_custom_button(__("Order Conversions"), function () {
                    // This will be handled by the conversion buttons
                }).addClass("btn-primary");
            }
        }
    }
});
