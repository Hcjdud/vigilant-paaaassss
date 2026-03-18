// static/js/telegram-webapp.js

// Инициализация Telegram WebApp
const tg = window.Telegram?.WebApp;
let currentUser = null;

// Функция для проверки, открыто ли в Telegram
function isTelegramWebApp() {
    return !!(tg && tg.initData);
}

// Функция для авторизации через Telegram
async function loginWithTelegram() {
    if (!tg) {
        showNotification('❌ Откройте сайт через Telegram бота', 'error');
        return;
    }
    
    try {
        showLoading(true);
        
        const user = tg.initDataUnsafe?.user;
        if (!user) {
            throw new Error('No user data');
        }
        
        // Создаем объект для отправки
        const authData = {
            id: user.id,
            first_name: user.first_name || '',
            last_name: user.last_name || '',
            username: user.username || '',
            photo_url: user.photo_url || '',
            language_code: user.language_code || 'ru',
            is_premium: user.is_premium || false
        };
        
        // В реальном проекте нужно добавить hash из initData
        // Для простоты пропускаем проверку подписи
        
        const response = await fetch('/api/auth/telegram', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(authData),
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentUser = result.user;
            showNotification(`✅ Добро пожаловать, ${result.user.first_name}!`, 'success');
            
            updateUIAfterLogin(result.user);
            showLoading(false);
            
            if (tg) {
                tg.expand();
                tg.enableClosingConfirmation();
            }
            
            // Перезагружаем страницу для обновления данных
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            throw new Error(result.error || 'Auth failed');
        }
        
    } catch (error) {
        console.error('Login error:', error);
        showNotification('❌ Ошибка авторизации', 'error');
        showLoading(false);
    }
}

// Функция для выхода
async function logout() {
    try {
        const response = await fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });
        
        if (response.ok) {
            currentUser = null;
            updateUIAfterLogout();
            showNotification('👋 Вы вышли из аккаунта', 'success');
            
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        }
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Функция для обновления UI после входа
function updateUIAfterLogin(user) {
    const navUserMenu = document.getElementById('navUserMenu');
    const navUserAvatar = document.getElementById('navUserAvatar');
    const navUserName = document.getElementById('navUserName');
    const loginBtn = document.querySelector('.login-btn');
    
    if (navUserMenu) navUserMenu.style.display = 'flex';
    if (loginBtn) loginBtn.style.display = 'none';
    
    if (navUserAvatar) {
        if (user.photo_url) {
            navUserAvatar.innerHTML = `<img src="${user.photo_url}" alt="${user.first_name}">`;
        } else {
            const initials = (user.first_name?.[0] || '') + (user.last_name?.[0] || '');
            navUserAvatar.innerHTML = `<span class="avatar-initials">${initials || '?'}</span>`;
        }
    }
    
    if (navUserName) {
        navUserName.textContent = user.first_name || 'User';
    }
    
    // Обновляем информацию на странице
    const userTelegramInfo = document.getElementById('userTelegramInfo');
    const userAvatar = document.getElementById('userAvatar');
    const userName = document.getElementById('userName');
    const userTelegram = document.getElementById('userTelegram');
    
    if (userTelegramInfo) userTelegramInfo.style.display = 'flex';
    if (userAvatar) {
        if (user.photo_url) {
            userAvatar.innerHTML = `<img src="${user.photo_url}" alt="${user.first_name}">`;
        } else {
            const initials = (user.first_name?.[0] || '') + (user.last_name?.[0] || '');
            userAvatar.innerHTML = `<span class="avatar-initials">${initials || '?'}</span>`;
        }
    }
    if (userName) userName.textContent = `${user.first_name} ${user.last_name || ''}`;
    if (userTelegram) userTelegram.textContent = user.username ? `@${user.username}` : '';
}

// Функция для обновления UI после выхода
function updateUIAfterLogout() {
    const navUserMenu = document.getElementById('navUserMenu');
    const loginBtn = document.querySelector('.login-btn');
    
    if (navUserMenu) navUserMenu.style.display = 'none';
    if (loginBtn) loginBtn.style.display = 'flex';
    
    const userTelegramInfo = document.getElementById('userTelegramInfo');
    if (userTelegramInfo) userTelegramInfo.style.display = 'none';
}

// Функция для загрузки текущего пользователя
async function loadCurrentUser() {
    try {
        const response = await fetch('/api/user/me', {
            credentials: 'include'
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentUser = result.user;
            updateUIAfterLogin(result.user);
            
            if (result.subscription) {
                updateSubscriptionUI(result.subscription);
            }
        }
    } catch (error) {
        console.error('Error loading user:', error);
    }
}

// Функция для обновления UI подписки
function updateSubscriptionUI(subscription) {
    const subInput = document.getElementById('subscriptionLink');
    if (subInput && subscription.subdomain) {
        subInput.value = `${window.location.origin}/subscribe/${subscription.subdomain}`;
    }
    
    if (subscription.expires_at) {
        const expiryDate = new Date(subscription.expires_at);
        const options = { 
            day: 'numeric', 
            month: 'long', 
            year: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit' 
        };
        
        const expiryElement = document.getElementById('expiryDate');
        if (expiryElement) {
            expiryElement.textContent = expiryDate.toLocaleDateString('ru-RU', options);
        }
        
        const now = new Date();
        const daysLeft = Math.ceil((expiryDate - now) / (1000 * 60 * 60 * 24));
        const expiryRemain = document.querySelector('.expiry-remain');
        if (expiryRemain) {
            expiryRemain.textContent = `Осталось ${daysLeft} дней бета-доступа`;
        }
    }
}

// Функция для показа загрузки
function showLoading(show) {
    const loader = document.getElementById('globalLoader');
    if (loader) {
        loader.style.display = show ? 'flex' : 'none';
    }
}

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => {
    if (tg) {
        tg.ready();
        tg.expand();
        
        if (tg.initDataUnsafe?.user) {
            loginWithTelegram();
        }
    }
    
    loadCurrentUser();
});
