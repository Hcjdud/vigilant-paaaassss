// static/js/main.js - Полная версия

// ===== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ =====
let charts = {};
let statsInterval;
let particlesInitialized = false;

// ===== ИНИЦИАЛИЗАЦИЯ =====
document.addEventListener('DOMContentLoaded', () => {
    initPreloader();
    initNavbar();
    initParticles();
    initCharts();
    initStats();
    initFaq();
    initAnimations();
    initSubscription();
});

// ===== ПРЕЛОАДЕР =====
function initPreloader() {
    const preloader = document.getElementById('preloader');
    if (preloader) {
        setTimeout(() => {
            preloader.classList.add('hidden');
        }, 1000);
    }
}

// ===== НАВИГАЦИЯ =====
function initNavbar() {
    const menuToggle = document.getElementById('menuToggle');
    const navMenu = document.querySelector('.nav-menu');
    const navbar = document.getElementById('navbar');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            menuToggle.classList.toggle('active');
            navMenu.classList.toggle('active');
        });
    }
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.style.background = 'rgba(3, 7, 18, 0.95)';
            navbar.style.backdropFilter = 'blur(12px)';
        } else {
            navbar.style.background = 'rgba(3, 7, 18, 0.8)';
        }
    });
    
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            menuToggle?.classList.remove('active');
            navMenu?.classList.remove('active');
        });
    });
}

// ===== ЧАСТИЦЫ НА ФОНЕ =====
function initParticles() {
    if (particlesInitialized) return;
    
    const canvas = document.getElementById('canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    let width, height;
    let particles = [];
    
    function resize() {
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = width;
        canvas.height = height;
    }
    
    function createParticles() {
        particles = [];
        for (let i = 0; i < 50; i++) {
            particles.push({
                x: Math.random() * width,
                y: Math.random() * height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                size: Math.random() * 2 + 1,
                color: `rgba(99, 102, 241, ${Math.random() * 0.5})`
            });
        }
    }
    
    function draw() {
        ctx.clearRect(0, 0, width, height);
        
        particles.forEach(p => {
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.fill();
            
            p.x += p.vx;
            p.y += p.vy;
            
            if (p.x < 0) p.x = width;
            if (p.x > width) p.x = 0;
            if (p.y < 0) p.y = height;
            if (p.y > height) p.y = 0;
        });
        
        requestAnimationFrame(draw);
    }
    
    window.addEventListener('resize', () => {
        resize();
        createParticles();
    });
    
    resize();
    createParticles();
    draw();
    
    particlesInitialized = true;
}

// ===== ГРАФИКИ =====
function initCharts() {
    if (typeof Chart === 'undefined') return;
    
    const usersCtx = document.getElementById('usersChart');
    if (usersCtx) {
        charts.users = new Chart(usersCtx, {
            type: 'line',
            data: {
                labels: ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
                datasets: [{
                    data: [6500, 7200, 8100, 7900, 8500, 8300, 8547],
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { display: false }, y: { display: false } }
            }
        });
    }
    
    const pingCtx = document.getElementById('pingChart');
    if (pingCtx) {
        charts.ping = new Chart(pingCtx, {
            type: 'line',
            data: {
                labels: ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
                datasets: [{
                    data: [42, 38, 35, 36, 34, 33, 34],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { display: false }, y: { display: false } }
            }
        });
    }
    
    const serversCtx = document.getElementById('serversChart');
    if (serversCtx) {
        charts.servers = new Chart(serversCtx, {
            type: 'line',
            data: {
                labels: ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
                datasets: [{
                    data: [980, 1050, 1120, 1180, 1220, 1240, 1250],
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { display: false }, y: { display: false } }
            }
        });
    }
}

// ===== СТАТИСТИКА =====
function initStats() {
    updateStats();
    statsInterval = setInterval(updateStats, 5000);
}

async function updateStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        animateNumber('userCount', stats.users || 8547, 1500);
        animateNumber('pingValue', stats.ping || 34, 1500);
        animateNumber('serverCount', stats.servers || 1250, 1500);
        animateNumber('betaCounter', stats.users || 8547, 1500);
        
        if (document.getElementById('betaUsers')) {
            animateNumber('betaUsers', stats.users || 8547, 1500);
        }
        if (document.getElementById('betaLeft')) {
            animateNumber('betaLeft', 10000 - (stats.users || 8547), 1500);
        }
        
        const progressThumb = document.querySelector('.progress-thumb');
        if (progressThumb) {
            const progress = ((stats.users || 8547) / 10000) * 100;
            progressThumb.style.width = `${progress}%`;
        }
        
        if (charts.users) {
            charts.users.data.datasets[0].data = [
                Math.floor(6500 + Math.random() * 2000),
                Math.floor(7200 + Math.random() * 2000),
                Math.floor(8100 + Math.random() * 1000),
                Math.floor(7900 + Math.random() * 1500),
                Math.floor(8500 + Math.random() * 500),
                Math.floor(8300 + Math.random() * 700),
                stats.users || 8547
            ];
            charts.users.update();
        }
        
        if (charts.ping) {
            charts.ping.data.datasets[0].data = [
                Math.floor(40 + Math.random() * 10),
                Math.floor(38 + Math.random() * 8),
                Math.floor(35 + Math.random() * 7),
                Math.floor(36 + Math.random() * 6),
                Math.floor(34 + Math.random() * 5),
                Math.floor(33 + Math.random() * 5),
                stats.ping || 34
            ];
            charts.ping.update();
        }
        
        if (charts.servers) {
            charts.servers.data.datasets[0].data = [
                Math.floor(980 + Math.random() * 100),
                Math.floor(1050 + Math.random() * 80),
                Math.floor(1120 + Math.random() * 60),
                Math.floor(1180 + Math.random() * 50),
                Math.floor(1220 + Math.random() * 40),
                Math.floor(1240 + Math.random() * 30),
                stats.servers || 1250
            ];
            charts.servers.update();
        }
        
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

function animateNumber(elementId, target, duration) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const start = parseInt(element.textContent.replace(/,/g, '')) || 0;
    const increment = (target - start) / (duration / 16);
    let current = start;
    
    function step() {
        current += increment;
        if ((increment > 0 && current >= target) || (increment < 0 && current <= target)) {
            element.textContent = target.toLocaleString();
            return;
        }
        element.textContent = Math.floor(current).toLocaleString();
        requestAnimationFrame(step);
    }
    
    requestAnimationFrame(step);
}

// ===== FAQ =====
function initFaq() {
    document.querySelectorAll('.faq-item').forEach(item => {
        const question = item.querySelector('.faq-question');
        question?.addEventListener('click', () => {
            const isActive = item.classList.contains('active');
            document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('active'));
            if (!isActive) item.classList.add('active');
        });
    });
}

function toggleFaq(element) {
    const item = element.closest('.faq-item');
    item?.classList.toggle('active');
}

// ===== ПОДПИСКА =====
function initSubscription() {
    setTimeout(() => {
        generateNewSubscription();
    }, 1000);
}

function generateRandomWord(length = 6) {
    const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    return Array.from({ length }, () => letters[Math.floor(Math.random() * letters.length)]).join('');
}

async function generateNewSubscription() {
    try {
        const response = await fetch('/api/subscription/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            const linkInput = document.getElementById('subscriptionLink');
            if (linkInput) {
                linkInput.value = data.url;
            }
            
            showNotification('✨ Новая подписка сгенерирована!', 'success');
        } else {
            showNotification('❌ Ошибка генерации подписки', 'error');
        }
    } catch (error) {
        console.error('Generate error:', error);
        showNotification('❌ Ошибка сервера', 'error');
    }
}

function copySubscriptionLink() {
    const input = document.getElementById('subscriptionLink');
    if (!input) return;
    
    input.select();
    document.execCommand('copy');
    
    showNotification('📋 Ссылка скопирована!', 'success');
    
    const copyBtn = document.querySelector('.copy-btn');
    if (copyBtn) {
        copyBtn.style.transform = 'scale(0.9)';
        setTimeout(() => {
            copyBtn.style.transform = 'scale(1)';
        }, 200);
    }
}

// ===== УВЕДОМЛЕНИЯ =====
function showNotification(message, type = 'success') {
    const container = document.getElementById('notificationContainer');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    let icon = 'check-circle';
    if (type === 'error') icon = 'exclamation-circle';
    if (type === 'warning') icon = 'exclamation-triangle';
    
    notification.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideIn 0.3s reverse';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ===== АНИМАЦИИ =====
function initAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.feature-card, .beta-feature, .faq-item, .stat-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'all 0.6s ease';
        observer.observe(el);
    });
}

// ===== ОЧИСТКА =====
window.addEventListener('beforeunload', () => {
    if (statsInterval) clearInterval(statsInterval);
});
