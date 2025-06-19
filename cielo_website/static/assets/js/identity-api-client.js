/**
 * Identity Provider API Client
 * Handles JWT authentication and API calls to the identity-provider service
 */

class IdentityApiClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.apiUrl = `${baseUrl}/api`;
    }

    /**
     * Get JWT token from cookie
     * @returns {string|null} JWT token or null if not found
     */
    getToken() {
        const cookies = document.cookie.split(';');
        console.log('Available cookies:', document.cookie);
        
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'jwt_token') {
                console.log('Found JWT token in cookie');
                return value;
            }
        }
        
        console.warn('JWT token not found in cookies');
        return null;
    }

    /**
     * Make authenticated API request
     * @param {string} endpoint - API endpoint (e.g., '/profile')
     * @param {object} options - Fetch options
     * @returns {Promise<Response>} Fetch response
     */
    async apiRequest(endpoint, options = {}) {
        const token = this.getToken();
        
        if (!token) {
            throw new Error('No authentication token found');
        }

        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        };

        // Merge options with defaults
        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...(options.headers || {})
            }
        };

        const response = await fetch(`${this.apiUrl}${endpoint}`, mergedOptions);
        
        if (!response.ok) {
            let errorMessage = `HTTP ${response.status}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.message || errorMessage;
            } catch (e) {
                // If response is not JSON, use status text
                errorMessage = response.statusText || errorMessage;
            }
            throw new Error(errorMessage);
        }

        return response;
    }

    /**
     * Get user profile information
     * @returns {Promise<object>} User profile data
     */
    async getProfile() {
        const response = await this.apiRequest('/profile/');
        return await response.json();
    }

    /**
     * Get API information
     * @returns {Promise<object>} API information
     */
    async getApiInfo() {
        const response = await this.apiRequest('/');
        return await response.json();
    }

    /**
     * Check if user is authenticated (has valid JWT token)
     * @returns {Promise<boolean>} True if authenticated
     */
    async isAuthenticated() {
        try {
            await this.getProfile();
            return true;
        } catch (error) {
            return false;
        }
    }
}

/**
 * Profile Page Handler
 * Manages the profile page functionality
 */
class ProfilePageHandler {
    constructor(identityApiClient) {
        this.apiClient = identityApiClient;
        this.isLoading = false;
    }

    /**
     * Initialize the profile page
     */
    async init() {
        this.setupEventListeners();
        await this.loadProfile();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Refresh button
        const refreshBtn = document.getElementById('refresh-profile-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadProfile());
        }

        // Retry button (shown on error)
        const retryBtn = document.getElementById('retry-profile-btn');
        if (retryBtn) {
            retryBtn.addEventListener('click', () => this.loadProfile());
        }
    }

    /**
     * Show loading state
     */
    showLoading() {
        this.isLoading = true;
        const loadingEl = document.getElementById('profile-loading');
        const contentEl = document.getElementById('profile-content');
        const errorEl = document.getElementById('profile-error');
        
        if (loadingEl) loadingEl.style.display = 'block';
        if (contentEl) contentEl.style.display = 'none';
        if (errorEl) errorEl.style.display = 'none';

        // Disable refresh button
        const refreshBtn = document.getElementById('refresh-profile-btn');
        if (refreshBtn) {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<i class="mdi mdi-loading mdi-spin"></i> Loading...';
        }
    }

    /**
     * Show profile content
     */
    showContent() {
        this.isLoading = false;
        const loadingEl = document.getElementById('profile-loading');
        const contentEl = document.getElementById('profile-content');
        const errorEl = document.getElementById('profile-error');
        
        if (loadingEl) loadingEl.style.display = 'none';
        if (contentEl) contentEl.style.display = 'block';
        if (errorEl) errorEl.style.display = 'none';

        // Re-enable refresh button
        const refreshBtn = document.getElementById('refresh-profile-btn');
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="mdi mdi-refresh"></i> Refresh';
        }
    }

    /**
     * Show error state
     * @param {string} errorMessage - Error message to display
     */
    showError(errorMessage) {
        this.isLoading = false;
        const loadingEl = document.getElementById('profile-loading');
        const contentEl = document.getElementById('profile-content');
        const errorEl = document.getElementById('profile-error');
        const errorMessageEl = document.getElementById('profile-error-message');
        
        if (loadingEl) loadingEl.style.display = 'none';
        if (contentEl) contentEl.style.display = 'none';
        if (errorEl) errorEl.style.display = 'block';
        if (errorMessageEl) errorMessageEl.textContent = errorMessage;

        // Re-enable refresh button
        const refreshBtn = document.getElementById('refresh-profile-btn');
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="mdi mdi-refresh"></i> Refresh';
        }
    }

    /**
     * Update profile display with data
     * @param {object} profileData - Profile data from API
     */
    updateProfileDisplay(profileData) {
        // Update username
        const usernameEl = document.getElementById('profile-username');
        if (usernameEl) usernameEl.textContent = profileData.username || 'N/A';

        // Update email
        const emailEl = document.getElementById('profile-email');
        if (emailEl) emailEl.textContent = profileData.email || 'N/A';

        // Update timestamp
        const timestampEl = document.getElementById('profile-timestamp');
        if (timestampEl && profileData.timestamp) {
            const date = new Date(profileData.timestamp);
            timestampEl.textContent = date.toLocaleString();
        }

        // Update last updated time
        const lastUpdatedEl = document.getElementById('profile-last-updated');
        if (lastUpdatedEl) {
            lastUpdatedEl.textContent = new Date().toLocaleString();
        }
    }

    /**
     * Load and display user profile
     */
    async loadProfile() {
        if (this.isLoading) return;

        try {
            this.showLoading();
            
            const profileData = await this.apiClient.getProfile();
            
            this.updateProfileDisplay(profileData);
            this.showContent();
            
            console.log('Profile loaded successfully:', profileData);
            
        } catch (error) {
            console.error('Failed to load profile:', error);
            this.showError(error.message || 'Failed to load profile information');
        }
    }
}

// Global variables for use in templates
window.IdentityApiClient = IdentityApiClient;
window.ProfilePageHandler = ProfilePageHandler;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the profile page
    if (document.getElementById('profile-content')) {
        // Get identity service URL from template context
        const identityServiceUrl = window.IDENTITY_SERVICE_URL;
        
        if (identityServiceUrl) {
            const apiClient = new IdentityApiClient(identityServiceUrl);
            const profileHandler = new ProfilePageHandler(apiClient);
            
            // Initialize profile page
            profileHandler.init().catch(error => {
                console.error('Failed to initialize profile page:', error);
            });
            
            // Make handlers available globally for debugging
            window.profileApiClient = apiClient;
            window.profileHandler = profileHandler;
        } else {
            console.error('Identity service URL not found');
        }
    }
});