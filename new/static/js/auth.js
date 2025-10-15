// Auth utility class
class Auth {
    constructor() {
        this.baseURL = '/auth';
        this.token = this.getToken();
        this.refreshToken = this.getRefreshToken();
    }

    // Token management
    setToken(token) {
        this.token = token;
        if (token) {
            document.cookie = `authToken=${token}; path=/; samesite=strict`;
        } else {
            document.cookie = 'authToken=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
        }
    }

    getToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'authToken') {
                return value;
            }
        }
        return null;
    }

    setRefreshToken(token) {
        this.refreshToken = token;
        if (token) {
            document.cookie = `refreshToken=${token}; path=/; samesite=strict`;
        } else {
            document.cookie = 'refreshToken=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
        }
    }

    getRefreshToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'refreshToken') {
                return value;
            }
        }
        return null;
    }

    // API request helper
    async makeRequest(endpoint, options = {}) {
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // Add auth token if available
        if (this.token && !config.headers.Authorization) {
            config.headers.Authorization = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, config);
            
            // Handle token refresh if needed
            if (response.status === 401 && this.refreshToken && endpoint !== '/refresh') {
                const refreshed = await this.refreshAccessToken();
                if (refreshed) {
                    config.headers.Authorization = `Bearer ${this.token}`;
                    return await fetch(`${this.baseURL}${endpoint}`, config);
                }
            }

            return response;
        } catch (error) {
            console.error('Request failed:', error);
            throw error;
        }
    }

    // Authentication methods
    async login(email, password, rememberMe = false) {
        try {
            const response = await this.makeRequest('/login', {
                method: 'POST',
                body: JSON.stringify({ email, password, rememberMe })
            });

            const data = await response.json();

            if (response.ok) {
                this.setToken(data.access_token || data.token || data.accessToken);
                if (data.refresh_token || data.refreshToken) {
                    this.setRefreshToken(data.refresh_token || data.refreshToken);
                }
                return { success: true, data };
            } else {
                return { success: false, error: data.error || data.message || 'Login failed' };
            }
        } catch (error) {
            return { success: false, error: 'Network error. Please try again.' };
        }
    }

    async register(userData) {
        try {
            const response = await this.makeRequest('/register', {
                method: 'POST',
                body: JSON.stringify(userData)
            });

            const data = await response.json();

            if (response.ok) {
                // Auto-login after registration if tokens are provided
                if (data.access_token || data.token || data.accessToken) {
                    this.setToken(data.access_token || data.token || data.accessToken);
                    if (data.refresh_token || data.refreshToken) {
                        this.setRefreshToken(data.refresh_token || data.refreshToken);
                    }
                }
                return { success: true, data, status: response.status };
            } else {
                // Log the actual error from server for debugging
                console.log('🔴 Server error response:', data);
                
                // Handle specific error codes
                let errorMessage = data.error || data.message || 'Registration failed';
                
                if (response.status === 409) {
                    // Conflict - user/email already exists
                    console.log('🔴 409 Conflict - Server message:', data.message);
                    
                    if (data.message && data.message.toLowerCase().includes('email')) {
                        errorMessage = 'This email is already registered. Please use a different email or login.';
                    } else if (data.message && data.message.toLowerCase().includes('shelter')) {
                        errorMessage = 'This shelter already has a manager. Please contact administrator.';
                    } else {
                        // Show the actual server message for debugging
                        errorMessage = `Account conflict: ${data.message || 'Please try logging in or use different details.'}`;
                    }
                }
                
                return { 
                    success: false, 
                    error: errorMessage,
                    status: response.status,
                    serverMessage: data.message // Add this for debugging
                };
            }
        } catch (error) {
            console.error('Registration network error:', error);
            return { success: false, error: 'Network error. Please try again.', status: 0 };
        }
    }

    async getMe() {
        try {
            const response = await this.makeRequest('/me');
            const data = await response.json();

            if (response.ok) {
                return { success: true, data };
            } else {
                return { success: false, error: data.message || 'Failed to get user data' };
            }
        } catch (error) {
            return { success: false, error: 'Network error. Please try again.' };
        }
    }

    async refreshAccessToken() {
        if (!this.refreshToken) {
            return false;
        }

        try {
            const response = await fetch(`${this.baseURL}/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refreshToken: this.refreshToken })
            });

            const data = await response.json();

            if (response.ok) {
                this.setToken(data.token || data.accessToken);
                if (data.refreshToken) {
                    this.setRefreshToken(data.refreshToken);
                }
                return true;
            } else {
                this.logout();
                return false;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
            this.logout();
            return false;
        }
    }

    async validateToken(token = null) {
        try {
            const tokenToValidate = token || this.token;
            if (!tokenToValidate) {
                return { success: false, error: 'No token provided' };
            }

            const response = await this.makeRequest('/validate-token', {
                method: 'POST',
                body: JSON.stringify({ token: tokenToValidate })
            });

            const data = await response.json();
            return { success: response.ok, data };
        } catch (error) {
            return { success: false, error: 'Network error. Please try again.' };
        }
    }

    async logout() {
        try {
            if (this.token) {
                await this.makeRequest('/logout', { method: 'POST' });
            }
        } catch (error) {
            console.error('Logout request failed:', error);
        } finally {
            this.setToken(null);
            this.setRefreshToken(null);
            window.location.href = '/auth/login';
        }
    }

    // Utility methods
    isAuthenticated() {
        return !!this.token;
    }

    // UI helper methods
    showMessage(elementId, message, isError = false) {
        const element = document.getElementById(elementId);
        if (element) {
            const messageText = element.querySelector('.message-text');
            if (messageText) {
                messageText.textContent = message;
            } else {
                element.textContent = message;
            }
            element.className = `message ${isError ? 'error-message' : 'success-message'}`;
            element.classList.remove('hidden');
            
            // Auto-hide success messages after 5 seconds
            if (!isError) {
                setTimeout(() => {
                    element.classList.add('hidden');
                }, 5000);
            }
        }
    }

    hideMessage(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.add('hidden');
        }
    }

    setButtonLoading(buttonId, isLoading) {
        const button = document.getElementById(buttonId);
        if (!button) return;
        
        const btnText = button.querySelector('.btn-text');
        const btnLoader = button.querySelector('.btn-loader');
        
        if (isLoading) {
            button.disabled = true;
            if (btnText) btnText.classList.add('hidden');
            if (btnLoader) btnLoader.classList.remove('hidden');
        } else {
            button.disabled = false;
            if (btnText) btnText.classList.remove('hidden');
            if (btnLoader) btnLoader.classList.add('hidden');
        }
    }

    // Password strength checker
    checkPasswordStrength(password) {
        let strength = 0;
        let feedback = [];

        if (password.length >= 8) strength += 1;
        else feedback.push('At least 8 characters');

        if (/[a-z]/.test(password)) strength += 1;
        else feedback.push('Lowercase letter');

        if (/[A-Z]/.test(password)) strength += 1;
        else feedback.push('Uppercase letter');

        if (/\d/.test(password)) strength += 1;
        else feedback.push('Number');

        if (/[^A-Za-z0-9]/.test(password)) strength += 1;
        else feedback.push('Special character');

        const levels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
        const colors = ['#ff4757', '#ff6b7a', '#ffa726', '#66bb6a', '#4caf50'];

        return {
            score: strength,
            level: levels[strength] || 'Very Weak',
            color: colors[strength] || '#ff4757',
            feedback: feedback
        };
    }

    updatePasswordStrength(password) {
        const strength = this.checkPasswordStrength(password);
        const strengthFill = document.getElementById('strengthFill');
        const strengthText = document.getElementById('strengthText');

        if (strengthFill && strengthText) {
            const percentage = (strength.score / 5) * 100;
            strengthFill.style.width = `${percentage}%`;
            strengthFill.style.backgroundColor = strength.color;
            strengthText.textContent = password ? strength.level : 'Enter password';
            strengthText.style.color = strength.color;
        }
    }

    // Form validation
    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // Page initialization methods
    initLogin() {
        console.log('🔍 initLogin called');
        const loginForm = document.getElementById('loginForm');
        
        if (loginForm) {
            console.log('✅ Login form found');
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                console.log('📝 Login form submitted');
                
                const email = document.getElementById('email').value.trim();
                const password = document.getElementById('password').value;
                const rememberMe = document.getElementById('rememberMe')?.checked || false;

                // Hide previous messages
                this.hideMessage('loginError');
                this.hideMessage('loginSuccess');

                // Validation
                if (!email || !password) {
                    this.showMessage('loginError', 'Please fill in all fields', true);
                    return;
                }

                if (!this.validateEmail(email)) {
                    this.showMessage('loginError', 'Please enter a valid email address', true);
                    return;
                }

                // Show loading
                this.setButtonLoading('loginBtn', true);

                // Attempt login
                console.log('🔐 Attempting login...');
                const result = await this.login(email, password, rememberMe);
                console.log('Login result:', result);

                if (result.success) {
                    this.showMessage('loginSuccess', 'Login successful! Redirecting...');
                    
                    // Use backend redirect_url
                    const redirectUrl = result.data.redirect_url;
                    console.log('✅ Redirecting to:', redirectUrl);
                    
                    setTimeout(() => {
                        window.location.href = redirectUrl;
                    }, 1000);
                } else {
                    console.log('❌ Login failed:', result.error);
                    this.showMessage('loginError', result.error, true);
                    this.setButtonLoading('loginBtn', false);
                }
            });
        } else {
            console.log('❌ Login form NOT found');
        }
    }

    initRegister() {
        console.log('🔍 initRegister called');
        const registerForm = document.getElementById('registerForm');
        const passwordInput = document.getElementById('password');
        
        if (passwordInput) {
            passwordInput.addEventListener('input', (e) => {
                this.updatePasswordStrength(e.target.value);
            });
        }
        
        if (registerForm) {
            console.log('✅ Register form found');
            registerForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                console.log('📝 Register form submitted');
                
                const first_name = document.getElementById('first_name').value.trim();
                const last_name = document.getElementById('last_name').value.trim();
                const email = document.getElementById('email').value.trim();
                const password = document.getElementById('password').value;
                const confirmPassword = document.getElementById('confirmPassword').value;
                const agreeTerms = document.getElementById('agreeTerms')?.checked || false;
                const role = document.getElementById('role')?.value || 'adopter';
                const phone = document.getElementById('phone')?.value.trim() || '';
                const address = document.getElementById('address')?.value.trim() || '';

                // Hide previous messages
                this.hideMessage('registerError');
                this.hideMessage('registerSuccess');

                // Validation
                if (!first_name || !last_name || !email || !password || !confirmPassword) {
                    this.showMessage('registerError', 'Please fill in all required fields', true);
                    return;
                }

                if (!this.validateEmail(email)) {
                    this.showMessage('registerError', 'Please enter a valid email address', true);
                    return;
                }

                if (password !== confirmPassword) {
                    this.showMessage('registerError', 'Passwords do not match', true);
                    return;
                }

                const strength = this.checkPasswordStrength(password);
                if (strength.score < 3) {
                    this.showMessage('registerError', 'Please choose a stronger password', true);
                    return;
                }

                if (!agreeTerms) {
                    this.showMessage('registerError', 'Please agree to the terms and conditions', true);
                    return;
                }

                // Prepare user data
                const userData = { 
                    first_name, 
                    last_name, 
                    email, 
                    password,
                    role,
                    phone,
                    address
                };

                // Add shelter_id if role is shelter_staff
                if (role === 'shelter_staff') {
                    const shelter_id = document.getElementById('shelter_id')?.value;
                    console.log('🏠 Shelter ID before parsing:', shelter_id, 'Type:', typeof shelter_id);
                    
                    if (shelter_id && shelter_id !== '') {
                        userData.shelter_id = parseInt(shelter_id, 10);
                        console.log('🏠 Shelter ID after parsing:', userData.shelter_id);
                    }
                }

                // Show loading
                this.setButtonLoading('registerBtn', true);

                // Attempt registration
                console.log('📤 Sending registration data:', { ...userData, password: '***' });
                const result = await this.register(userData);
                console.log('📥 Registration result:', result);
                console.log('📥 Full result details:', JSON.stringify(result, null, 2));

                if (result.success) {
                    const isStaff = result.data.role === 'shelter_staff';
                    const message = isStaff 
                        ? 'Registration submitted! Admin will review your request. You will receive an email once approved.'
                        : 'Registration successful! Redirecting...';
                    
                    this.showMessage('registerSuccess', message);
                    
                    // Only redirect if not shelter_staff (they need approval first)
                    if (!isStaff) {
                        const redirectUrl = result.data.redirect_url || '/auth/login';
                        console.log('✅ Redirecting to:', redirectUrl);
                        
                        setTimeout(() => {
                            window.location.href = redirectUrl;
                        }, 1500);
                    }
                } else {
                    console.log('❌ Registration failed:', result.error);
                    this.showMessage('registerError', result.error, true);
                    this.setButtonLoading('registerBtn', false);
                }
            });
        } else {
            console.log('❌ Register form NOT found');
        }
    }
}

// Create global instance
const auth = new Auth();

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 DOM Content Loaded');
    const path = window.location.pathname;
    console.log('Current path:', path);

    if (path.includes('login')) {
        console.log('📍 On login page');
        auth.initLogin();
    } else if (path.includes('register')) {
        console.log('📍 On register page');
        auth.initRegister();
    }
});

// Export for use in other files
if (typeof window !== 'undefined') {
    window.Auth = Auth;
    window.auth = auth;
}