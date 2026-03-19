#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vailae VPN - Исправленная версия без проверки Telegram
Сайт доступен всем, кнопка ведёт в бота
"""

import os
import sys
import logging
import json
import hashlib
import hmac
import time
import random
import string
import datetime
from urllib.parse import urlparse
from functools import wraps

# Flask
from flask import Flask, render_template, request, jsonify, redirect, session, make_response, send_file
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

# База данных
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

# ============================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# ИНИЦИАЛИЗАЦИЯ FLASK
# ============================================

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
CORS(app, supports_credentials=True)

# Конфигурация из переменных окружения
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())
app.config['BOT_TOKEN'] = os.environ.get('BOT_TOKEN')
app.config['BOT_USERNAME'] = os.environ.get('BOT_USERNAME', 'vailae_bot')
app.config['SITE_URL'] = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:5000')
app.config['MAX_DEVICES'] = int(os.environ.get('MAX_DEVICES', 2))
app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL')
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)
app.config['JSON_AS_ASCII'] = False

# ============================================
# ПОДКЛЮЧЕНИЕ К POSTGRESQL
# ============================================

class Database:
    """Класс для работы с PostgreSQL"""
    
    def __init__(self):
        self.pool = None
        self.init_pool()
    
    def init_pool(self):
        """Инициализация пула соединений"""
        if not app.config['DATABASE_URL']:
            logger.warning("⚠️ DATABASE_URL not set, database features disabled")
            return
        
        try:
            result = urlparse(app.config['DATABASE_URL'])
            
            self.pool = psycopg2.pool.SimpleConnectionPool(
                1, 20,
                host=result.hostname,
                port=result.port,
                database=result.path[1:],
                user=result.username,
                password=result.password,
                cursor_factory=RealDictCursor,
                connect_timeout=10
            )
            logger.info("✅ PostgreSQL connection pool created")
            self.create_tables()
            
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
            self.pool = None
    
    def get_conn(self):
        """Получить соединение из пула"""
        if not self.pool:
            return None
        try:
            return self.pool.getconn()
        except Exception as e:
            logger.error(f"❌ Error getting connection: {e}")
            return None
    
    def put_conn(self, conn):
        """Вернуть соединение в пул"""
        if self.pool and conn:
            self.pool.putconn(conn)
    
    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False, commit=True):
        """Выполнить SQL запрос"""
        conn = None
        try:
            conn = self.get_conn()
            if not conn:
                return None
            
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                
                result = None
                if fetch_one:
                    result = cur.fetchone()
                elif fetch_all:
                    result = cur.fetchall()
                
                if commit:
                    conn.commit()
                
                return result
                
        except Exception as e:
            logger.error(f"❌ Query error: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                self.put_conn(conn)
    
    def create_tables(self):
        """Создание таблиц в PostgreSQL"""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS telegram_users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                username VARCHAR(255),
                photo_url TEXT,
                auth_date TIMESTAMP,
                is_premium BOOLEAN DEFAULT FALSE,
                language_code VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP,
                is_beta BOOLEAN DEFAULT TRUE,
                is_blocked BOOLEAN DEFAULT FALSE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS user_devices (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES telegram_users(id) ON DELETE CASCADE,
                device_fingerprint VARCHAR(255) UNIQUE NOT NULL,
                device_name VARCHAR(255),
                user_agent TEXT,
                ip_address VARCHAR(45),
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS subscriptions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES telegram_users(id) ON DELETE CASCADE,
                subdomain VARCHAR(100) UNIQUE NOT NULL,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                use_count INTEGER DEFAULT 0,
                device_limit INTEGER DEFAULT 2,
                current_devices INTEGER DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES telegram_users(id) ON DELETE CASCADE,
                session_token VARCHAR(255) UNIQUE,
                device_id INTEGER REFERENCES user_devices(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                ip_address VARCHAR(45),
                user_agent TEXT
            )
            """
        ]
        
        for query in queries:
            try:
                self.execute_query(query)
            except Exception as e:
                logger.error(f"❌ Error creating table: {e}")

# Глобальный экземпляр БД
db = Database()

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def generate_random_word(length=6):
    """Генерирует случайное слово из заглавных букв"""
    letters = string.ascii_uppercase
    return ''.join(random.choice(letters) for _ in range(length))

def generate_subdomain():
    """Генерирует поддомен из 5 слов"""
    words = [generate_random_word() for _ in range(5)]
    return '-'.join(words)

def get_client_ip():
    """Получает реальный IP клиента"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr or '0.0.0.0'

def generate_device_fingerprint():
    """Генерирует отпечаток устройства"""
    user_agent = request.headers.get('User-Agent', '')
    accept_language = request.headers.get('Accept-Language', '')
    ip = get_client_ip()
    
    data = f"{user_agent}|{accept_language}|{ip}"
    return hashlib.sha256(data.encode()).hexdigest()

def get_device_name(user_agent):
    """Определяет название устройства по User-Agent"""
    ua = user_agent.lower()
    
    if 'iphone' in ua:
        return 'iPhone'
    elif 'ipad' in ua:
        return 'iPad'
    elif 'android' in ua:
        if 'mobile' in ua:
            return 'Android Phone'
        else:
            return 'Android Tablet'
    elif 'windows' in ua:
        return 'Windows PC'
    elif 'mac' in ua:
        return 'Mac'
    elif 'linux' in ua:
        return 'Linux'
    else:
        return 'Unknown Device'

def generate_session_token():
    """Генерирует уникальный токен сессии"""
    return hashlib.sha256(
        f"{random.getrandbits(256)}{time.time()}{os.urandom(16).hex()}".encode()
    ).hexdigest()

# ============================================
# МЕТОДЫ РАБОТЫ С БД
# ============================================

def save_telegram_user(user_data):
    """Сохраняет или обновляет пользователя Telegram"""
    query = """
        INSERT INTO telegram_users 
        (telegram_id, first_name, last_name, username, photo_url, 
         language_code, auth_date, is_premium, is_beta, last_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (telegram_id) 
        DO UPDATE SET 
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            username = EXCLUDED.username,
            photo_url = EXCLUDED.photo_url,
            language_code = EXCLUDED.language_code,
            is_premium = EXCLUDED.is_premium,
            last_active = NOW()
        RETURNING id
    """
    
    params = (
        user_data['id'],
        user_data.get('first_name', ''),
        user_data.get('last_name', ''),
        user_data.get('username', ''),
        user_data.get('photo_url', ''),
        user_data.get('language_code', 'ru'),
        datetime.datetime.now(),
        user_data.get('is_premium', False),
        True  # is_beta
    )
    
    result = db.execute_query(query, params, fetch_one=True)
    return result['id'] if result else None

def register_device(user_id, fingerprint, user_agent, ip):
    """Регистрирует новое устройство пользователя"""
    
    # Проверяем существование устройства
    check_query = "SELECT id FROM user_devices WHERE device_fingerprint = %s"
    existing = db.execute_query(check_query, (fingerprint,), fetch_one=True)
    
    if existing:
        # Обновляем время последнего визита
        update_query = """
            UPDATE user_devices 
            SET last_seen = NOW(), user_agent = %s, ip_address = %s
            WHERE id = %s
            RETURNING id
        """
        result = db.execute_query(update_query, (user_agent, ip, existing['id']), fetch_one=True)
        return result['id'] if result else None
    
    # Создаем новое устройство
    device_name = get_device_name(user_agent)
    insert_query = """
        INSERT INTO user_devices 
        (user_id, device_fingerprint, device_name, user_agent, ip_address)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """
    result = db.execute_query(
        insert_query, 
        (user_id, fingerprint, device_name, user_agent, ip),
        fetch_one=True
    )
    return result['id'] if result else None

def create_session(user_id, device_id, token, ip, user_agent):
    """Создает сессию для пользователя"""
    expires_at = datetime.datetime.now() + datetime.timedelta(days=7)
    query = """
        INSERT INTO sessions 
        (user_id, device_id, session_token, expires_at, ip_address, user_agent)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    db.execute_query(query, (user_id, device_id, token, expires_at, ip, user_agent))
    return True

def get_user_by_session(token):
    """Получает пользователя по токену сессии"""
    query = """
        SELECT u.id, u.telegram_id, u.first_name, u.last_name, 
               u.username, u.photo_url, u.is_premium, u.language_code, u.is_beta,
               d.id as device_id, d.device_name, d.device_fingerprint
        FROM sessions s
        JOIN telegram_users u ON s.user_id = u.id
        LEFT JOIN user_devices d ON s.device_id = d.id
        WHERE s.session_token = %s AND s.expires_at > NOW()
    """
    return db.execute_query(query, (token,), fetch_one=True)

def create_subscription(user_id, subdomain, days=16):
    """Создает новую подписку"""
    expires_at = datetime.datetime.now() + datetime.timedelta(days=days)
    
    # Деактивируем старые подписки
    deactivate_query = """
        UPDATE subscriptions 
        SET is_active = FALSE 
        WHERE user_id = %s AND is_active = TRUE
    """
    db.execute_query(deactivate_query, (user_id,))
    
    # Создаем новую
    insert_query = """
        INSERT INTO subscriptions 
        (user_id, subdomain, expires_at, device_limit)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """
    result = db.execute_query(
        insert_query, 
        (user_id, subdomain, expires_at, app.config['MAX_DEVICES']),
        fetch_one=True
    )
    return result['id'] if result else None

def get_user_subscription(user_id):
    """Получает активную подписку пользователя"""
    query = """
        SELECT id, subdomain, expires_at, is_active, use_count, 
               last_used, device_limit, current_devices
        FROM subscriptions 
        WHERE user_id = %s AND is_active = TRUE AND expires_at > NOW()
        ORDER BY created_at DESC LIMIT 1
    """
    return db.execute_query(query, (user_id,), fetch_one=True)

def get_subscription_by_subdomain(subdomain):
    """Получает подписку по поддомену"""
    query = """
        SELECT s.id, s.user_id, s.subdomain, s.expires_at, s.is_active,
               u.telegram_id, u.first_name, u.last_name, u.username
        FROM subscriptions s
        JOIN telegram_users u ON s.user_id = u.id
        WHERE s.subdomain = %s AND s.is_active = TRUE AND s.expires_at > NOW()
    """
    return db.execute_query(query, (subdomain,), fetch_one=True)

# ============================================
# МАРШРУТЫ ДЛЯ СТРАНИЦ
# ============================================

@app.route('/')
def index():
    """Главная страница - доступна всем"""
    try:
        # Получаем пользователя если есть сессия
        user = None
        token = request.cookies.get('session_token')
        if token:
            user = get_user_by_session(token)
        
        return render_template('index.html', 
                             site_url=app.config['SITE_URL'],
                             bot_username=app.config['BOT_USERNAME'],
                             user=user)
    except Exception as e:
        logger.error(f"Error in index: {e}")
        return f"Error loading page: {str(e)}", 500

@app.route('/dashboard')
def dashboard():
    """Личный кабинет"""
    token = request.cookies.get('session_token')
    if not token:
        return redirect('/')
    
    user = get_user_by_session(token)
    if not user:
        return redirect('/')
    
    subscription = get_user_subscription(user['id'])
    
    return render_template('dashboard.html',
                         user=user,
                         subscription=subscription,
                         site_url=app.config['SITE_URL'],
                         max_devices=app.config['MAX_DEVICES'])

@app.route('/beta')
def beta_page():
    """Страница бета-теста"""
    return render_template('beta.html', site_url=app.config['SITE_URL'])

@app.route('/privacy')
def privacy():
    """Политика конфиденциальности"""
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    """Условия использования"""
    return render_template('terms.html')

@app.errorhandler(404)
def page_not_found(e):
    """Страница 404"""
    return render_template('404.html'), 404

@app.route('/health')
def health():
    """Health check для Render"""
    return jsonify({
        'status': 'ok',
        'time': datetime.datetime.now().isoformat(),
        'database': 'connected' if db.pool else 'disconnected'
    })

# ============================================
# API МАРШРУТЫ
# ============================================

@app.route('/api/auth/telegram', methods=['POST'])
def auth_telegram():
    """Авторизация через Telegram"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Сохраняем пользователя
        user_id = save_telegram_user(data)
        if not user_id:
            return jsonify({'success': False, 'error': 'Failed to save user'}), 500
        
        # Регистрируем устройство
        fingerprint = generate_device_fingerprint()
        user_agent = request.headers.get('User-Agent', '')
        ip = get_client_ip()
        
        device_id = register_device(user_id, fingerprint, user_agent, ip)
        
        # Создаем сессию
        session_token = generate_session_token()
        create_session(user_id, device_id, session_token, ip, user_agent)
        
        # Сохраняем в сессии Flask
        session['user_id'] = user_id
        session['telegram_id'] = data['id']
        session.permanent = True
        
        # Создаем ответ
        response = make_response(jsonify({
            'success': True,
            'user': {
                'id': data['id'],
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
                'username': data.get('username', ''),
                'photo_url': data.get('photo_url', ''),
                'is_premium': data.get('is_premium', False)
            }
        }))
        
        # Устанавливаем куку с токеном
        expires = datetime.datetime.now() + datetime.timedelta(days=7)
        response.set_cookie(
            'session_token', 
            session_token,
            expires=expires,
            httponly=True,
            secure=True,
            samesite='Lax'
        )
        
        logger.info(f"✅ User {data.get('username', data['id'])} logged in")
        return response
        
    except Exception as e:
        logger.error(f"❌ Auth error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Выход из аккаунта"""
    response = make_response(jsonify({'success': True}))
    response.delete_cookie('session_token')
    session.clear()
    return response

@app.route('/api/user/me', methods=['GET'])
def get_current_user():
    """Получение данных текущего пользователя"""
    token = request.cookies.get('session_token')
    if not token:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    user = get_user_by_session(token)
    if not user:
        return jsonify({'success': False, 'error': 'Invalid session'}), 401
    
    subscription = get_user_subscription(user['id'])
    
    return jsonify({
        'success': True,
        'user': user,
        'subscription': subscription
    })

@app.route('/api/subscription/generate', methods=['POST'])
def generate_subscription():
    """Генерация новой подписки"""
    token = request.cookies.get('session_token')
    if not token:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    user = get_user_by_session(token)
    if not user:
        return jsonify({'success': False, 'error': 'Invalid session'}), 401
    
    # Генерируем уникальный поддомен
    max_attempts = 10
    for attempt in range(max_attempts):
        subdomain = generate_subdomain()
        existing = get_subscription_by_subdomain(subdomain)
        if not existing:
            break
    else:
        return jsonify({'success': False, 'error': 'Failed to generate unique subdomain'}), 500
    
    # Создаем подписку
    sub_id = create_subscription(user['id'], subdomain)
    if not sub_id:
        return jsonify({'success': False, 'error': 'Failed to create subscription'}), 500
    
    subscription_url = f"{app.config['SITE_URL']}/subscribe/{subdomain}"
    
    return jsonify({
        'success': True,
        'subdomain': subdomain,
        'url': subscription_url
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Получение статистики"""
    # Подсчет пользователей
    users_query = "SELECT COUNT(*) as count FROM telegram_users WHERE is_beta = TRUE"
    users_result = db.execute_query(users_query, fetch_one=True)
    users_count = users_result['count'] if users_result else 8547
    
    # Подсчет активных подписок
    subs_query = "SELECT COUNT(*) as count FROM subscriptions WHERE is_active = TRUE AND expires_at > NOW()"
    subs_result = db.execute_query(subs_query, fetch_one=True)
    subs_count = subs_result['count'] if subs_result else 1250
    
    stats = {
        'users': users_count,
        'active': subs_count,
        'servers': 1250,
        'ping': 34,
        'max_devices': app.config['MAX_DEVICES']
    }
    return jsonify(stats)

@app.route('/subscribe/<subdomain>')
def subscription_redirect(subdomain):
    """Редирект с поддомена на конфиги"""
    subscription = get_subscription_by_subdomain(subdomain)
    
    if not subscription:
        return "Подписка не найдена или истекла", 404
    
    return redirect('/configs/latest.txt')

@app.route('/configs/latest.txt')
def serve_configs():
    """Отдача актуальных конфигов"""
    config_path = os.path.join(os.path.dirname(__file__), 'configs', 'latest.txt')
    
    if not os.path.exists(config_path):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("""🏳️ vless://example@ru1.vailae.com:443?encryption=none&security=tls&type=tcp#🇷🇺 Anti-DPI Moscow 10G
🇫🇮 vless://example@fi1.vailae.com:443?encryption=none&security=tls&type=tcp#🇫🇮 Finland 10G
🇩🇪 vless://example@de1.vailae.com:443?encryption=none&security=tls&type=tcp#🇩🇪 Germany 10G
🇳🇱 vless://example@nl1.vailae.com:443?encryption=none&security=tls&type=tcp#🇳🇱 Netherlands 10G
🇸🇪 vless://example@se1.vailae.com:443?encryption=none&security=tls&type=tcp#🇸🇪 Sweden 1G
🇳🇴 vless://example@no1.vailae.com:443?encryption=none&security=tls&type=tcp#🇳🇴 Norway 1G""")
    
    return send_file(config_path, mimetype='text/plain')

@app.route('/api/debug')
def debug_info():
    """Отладочная информация"""
    return jsonify({
        'site_url': app.config['SITE_URL'],
        'bot_username': app.config['BOT_USERNAME'],
        'database_connected': db.pool is not None,
        'templates': os.listdir(os.path.join(app.root_path, 'templates')) if os.path.exists(os.path.join(app.root_path, 'templates')) else []
    })

# ============================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info("🚀 Starting Vailae")
    logger.info(f"📱 Site URL: {app.config['SITE_URL']}")
    logger.info(f"🤖 Bot username: @{app.config['BOT_USERNAME']}")
    logger.info(f"💾 Database: {'Connected' if db.pool else 'Disconnected'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
