/**
 * Identity Admin API Client
 * 
 * Client-side JavaScript for making API calls to Identity Provider
 */

class IdentityAdminClient {
    constructor() {
        this.baseUrl = window.IDENTITY_PROVIDER_URL || '';
        this.token = this.getJWTToken();
        this.csrfToken = window.CSRF_TOKEN || this.getCSRFToken();
    }
    
    /**
     * Get JWT token from cookies
     */
    getJWTToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'jwt' || name === 'jwt_token') {
                return value;
            }
        }
        return null;
    }
    
    /**
     * Get CSRF token from cookies
     */
    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return null;
    }
    
    /**
     * Make API request
     */
    async request(method, endpoint, data = null) {
        const url = this.baseUrl + endpoint;
        const options = {
            method: method,
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-CSRFToken': this.csrfToken
            }
        };
        
        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(url, options);
            
            if (!response.ok) {
                let errorMessage = `HTTP ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.message || JSON.stringify(errorData);
                } catch (e) {
                    errorMessage = response.statusText || errorMessage;
                }
                throw new Error(errorMessage);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
    
    // User Management Methods
    
    async assignRole(userId, roleData) {
        return this.request('POST', `/api/admin/users/${userId}/roles/`, roleData);
    }
    
    async revokeRole(userId, roleId, reason = null) {
        const data = reason ? { reason } : null;
        return this.request('DELETE', `/api/admin/users/${userId}/roles/${roleId}/`, data);
    }
    
    async updateUserAttribute(userId, attributeName, attributeValue) {
        return this.request('POST', `/api/admin/users/${userId}/attributes/`, {
            name: attributeName,
            value: attributeValue
        });
    }
    
    // Utility Methods
    
    showSuccess(message) {
        this.showAlert(message, 'success');
    }
    
    showError(message) {
        this.showAlert(message, 'danger');
    }
    
    showAlert(message, type = 'info') {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        
        // Find or create alert container
        let alertContainer = document.getElementById('alert-container');
        if (!alertContainer) {
            const pageTitle = document.querySelector('.page-title-box');
            if (pageTitle) {
                alertContainer = document.createElement('div');
                alertContainer.id = 'alert-container';
                pageTitle.parentNode.insertBefore(alertContainer, pageTitle.nextSibling);
            }
        }
        
        if (alertContainer) {
            alertContainer.insertAdjacentHTML('beforeend', alertHtml);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                const alert = alertContainer.lastElementChild;
                if (alert) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, 5000);
        }
    }
}

// Initialize global instance
window.identityAdminClient = new IdentityAdminClient();