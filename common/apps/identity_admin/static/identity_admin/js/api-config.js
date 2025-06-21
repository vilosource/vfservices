/**
 * API Configuration for Identity Admin
 * 
 * This file determines whether to use the mock API or the real Identity Provider API
 */

// Check if we're in development mode or if the real API is available
window.USE_MOCK_API = false;  // Set to false to use real API

// Get the API implementation based on configuration
window.getIdentityAPI = function() {
    if (window.USE_MOCK_API) {
        console.log('Using Mock Identity API');
        return new MockIdentityAPI();
    } else {
        console.log('Using Real Identity Provider API');
        return new IdentityProviderAPI();
    }
};

/**
 * Real Identity Provider API Client
 */
class IdentityProviderAPI {
    constructor() {
        this.client = window.identityAdminClient;
        this.baseUrl = this.client.baseUrl;
    }
    
    // User endpoints
    async listUsers(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = `/api/admin/users/${queryString ? '?' + queryString : ''}`;
        return await this.client.request('GET', url);
    }
    
    async getUser(userId) {
        return await this.client.request('GET', `/api/admin/users/${userId}/`);
    }
    
    async updateUser(userId, data) {
        return await this.client.request('PUT', `/api/admin/users/${userId}/`, data);
    }
    
    async setUserPassword(userId, password) {
        return await this.client.request('POST', `/api/admin/users/${userId}/set-password/`, {
            password: password
        });
    }
    
    // Role endpoints
    async listUserRoles(userId) {
        return await this.client.request('GET', `/api/admin/users/${userId}/roles/`);
    }
    
    async assignRole(userId, roleData) {
        return await this.client.request('POST', `/api/admin/users/${userId}/roles/`, {
            role_name: roleData.role_name,
            service_name: roleData.service_name,
            expires_at: roleData.expires_at || null,
            reason: roleData.reason || ''
        });
    }
    
    async revokeRole(userId, roleId, reason = null) {
        return await this.client.request('DELETE', `/api/admin/users/${userId}/roles/${roleId}/`, {
            reason: reason
        });
    }
    
    // Service and role listing
    async listServices() {
        const response = await this.client.request('GET', '/api/admin/services/');
        return response.results || response;
    }
    
    async listRoles(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = `/api/admin/roles/${queryString ? '?' + queryString : ''}`;
        const response = await this.client.request('GET', url);
        
        // Debug logging
        console.log('Raw roles API response:', response);
        console.log('Response type:', typeof response);
        console.log('Is array:', Array.isArray(response));
        console.log('Has results property:', response.hasOwnProperty('results'));
        
        const roles = response.results || response;
        
        // Log first role to check structure
        if (roles.length > 0) {
            console.log('First role from API:', roles[0]);
            console.log('First role has user_count:', roles[0].hasOwnProperty('user_count'));
        }
        
        // Ensure roles have the expected structure
        return roles.map(role => ({
            ...role,
            service: typeof role.service === 'string' ? { name: role.service_name } : role.service
        }));
    }
}

// Make IdentityProviderAPI available globally
window.IdentityProviderAPI = IdentityProviderAPI;