# Universal Workshop Contextual Help System Documentation

## Overview
The Contextual Help System provides in-application assistance with smart context detection, interactive tooltips, and seamless integration with training modules and documentation.

## Features

### 1. Context Detection
- Automatically detects user's current location in the application
- Provides relevant help content based on route, DocType, and user role
- Supports multilingual content (English/Arabic)

### 2. Interactive Components
- **Help Widget**: Floating help button with search functionality
- **Tooltips**: Context-sensitive tooltips for form fields and buttons
- **Banners**: Important announcements and notifications
- **Overlays**: Guided tours and step-by-step instructions

### 3. Content Management
- **Help Content DocType**: Centralized content management
- **Role-based Content**: Different content for different user roles
- **Priority System**: High, Medium, Low priority content
- **Multiple Content Types**: Quick Tips, Guided Tours, Documentation, Training, Videos

### 4. Analytics and Feedback
- **Usage Tracking**: Monitor which help content is accessed
- **User Feedback**: Collect ratings and comments
- **Analytics Report**: Comprehensive usage analytics

## Implementation

### Backend Components

#### DocTypes
1. **Help Content** - Main content storage
2. **Help Content Route** - Route-specific mappings
3. **Help Content Role** - Role-based access
4. **Help Content Documentation** - Documentation links
5. **Help Content Training** - Training module integration
6. **Help Content Video** - Video content
7. **Help Usage Log** - Usage tracking
8. **Help Content Feedback** - User feedback

#### API Endpoints
```python
# Get contextual help for current route
universal_workshop.training_management.api.contextual_help.get_contextual_help(route, user_role)

# Search help content
universal_workshop.training_management.api.contextual_help.search_help_content(query, filters)

# Log help usage
universal_workshop.training_management.api.contextual_help.log_help_usage(content_key, action)

# Submit feedback
universal_workshop.training_management.api.contextual_help.submit_help_feedback(content_key, rating, feedback)
```

### Frontend Components

#### JavaScript Classes
```javascript
// Main help system class
class ContextualHelpSystem {
    init()                    // Initialize the system
    loadHelpContent()         // Load help content from server
    createHelpWidget()        // Create floating help widget
    showContextualHelp()      // Display contextual help
    showTooltip()            // Show interactive tooltips
    showBanner()             // Display help banners
    showOverlay()            // Display guided overlays
}
```

#### Global Functions
```javascript
// Show help for specific content key
window.showHelp(contentKey)

// Toggle help widget
window.toggleHelpWidget()

// Search help content
window.searchHelp(query)
```

## Usage

### For Administrators

#### Creating Help Content
1. Go to Help Content list
2. Create new Help Content record
3. Set content key, title, and description
4. Define target routes and roles
5. Add content in HTML format
6. Set priority and activate

#### Managing Content
- Use the Help Content list to manage all help items
- Configure routes for context-specific help
- Set role permissions for targeted assistance
- Monitor usage through Help Content Analytics report

### For Developers

#### Adding Help Icons
```html
<!-- Add help icon to any element -->
<i class="fa fa-question-circle help-icon" data-help-key="your-content-key"></i>
```

#### Triggering Help Programmatically
```javascript
// Show specific help content
window.contextualHelp.showHelpContent('content-key');

// Show contextual help for current page
window.contextualHelp.showContextualHelp();
```

#### Custom Help Integration
```javascript
// Register custom help handler
frappe.ui.toolbar.add_dropdown_button("Help", function() {
    window.contextualHelp.showContextualHelp();
});
```

### For End Users

#### Accessing Help
- **F1 Key**: Press F1 for contextual help
- **Help Widget**: Click floating help button
- **Help Icons**: Click ? icons next to form elements
- **Search**: Use help widget search functionality

#### Providing Feedback
- Rate help content (1-5 stars)
- Submit comments and suggestions
- Report issues with help content

## Configuration

### Settings
```json
{
    "enable_contextual_help": true,
    "help_widget_position": "bottom-right",
    "show_help_icons": true,
    "enable_help_analytics": true,
    "default_language": "en"
}
```

### Customization
- Modify CSS for custom styling
- Override JavaScript methods for custom behavior
- Create custom content types
- Implement custom analytics

## Testing

### Manual Testing
1. Navigate to any page in the application
2. Press F1 to test contextual help
3. Click help icons if available
4. Test search functionality
5. Verify multilingual content

### Automated Testing
```javascript
// Run integration tests
window.helpSystemTests.testContextualHelpInitialization();
window.helpSystemTests.testHelpContentLoading();
window.helpSystemTests.testAPIEndpoints();
window.helpSystemTests.testUIComponents();
```

## Troubleshooting

### Common Issues
1. **Help content not showing**: Check if content is active and route mapping is correct
2. **JavaScript errors**: Verify all dependencies are loaded
3. **API errors**: Check server logs and permissions
4. **Multilingual issues**: Verify language settings and content translation

### Debugging
```javascript
// Enable debug mode
window.contextualHelp.debugMode = true;

// Check help content loading
console.log(window.contextualHelp.helpContent);

// Test API endpoints
frappe.call({
    method: 'universal_workshop.training_management.api.contextual_help.get_contextual_help',
    args: { route: window.location.pathname },
    callback: console.log
});
```

## Integration with Training System

### Training Module Links
- Help content can link to specific training modules
- Automatic progress tracking when help is accessed
- Guided learning paths through help system

### Documentation Integration
- Links to knowledge base articles
- PDF document integration
- Video tutorial embedding

## Maintenance

### Regular Tasks
1. Review help content analytics monthly
2. Update content based on user feedback
3. Add new help content for new features
4. Monitor system performance

### Content Updates
- Keep help content synchronized with application changes
- Translate new content for multilingual support
- Archive outdated help content

## Security Considerations

### Permissions
- Help content respects role-based permissions
- Sensitive help content is restricted by role
- Usage analytics respect privacy settings

### Content Safety
- HTML content is sanitized
- External links are validated
- User-generated feedback is moderated

## Performance

### Optimization
- Help content is cached on client side
- Lazy loading for heavy content
- Compressed content delivery
- Background prefetching

### Monitoring
- Track help system performance
- Monitor API response times
- Optimize database queries
- Cache frequently accessed content
