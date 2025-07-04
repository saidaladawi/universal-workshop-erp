/**
 * Contextual Help System Integration Tests
 * Tests for the Universal Workshop contextual help functionality
 */

// Test the contextual help system initialization
function testContextualHelpInitialization() {
    console.log('Testing Contextual Help Initialization...');

    // Check if the global help system is available
    if (typeof window.contextualHelp !== 'undefined') {
        console.log('✓ Contextual Help System is available');
        return true;
    } else {
        console.log('✗ Contextual Help System not found');
        return false;
    }
}

// Test help content loading
function testHelpContentLoading() {
    console.log('Testing Help Content Loading...');

    if (window.contextualHelp && window.contextualHelp.helpContent) {
        const contentCount = Object.keys(window.contextualHelp.helpContent).length;
        console.log(`✓ Help content loaded: ${contentCount} items`);
        return true;
    } else {
        console.log('✗ Help content not loaded');
        return false;
    }
}

// Test API endpoints
function testAPIEndpoints() {
    console.log('Testing API Endpoints...');

    // Test context detection
    frappe.call({
        method: 'universal_workshop.training_management.api.contextual_help.get_contextual_help',
        args: {
            route: '/app/training-module'
        },
        callback: function (r) {
            if (r.message) {
                console.log('✓ Context detection API working');
                console.log(`  Found ${r.message.content.length} contextual items`);
            } else {
                console.log('✗ Context detection API failed');
            }
        }
    });

    // Test search
    frappe.call({
        method: 'universal_workshop.training_management.api.contextual_help.search_help_content',
        args: {
            query: 'training'
        },
        callback: function (r) {
            if (r.message) {
                console.log('✓ Search API working');
                console.log(`  Found ${r.message.results.length} search results`);
            } else {
                console.log('✗ Search API failed');
            }
        }
    });
}

// Test UI components
function testUIComponents() {
    console.log('Testing UI Components...');

    // Check for help widget
    if ($('.contextual-help-widget').length > 0) {
        console.log('✓ Help widget found in DOM');
    } else {
        console.log('✗ Help widget not found');
    }

    // Test F1 key functionality
    console.log('Press F1 to test contextual help shortcut');

    // Test help icon clicks
    if ($('.help-icon').length > 0) {
        console.log(`✓ Found ${$('.help-icon').length} help icons`);
    } else {
        console.log('! No help icons found (this is normal if none are configured)');
    }
}

// Run all tests when page is ready
$(document).ready(function () {
    setTimeout(function () {
        console.log('=== Contextual Help System Integration Tests ===');
        testContextualHelpInitialization();
        testHelpContentLoading();
        testAPIEndpoints();
        testUIComponents();
        console.log('=== Integration Tests Complete ===');
    }, 2000); // Wait 2 seconds for system to initialize
});

// Export for manual testing
window.helpSystemTests = {
    testContextualHelpInitialization,
    testHelpContentLoading,
    testAPIEndpoints,
    testUIComponents
};
