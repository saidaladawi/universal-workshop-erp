/**
 * Enhanced V2 Bridge Loader - Universal Workshop ERP
 * 
 * Advanced integration layer for progressive migration between traditional and V2 frontends
 * Complements the existing frontend_switcher.js with runtime component loading capabilities
 */

class V2BridgeLoader {
    constructor() {
        this.loadedModules = new Map();
        this.componentRegistry = new Map();
        this.loadingPromises = new Map();
        this.eventBridge = null;
        this.stateBridge = null;
        this.isV2Available = false;
        this.v2Config = null;
        
        this.init();
    }
    
    async init() {
        try {
            // Check if V2 is available through existing frontend bridge
            await this.checkV2Availability();
            
            if (this.isV2Available) {
                await this.initializeBridges();
                this.setupGlobalAPI();
                console.log('✅ V2 Bridge Loader initialized successfully');
            }
        } catch (error) {
            console.error('❌ V2 Bridge Loader initialization failed:', error);
        }
    }
    
    async checkV2Availability() {
        try {
            const response = await frappe.call({
                method: 'universal_workshop.api.frontend_bridge.get_v2_config'
            });
            
            if (response.message) {
                this.isV2Available = true;
                this.v2Config = response.message;
                return true;
            }
        } catch (error) {
            console.log('V2 not available:', error.message);
            this.isV2Available = false;
        }
        
        return false;
    }
    
    async initializeBridges() {
        // Initialize event bridge for cross-system communication
        this.eventBridge = new V2EventBridge();
        
        // Initialize state bridge for data synchronization  
        this.stateBridge = new V2StateBridge();
        
        // Setup progressive component loading
        this.setupProgressiveLoading();
    }
    
    setupGlobalAPI() {
        // Create global API for V2 integration
        window.UniversalWorkshopV2 = {
            // Core module loading
            loadModule: this.loadModule.bind(this),
            loadComponent: this.loadComponent.bind(this),
            
            // Component management
            replaceComponent: this.replaceComponent.bind(this),
            embedComponent: this.embedComponent.bind(this),
            unregisterComponent: this.unregisterComponent.bind(this),
            
            // State management
            syncState: this.syncState.bind(this),
            bridgeFormData: this.bridgeFormData.bind(this),
            
            // Event handling
            emitEvent: this.emitEvent.bind(this),
            onEvent: this.onEvent.bind(this),
            
            // Progressive migration
            enableFeature: this.enableFeature.bind(this),
            migrateView: this.migrateView.bind(this),
            
            // Utilities
            isV2Available: () => this.isV2Available,
            getConfig: () => this.v2Config,
            getLoadedModules: () => Array.from(this.loadedModules.keys())
        };
    }
    
    async loadModule(moduleName, options = {}) {
        if (!this.isV2Available) {
            throw new Error('V2 is not available');
        }
        
        // Check if module is already loaded
        if (this.loadedModules.has(moduleName)) {
            return this.loadedModules.get(moduleName);
        }
        
        // Check if loading is in progress
        if (this.loadingPromises.has(moduleName)) {
            return this.loadingPromises.get(moduleName);
        }
        
        // Start loading
        const loadingPromise = this._loadModuleAssets(moduleName, options);
        this.loadingPromises.set(moduleName, loadingPromise);
        
        try {
            const module = await loadingPromise;
            this.loadedModules.set(moduleName, module);
            this.loadingPromises.delete(moduleName);
            
            console.log(`✅ V2 module '${moduleName}' loaded successfully`);
            return module;
        } catch (error) {
            this.loadingPromises.delete(moduleName);
            console.error(`❌ Failed to load V2 module '${moduleName}':`, error);
            throw error;
        }
    }
    
    async _loadModuleAssets(moduleName, options) {
        const baseUrl = '/assets/universal_workshop/v2';
        const moduleUrl = `${baseUrl}/${moduleName}.js`;
        
        // Dynamic import with error handling
        try {
            const module = await import(moduleUrl);
            
            // If module has an initialization function, call it
            if (module.default && typeof module.default.init === 'function') {
                await module.default.init(options);
            }
            
            return module;
        } catch (error) {
            // Fallback: try loading via script tag
            return this._loadModuleViaScript(moduleUrl, moduleName);
        }
    }
    
    _loadModuleViaScript(url, moduleName) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.type = 'module';
            script.src = url;
            
            script.onload = () => {
                // Check if module was loaded into global scope
                const module = window[`UniversalWorkshop_${moduleName}`];
                if (module) {
                    resolve(module);
                } else {
                    resolve({ loaded: true, moduleName });
                }
            };
            
            script.onerror = () => {
                reject(new Error(`Failed to load script: ${url}`));
            };
            
            document.head.appendChild(script);
        });
    }
    
    async loadComponent(componentName, containerSelector, props = {}) {
        try {
            // Load the main module if not already loaded
            const mainModule = await this.loadModule('main');
            
            // Get component from registry
            let component = this.componentRegistry.get(componentName);
            
            if (!component && mainModule.componentRegistry) {
                component = mainModule.componentRegistry.get(componentName);
            }
            
            if (!component) {
                throw new Error(`Component '${componentName}' not found`);
            }
            
            // Mount component to container
            const container = document.querySelector(containerSelector);
            if (!container) {
                throw new Error(`Container '${containerSelector}' not found`);
            }
            
            // Create component instance
            const instance = await this._createComponentInstance(component, container, props);
            
            return instance;
        } catch (error) {
            console.error(`Failed to load component '${componentName}':`, error);
            throw error;
        }
    }
    
    async _createComponentInstance(component, container, props) {
        // Clear container
        container.innerHTML = '';
        
        // Create wrapper div for Vue component
        const wrapper = document.createElement('div');
        wrapper.className = 'v2-component-wrapper';
        container.appendChild(wrapper);
        
        // Mount component (this would integrate with Vue.js mounting)
        if (typeof component.mount === 'function') {
            return await component.mount(wrapper, props);
        } else if (typeof component === 'function') {
            return await component(wrapper, props);
        } else {
            throw new Error('Invalid component format');
        }
    }
    
    async replaceComponent(selector, componentName, props = {}) {
        const containers = document.querySelectorAll(selector);
        const instances = [];
        
        for (const container of containers) {
            try {
                const instance = await this.loadComponent(componentName, container, props);
                instances.push(instance);
                
                // Add replacement marker
                container.setAttribute('data-v2-component', componentName);
                container.classList.add('v2-replaced');
                
            } catch (error) {
                console.error(`Failed to replace component at '${selector}':`, error);
            }
        }
        
        return instances;
    }
    
    embedComponent(containerSelector, componentName, props = {}) {
        // Non-blocking component embedding
        this.loadComponent(componentName, containerSelector, props)
            .then(instance => {
                console.log(`✅ Component '${componentName}' embedded successfully`);
                this.emitEvent('component_embedded', { componentName, instance });
            })
            .catch(error => {
                console.error(`❌ Failed to embed component '${componentName}':`, error);
                this.emitEvent('component_embed_failed', { componentName, error });
            });
    }
    
    unregisterComponent(componentName) {
        // Remove component instances
        const containers = document.querySelectorAll(`[data-v2-component="${componentName}"]`);
        containers.forEach(container => {
            container.innerHTML = '';
            container.removeAttribute('data-v2-component');
            container.classList.remove('v2-replaced');
        });
        
        // Remove from registry
        this.componentRegistry.delete(componentName);
        
        console.log(`🗑️ Component '${componentName}' unregistered`);
    }
    
    async syncState(dataType, direction = 'toV2') {
        if (!this.stateBridge) {
            throw new Error('State bridge not initialized');
        }
        
        return await this.stateBridge.sync(dataType, direction);
    }
    
    async bridgeFormData(formName, formData) {
        if (!this.stateBridge) {
            throw new Error('State bridge not initialized');
        }
        
        return await this.stateBridge.bridgeForm(formName, formData);
    }
    
    emitEvent(eventName, data = {}) {
        if (this.eventBridge) {
            this.eventBridge.emit(eventName, data);
        }
        
        // Also emit to traditional Frappe events
        $(document).trigger(`v2:${eventName}`, data);
    }
    
    onEvent(eventName, callback) {
        if (this.eventBridge) {
            this.eventBridge.on(eventName, callback);
        }
        
        // Also listen to traditional Frappe events
        $(document).on(`v2:${eventName}`, (event, data) => callback(data));
    }
    
    async enableFeature(featureName, enabled = true) {
        try {
            // This would integrate with feature flags
            const response = await frappe.call({
                method: 'universal_workshop.api.frontend_bridge.toggle_feature',
                args: { feature: featureName, enabled }
            });
            
            this.emitEvent('feature_toggled', { featureName, enabled });
            return response.message;
        } catch (error) {
            console.error(`Failed to toggle feature '${featureName}':`, error);
            throw error;
        }
    }
    
    async migrateView(viewName, options = {}) {
        try {
            console.log(`🔄 Starting migration of view '${viewName}'`);
            
            // Load required components for the view
            if (options.components) {
                for (const component of options.components) {
                    await this.loadComponent(component.name, component.selector, component.props);
                }
            }
            
            // Sync necessary data
            if (options.syncData) {
                for (const dataType of options.syncData) {
                    await this.syncState(dataType);
                }
            }
            
            this.emitEvent('view_migrated', { viewName, options });
            console.log(`✅ View '${viewName}' migrated successfully`);
            
        } catch (error) {
            console.error(`❌ Failed to migrate view '${viewName}':`, error);
            throw error;
        }
    }
    
    setupProgressiveLoading() {
        // Setup intersection observer for lazy loading components
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const element = entry.target;
                        const componentName = element.getAttribute('data-v2-lazy');
                        
                        if (componentName) {
                            this.embedComponent(element, componentName);
                            observer.unobserve(element);
                        }
                    }
                });
            });
            
            // Observe elements marked for lazy loading
            document.querySelectorAll('[data-v2-lazy]').forEach(el => {
                observer.observe(el);
            });
        }
    }
}

// Event Bridge Class
class V2EventBridge {
    constructor() {
        this.listeners = new Map();
    }
    
    emit(eventName, data) {
        const listeners = this.listeners.get(eventName) || [];
        listeners.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`Error in event listener for '${eventName}':`, error);
            }
        });
    }
    
    on(eventName, callback) {
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, []);
        }
        this.listeners.get(eventName).push(callback);
    }
    
    off(eventName, callback) {
        const listeners = this.listeners.get(eventName) || [];
        const index = listeners.indexOf(callback);
        if (index > -1) {
            listeners.splice(index, 1);
        }
    }
}

// State Bridge Class  
class V2StateBridge {
    constructor() {
        this.syncQueue = [];
        this.syncInProgress = false;
    }
    
    async sync(dataType, direction = 'toV2') {
        try {
            const response = await frappe.call({
                method: 'universal_workshop.api.frontend_bridge.sync_v2_data',
                args: { data_type: dataType }
            });
            
            if (response.message) {
                console.log(`✅ Data sync completed for '${dataType}'`);
                return response.message;
            }
        } catch (error) {
            console.error(`❌ Data sync failed for '${dataType}':`, error);
            throw error;
        }
    }
    
    async bridgeForm(formName, formData) {
        // Bridge form data between traditional and V2 systems
        return {
            bridged: true,
            formName,
            data: formData,
            timestamp: Date.now()
        };
    }
}

// Initialize V2 Bridge Loader
$(document).ready(() => {
    // Only initialize if we're in the main app and not already in V2 mode
    if (window.location.pathname.startsWith('/app') && 
        !window.location.pathname.includes('/universal-workshop-v2')) {
        
        window.v2BridgeLoader = new V2BridgeLoader();
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { V2BridgeLoader, V2EventBridge, V2StateBridge };
}