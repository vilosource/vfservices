/**
 * Mock API implementation for Identity Admin
 * This provides mock data until the Identity Provider API endpoints are implemented
 */

class MockIdentityAPI {
    constructor() {
        // Mock data storage
        this.users = [
            {
                id: 1,
                username: 'admin',
                email: 'admin@example.com',
                first_name: 'Admin',
                last_name: 'User',
                is_active: true,
                is_staff: true,
                is_superuser: true,
                date_joined: '2025-06-16T18:13:23.572311Z',
                last_login: '2025-06-20T15:42:00Z',
                roles_count: 1
            },
            {
                id: 8,
                username: 'alice',
                email: 'alice@example.com',
                first_name: 'Alice',
                last_name: 'User',
                is_active: true,
                is_staff: false,
                is_superuser: false,
                date_joined: '2025-06-16T18:13:24.068897Z',
                last_login: '2025-06-20T15:52:00Z',
                roles_count: 2
            }
        ];
        
        this.roles = [
            {
                id: 1,
                name: 'identity_admin',
                display_name: 'Identity Administrator',
                description: 'Full administrative access to identity provider',
                service_name: 'identity_provider',
                service_display_name: 'Identity Provider',
                is_global: true
            },
            {
                id: 2,
                name: 'customer_manager',
                display_name: 'Customer Manager',
                description: 'Can manage customer records and relationships',
                service_name: 'identity_provider',
                service_display_name: 'Identity Provider',
                is_global: true
            },
            {
                id: 3,
                name: 'billing_admin',
                display_name: 'Billing Administrator',
                description: 'Full access to billing operations',
                service_name: 'billing_api',
                service_display_name: 'Billing API',
                is_global: true
            }
        ];
        
        this.userRoles = [
            {
                id: 1,
                user_id: 1,
                role_id: 1,
                role_name: 'identity_admin',
                role_display_name: 'Identity Administrator',
                service_name: 'identity_provider',
                service_display_name: 'Identity Provider',
                granted_at: '2025-06-20T15:39:00Z',
                granted_by_username: 'system',
                expires_at: null,
                is_active: true
            },
            {
                id: 2,
                user_id: 8,
                role_id: 2,
                role_name: 'customer_manager',
                role_display_name: 'Customer Manager',
                service_name: 'identity_provider',
                service_display_name: 'Identity Provider',
                granted_at: '2025-06-16T18:13:24.068897Z',
                granted_by_username: 'system',
                expires_at: null,
                is_active: true
            },
            {
                id: 3,
                user_id: 8,
                role_id: 1,
                role_name: 'identity_admin',
                role_display_name: 'Identity Administrator',
                service_name: 'identity_provider',
                service_display_name: 'Identity Provider',
                granted_at: '2025-06-20T15:47:00Z',
                granted_by_username: 'admin',
                expires_at: null,
                is_active: true
            }
        ];
        
        this.services = [
            {
                id: 1,
                name: 'identity_provider',
                display_name: 'Identity Provider',
                description: 'Core identity and access management service',
                is_active: true,
                manifest_version: '1.0',
                created_at: '2025-06-16T00:00:00Z'
            },
            {
                id: 2,
                name: 'billing_api',
                display_name: 'Billing API',
                description: 'Billing and invoice management service',
                is_active: true,
                manifest_version: '1.0',
                created_at: '2025-06-16T00:00:00Z'
            },
            {
                id: 3,
                name: 'inventory_api',
                display_name: 'Inventory API',
                description: 'Inventory management service',
                is_active: true,
                manifest_version: '1.0',
                created_at: '2025-06-16T00:00:00Z'
            },
            {
                id: 4,
                name: 'website',
                display_name: 'Website',
                description: 'Main website and portal',
                is_active: true,
                manifest_version: '1.0',
                created_at: '2025-06-16T00:00:00Z'
            }
        ];
    }
    
    // Simulate API delay
    async delay(ms = 300) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // User endpoints
    async listUsers(params = {}) {
        await this.delay();
        
        let filteredUsers = [...this.users];
        
        // Apply search filter
        if (params.search) {
            const search = params.search.toLowerCase();
            filteredUsers = filteredUsers.filter(user => 
                user.username.toLowerCase().includes(search) ||
                user.email.toLowerCase().includes(search) ||
                user.first_name.toLowerCase().includes(search) ||
                user.last_name.toLowerCase().includes(search)
            );
        }
        
        // Apply is_active filter
        if (params.is_active === 'true') {
            filteredUsers = filteredUsers.filter(user => user.is_active);
        } else if (params.is_active === 'false') {
            filteredUsers = filteredUsers.filter(user => !user.is_active);
        }
        
        // Pagination
        const page = parseInt(params.page) || 1;
        const pageSize = parseInt(params.page_size) || 50;
        const start = (page - 1) * pageSize;
        const end = start + pageSize;
        const paginatedUsers = filteredUsers.slice(start, end);
        
        return {
            count: filteredUsers.length,
            next: end < filteredUsers.length ? `?page=${page + 1}` : null,
            previous: page > 1 ? `?page=${page - 1}` : null,
            results: paginatedUsers
        };
    }
    
    async getUser(userId) {
        await this.delay();
        
        const user = this.users.find(u => u.id === parseInt(userId));
        if (!user) {
            throw new Error('User not found');
        }
        
        // Add roles to user details
        const userRoles = this.userRoles.filter(ur => ur.user_id === user.id);
        
        return {
            ...user,
            roles: userRoles
        };
    }
    
    async updateUser(userId, data) {
        await this.delay();
        
        const userIndex = this.users.findIndex(u => u.id === parseInt(userId));
        if (userIndex === -1) {
            throw new Error('User not found');
        }
        
        // Update user data
        this.users[userIndex] = {
            ...this.users[userIndex],
            ...data,
            id: this.users[userIndex].id,  // Preserve ID
            username: this.users[userIndex].username  // Preserve username
        };
        
        return this.users[userIndex];
    }
    
    async setUserPassword(userId, password) {
        await this.delay();
        
        const user = this.users.find(u => u.id === parseInt(userId));
        if (!user) {
            throw new Error('User not found');
        }
        
        // In mock, just return success
        return { status: 'Password set successfully' };
    }
    
    // Role endpoints
    async listUserRoles(userId) {
        await this.delay();
        
        return this.userRoles.filter(ur => ur.user_id === parseInt(userId));
    }
    
    async assignRole(userId, roleData) {
        await this.delay();
        
        // Find the role
        const role = this.roles.find(r => 
            r.name === roleData.role_name && 
            r.service_name === roleData.service_name
        );
        
        if (!role) {
            throw new Error('Role not found');
        }
        
        // Check if already assigned
        const existing = this.userRoles.find(ur => 
            ur.user_id === parseInt(userId) && 
            ur.role_id === role.id
        );
        
        if (existing) {
            throw new Error('User already has this role');
        }
        
        // Create new assignment
        const newAssignment = {
            id: Math.max(...this.userRoles.map(ur => ur.id)) + 1,
            user_id: parseInt(userId),
            role_id: role.id,
            role_name: role.name,
            role_display_name: role.display_name,
            service_name: role.service_name,
            service_display_name: role.service_display_name,
            granted_at: new Date().toISOString(),
            granted_by_username: 'admin',  // Mock current user
            expires_at: roleData.expires_at || null,
            is_active: true
        };
        
        this.userRoles.push(newAssignment);
        
        return {
            id: newAssignment.id,
            message: `Role ${role.display_name} assigned successfully`
        };
    }
    
    async revokeRole(userId, roleId) {
        await this.delay();
        
        const index = this.userRoles.findIndex(ur => 
            ur.user_id === parseInt(userId) && 
            ur.id === parseInt(roleId)
        );
        
        if (index === -1) {
            throw new Error('Role assignment not found');
        }
        
        this.userRoles.splice(index, 1);
        
        return { status: 'Role revoked successfully' };
    }
    
    // Service and role listing
    async listServices() {
        await this.delay();
        return this.services;
    }
    
    async listRoles(params = {}) {
        await this.delay();
        
        let filteredRoles = [...this.roles];
        
        if (params.service) {
            filteredRoles = filteredRoles.filter(r => r.service_name === params.service);
        }
        
        if (params.is_global === 'true') {
            filteredRoles = filteredRoles.filter(r => r.is_global);
        } else if (params.is_global === 'false') {
            filteredRoles = filteredRoles.filter(r => !r.is_global);
        }
        
        return filteredRoles;
    }
}

// Export for use
window.MockIdentityAPI = MockIdentityAPI;