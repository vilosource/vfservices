/**
 * Avatar Management Module
 * Handles loading and uploading user avatars from/to the Identity Provider
 */

const AvatarManager = {
    // Configuration
    config: {
        identityProviderUrl: 'https://identity.vfservices.viloforge.com',
        defaultAvatarsPath: '/static/assets/images/users/',
        defaultAvatarCount: 10,
        cacheKey: 'userAvatarData',
        cacheExpiry: 300000, // 5 minutes in milliseconds
    },

    /**
     * Initialize avatar loading for all avatar elements on the page
     * @param {string} avatarSelector - CSS selector for avatar images (default: '.user-avatar')
     */
    async init(avatarSelector = '.user-avatar') {
        try {
            const userData = await this.fetchUserProfile();
            if (userData) {
                this.updateAvatarElements(userData, avatarSelector);
            }
        } catch (error) {
            console.error('Failed to initialize avatar:', error);
        }
    },

    /**
     * Fetch user profile from Identity Provider
     * @returns {Promise<Object|null>} User profile data or null if failed
     */
    async fetchUserProfile() {
        // Check cache first
        const cached = this.getCachedData();
        if (cached) {
            return cached;
        }

        try {
            const response = await fetch(`${this.config.identityProviderUrl}/api/profile/`, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Accept': 'application/json',
                }
            });

            if (response.ok) {
                const userData = await response.json();
                // Cache the data
                this.setCachedData(userData);
                return userData;
            } else if (response.status === 401) {
                console.warn('User not authenticated');
                return null;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Failed to fetch user profile:', error);
            return null;
        }
    },

    /**
     * Update all avatar elements on the page with user avatar
     * @param {Object} userData - User profile data
     * @param {string} avatarSelector - CSS selector for avatar images
     */
    updateAvatarElements(userData, avatarSelector) {
        const avatarElements = document.querySelectorAll(avatarSelector);
        const avatarUrl = this.getAvatarUrl(userData);

        avatarElements.forEach(element => {
            if (element.tagName === 'IMG') {
                element.src = avatarUrl;
                element.onerror = () => {
                    // Fallback to default avatar if custom avatar fails to load
                    element.src = this.getDefaultAvatar(userData.id);
                };
            } else {
                // For div backgrounds or other elements
                element.style.backgroundImage = `url(${avatarUrl})`;
            }
        });
    },

    /**
     * Get avatar URL for a user
     * @param {Object} userData - User profile data
     * @returns {string} Avatar URL
     */
    getAvatarUrl(userData) {
        if (userData.avatar_url) {
            return userData.avatar_url;
        }
        return this.getDefaultAvatar(userData.id);
    },

    /**
     * Get default avatar based on user ID
     * @param {number} userId - User ID
     * @returns {string} Default avatar URL
     */
    getDefaultAvatar(userId) {
        const avatarNum = ((userId || 0) % this.config.defaultAvatarCount) + 1;
        return `${this.config.defaultAvatarsPath}avatar-${avatarNum}.jpg`;
    },

    /**
     * Upload a new avatar image
     * @param {File} file - Image file to upload
     * @param {Function} progressCallback - Optional callback for upload progress
     * @returns {Promise<Object>} Response with new avatar URL
     */
    async uploadAvatar(file, progressCallback = null) {
        if (!file) {
            throw new Error('No file provided');
        }

        // Validate file type
        const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            throw new Error('Invalid file type. Allowed types: JPEG, PNG, GIF, WebP');
        }

        // Validate file size (5MB max)
        const maxSize = 5 * 1024 * 1024;
        if (file.size > maxSize) {
            throw new Error('File too large. Maximum size is 5MB');
        }

        const formData = new FormData();
        formData.append('avatar', file);

        try {
            const response = await fetch(`${this.config.identityProviderUrl}/api/profile/avatar/`, {
                method: 'POST',
                credentials: 'include',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCsrfToken(),
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }

            const result = await response.json();
            
            // Clear cache to force refresh
            this.clearCache();
            
            // Update all avatar elements immediately
            await this.init();
            
            return result;
        } catch (error) {
            console.error('Avatar upload failed:', error);
            throw error;
        }
    },

    /**
     * Get CSRF token from cookies or meta tag
     * @returns {string} CSRF token
     */
    getCsrfToken() {
        // Try to get from cookie first
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        
        if (cookieValue) {
            return cookieValue;
        }

        // Fallback to meta tag
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.content : '';
    },

    /**
     * Cache management methods
     */
    getCachedData() {
        try {
            const cached = sessionStorage.getItem(this.config.cacheKey);
            if (cached) {
                const data = JSON.parse(cached);
                if (Date.now() - data.timestamp < this.config.cacheExpiry) {
                    return data.userData;
                }
            }
        } catch (error) {
            console.error('Cache read error:', error);
        }
        return null;
    },

    setCachedData(userData) {
        try {
            sessionStorage.setItem(this.config.cacheKey, JSON.stringify({
                userData,
                timestamp: Date.now()
            }));
        } catch (error) {
            console.error('Cache write error:', error);
        }
    },

    clearCache() {
        try {
            sessionStorage.removeItem(this.config.cacheKey);
        } catch (error) {
            console.error('Cache clear error:', error);
        }
    },

    /**
     * Create an avatar upload widget
     * @param {string} containerId - ID of the container element
     * @param {Object} options - Widget options
     */
    createUploadWidget(containerId, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container with ID '${containerId}' not found`);
            return;
        }

        const widget = document.createElement('div');
        widget.className = 'avatar-upload-widget';
        widget.innerHTML = `
            <div class="avatar-preview">
                <img class="user-avatar avatar-preview-img" src="${this.config.defaultAvatarsPath}avatar-1.jpg" alt="Avatar">
            </div>
            <div class="avatar-controls">
                <input type="file" id="avatar-file-input" accept="image/jpeg,image/png,image/gif,image/webp" style="display: none;">
                <button class="btn btn-primary btn-sm" onclick="document.getElementById('avatar-file-input').click()">
                    Change Avatar
                </button>
                <div class="avatar-upload-status"></div>
            </div>
        `;

        container.appendChild(widget);

        // Initialize current avatar
        this.init('.avatar-preview-img');

        // Handle file selection
        const fileInput = widget.querySelector('#avatar-file-input');
        const statusDiv = widget.querySelector('.avatar-upload-status');

        fileInput.addEventListener('change', async (event) => {
            const file = event.target.files[0];
            if (!file) return;

            statusDiv.innerHTML = '<span class="text-info">Uploading...</span>';

            try {
                const result = await this.uploadAvatar(file);
                statusDiv.innerHTML = '<span class="text-success">Avatar updated successfully!</span>';
                
                // Clear status message after 3 seconds
                setTimeout(() => {
                    statusDiv.innerHTML = '';
                }, 3000);

                // Call custom callback if provided
                if (options.onSuccess) {
                    options.onSuccess(result);
                }
            } catch (error) {
                statusDiv.innerHTML = `<span class="text-danger">Error: ${error.message}</span>`;
                
                // Call custom callback if provided
                if (options.onError) {
                    options.onError(error);
                }
            }

            // Clear file input
            fileInput.value = '';
        });
    }
};

// Auto-initialize on DOMContentLoaded if not in a module context
if (typeof module === 'undefined' && typeof exports === 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        AvatarManager.init();
    });
}