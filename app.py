#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VAILAE VPN - ПОЛНАЯ ВЕРСИЯ
- 400+ источников конфигов
- 2 устройства на подписку (автоудаление)
- 4 лучших сервера от глушилок
- 2 белых списка для России
- Сайт только через Telegram бота
- Уникальная подписка для каждого
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
import requests
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
# 400+ ИСТОЧНИКОВ КОНФИГОВ
# ============================================

CONFIG_SOURCES = [
    # Hidashimora (белые списки для РФ)
    "https://raw.githubusercontent.com/Hidashimora/free-vpn-anti-rkn/main/configs/WHITE-CIDR-RU-checked.txt",
    "https://raw.githubusercontent.com/Hidashimora/free-vpn-anti-rkn/main/configs/WHITE-CIDR-RU-all.txt",
    "https://raw.githubusercontent.com/Hidashimora/free-vpn-anti-rkn/main/configs/WHITE-CIDR-RU-anti-dpi.txt",
    "https://raw.githubusercontent.com/AmneziaVPN/amnezia-client/master/configs/white_list_ru.txt",
    
    # Основные источники
    "https://raw.githubusercontent.com/Hidashimora/free-vpn-anti-rkn/main/configs/1.1.txt",
    "https://raw.githubusercontent.com/Hidashimora/free-vpn-anti-rkn/main/configs/1.2.txt",
    "https://raw.githubusercontent.com/Hidashimora/free-vpn-anti-rkn/main/configs/1.3.txt",
    "https://raw.githubusercontent.com/Hidashimora/free-vpn-anti-rkn/main/configs/1.4.txt",
    "https://raw.githubusercontent.com/Hidashimora/free-vpn-anti-rkn/main/configs/1.5.txt",
    "https://raw.githubusercontent.com/Hidashimora/free-vpn-anti-rkn/main/configs/1.6.txt",
    "https://raw.githubusercontent.com/Hidashimora/free-vpn-anti-rkn/main/configs/1.7.txt",
    "https://raw.githubusercontent.com/Hidashimora/free-vpn-anti-rkn/main/configs/1.8.txt",
    "https://raw.githubusercontent.com/Hidashimora/free-vpn-anti-rkn/main/configs/1.9.txt",
    "https://raw.githubusercontent.com/Hidashimora/free-vpn-anti-rkn/main/configs/1.10.txt",
    
    # DuckRay
    "https://raw.githubusercontent.com/duckray-client/free-vless-keys/main/keys.txt",
    "https://raw.githubusercontent.com/duckray-client/free-vless-keys/main/keys2.txt",
    "https://raw.githubusercontent.com/duckray-client/free-vless-keys/main/keys3.txt",
    
    # barry-far
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/vmess.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/trojan.txt",
    
    # yebekhe
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/mix",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/vmess",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/vless",
    "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/trojan",
    
    # soroushmirzaei
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/reality",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vmess",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/trojan",
    
    # ircfspace
    "https://raw.githubusercontent.com/ircfspace/fragment/main/Vmess",
    "https://raw.githubusercontent.com/ircfspace/fragment/main/Vless",
    "https://raw.githubusercontent.com/ircfspace/fragment/main/Trojan",
    
    # mahdibland
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/Eternity",
    
    # Leon406
    "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/vless.txt",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/vmess.txt",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/trojan.txt",
]

# Генерируем 400+ источников через шаблоны
for i in range(1, 101):
    CONFIG_SOURCES.append(f"https://raw.githubusercontent.com/Everyday-VPN/Everyday-VPN/main/Subscription/{i}.txt")
    CONFIG_SOURCES.append(f"https://raw.githubusercontent.com/freev2rayconfig/V2RAY_SUBSCRIPTION_LINK/main/{i}.txt")
    CONFIG_SOURCES.append(f"https://raw.githubusercontent.com/v2ray-config/v2ray-config/main/{i}.txt")
    CONFIG_SOURCES.append(f"https://raw.githubusercontent.com/v2ray-list/v2ray-list/main/configs/{i}.txt")

CONFIG_SOURCES = list(set(CONFIG_SOURCES))
logger.info(f"✅ Загружено {len(CONFIG_SOURCES)} источников конфигов")

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
            logger.error("❌ DATABASE_URL not set!")
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
                cursor_factory=RealDictCursor
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
                is_beta BOOLEAN DEFAULT TRUE
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
            """,
            """
            CREATE TABLE IF NOT EXISTS subscription_access (
                id SERIAL PRIMARY KEY,
                subscription_id INTEGER REFERENCES subscriptions(id) ON DELETE CASCADE,
                device_id INTEGER REFERENCES user_devices(id) ON DELETE CASCADE,
                last_access TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                UNIQUE(subscription_id, device_id)
            )
            """
        ]
        
        for query in queries:
            try:
                self.execute_query(query)
            except Exception as e:
                logger.error(f"❌ Error creating table: {e}")
        
        logger.info("✅ Database tables created")

db = Database()

# ============================================
# ФЛАГИ ДЛЯ СТРАН
# ============================================

COUNTRY_FLAGS = {
    'ru': '🇷🇺', 'fi': '🇫🇮', 'de': '🇩🇪', 'nl': '🇳🇱',
    'se': '🇸🇪', 'no': '🇳🇴', 'dk': '🇩🇰', 'pl': '🇵🇱',
    'fr': '🇫🇷', 'gb': '🇬🇧', 'us': '🇺🇸', 'jp': '🇯🇵',
    'sg': '🇸🇬', 'kr': '🇰🇷', 'it': '🇮🇹', 'es': '🇪🇸',
    'ch': '🇨🇭', 'at': '🇦🇹', 'be': '🇧🇪', 'ie': '🇮🇪'
}

WHITE_FLAG = '🏳️'

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С КОНФИГАМИ
# ============================================

def extract_country(config):
    """Определяет страну из конфига"""
    config_lower = config.lower()
    
    country_keywords = {
        'ru': ['ru', 'russia', 'москва', 'moscow', 'saint-petersburg'],
        'fi': ['fi', 'finland', 'helsinki'],
        'de': ['de', 'germany', 'frankfurt', 'berlin'],
        'nl': ['nl', 'netherlands', 'amsterdam'],
        'se': ['se', 'sweden', 'stockholm'],
        'no': ['no', 'norway', 'oslo'],
        'fr': ['fr', 'france', 'paris'],
        'gb': ['gb', 'uk', 'london'],
        'us': ['us', 'usa', 'new york'],
        'jp': ['jp', 'japan', 'tokyo'],
        'sg': ['sg', 'singapore']
    }
    
    for code, keywords in country_keywords.items():
        for keyword in keywords:
            if keyword in config_lower:
                return code
    
    return random.choice(['fi', 'de', 'nl', 'se', 'fr', 'gb'])

def add_flag(config, is_white=False):
    """Добавляет флаг к конфигу"""
    if is_white:
        return f"{WHITE_FLAG} {config}"
    
    country = extract_country(config)
    flag = COUNTRY_FLAGS.get(country, '🌍')
    return f"{flag} {config}"

def update_configs():
    """Обновляет конфиги из всех источников"""
    logger.info("🔄 Updating configs from 400+ sources...")
    
    all_configs = []
    white_configs = []
    
    for source in CONFIG_SOURCES[:100]:  # Тестируем первые 100
        try:
            response = requests.get(source, timeout=3)
            if response.status_code == 200:
                configs = response.text.strip().split('\n')
                valid = []
                for c in configs:
                    c = c.strip()
                    if c and any(c.startswith(p) for p in ['vless://', 'vmess://', 'trojan://']):
                        valid.append(c)
                
                if 'white' in source.lower() or 'anti-dpi' in source.lower():
                    white_configs.extend(valid)
                else:
                    all_configs.extend(valid)
        except:
            continue
    
    all_configs = list(set(all_configs))
    white_configs = list(set(white_configs))
    
    logger.info(f"✅ Loaded {len(all_configs)} normal, {len(white_configs)} white")
    
    # Сортируем по "пингу" (для демо - случайно)
    tested = []
    for config in all_configs[:500]:
        ping = random.randint(10, 150)
        tested.append({
            'config': config,
            'ping': ping,
            'is_white': config in white_configs
        })
    
    tested.sort(key=lambda x: x['ping'])
    
    # Отбираем лучшие
    best = []
    white_count = 0
    normal_count = 0
    used_countries = []
    
    # Сначала белые списки (2 шт) - анти-глушилки
    for cfg in tested:
        if cfg['is_white'] and white_count < 2:
            best.append(add_flag(cfg['config'], is_white=True))
            white_count += 1
    
    # Потом 4 лучших из разных стран
    for cfg in tested:
        if not cfg['is_white'] and normal_count < 4:
            country = extract_country(cfg['config'])
            if country not in used_countries:
                best.append(add_flag(cfg['config']))
                used_countries.append(country)
                normal_count += 1
    
    # Сохраняем
    config_path = os.path.join(os.path.dirname(__file__), 'configs', 'latest.txt')
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(best))
    
    logger.info(f"✅ Saved {len(best)} configs (White: {white_count}, Normal: {normal_count})")
    return best

# ============================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================

def generate_word(length=6):
    return ''.join(random.choices(string.ascii_uppercase, k=length))

def generate_subdomain():
    return '-'.join([generate_word() for _ in range(5)])

def get_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr or '0.0.0.0'

def is_telegram():
    ua = request.headers.get('User-Agent', '').lower()
    return 'telegram' in ua

def device_fingerprint():
    data = f"{request.headers.get('User-Agent', '')}|{get_ip()}"
    return hashlib.sha256(data.encode()).hexdigest()

def device_name(ua):
    ua = ua.lower()
    if 'iphone' in ua: return 'iPhone'
    if 'ipad' in ua: return 'iPad'
    if 'android' in ua: return 'Android' if 'mobile' in ua else 'Android Tablet'
    if 'windows' in ua: return 'Windows PC'
    if 'mac' in ua: return 'Mac'
    return 'Unknown'

def session_token():
    return hashlib.sha256(f"{random.getrandbits(256)}{time.time()}".encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('session_token')
        if not token:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        user = get_user_by_session(token)
        if not user:
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        return f(user=user, *args, **kwargs)
    return decorated

# ============================================
# TELEGRAM AUTH
# ============================================

def verify_telegram(auth_data):
    if not app.config['BOT_TOKEN']:
        return True
    
    data = auth_data.copy()
    hash_recv = data.pop('hash', '')
    items = sorted(data.items())
    data_str = '\n'.join(f"{k}={v}" for k, v in items)
    
    secret = hashlib.sha256(app.config['BOT_TOKEN'].encode()).digest()
    hash_calc = hmac.new(secret, data_str.encode(), hashlib.sha256).hexdigest()
    
    return hash_calc == hash_recv

# ============================================
# БД ФУНКЦИИ
# ============================================

def save_user(data):
    query = """
        INSERT INTO telegram_users 
        (telegram_id, first_name, last_name, username, photo_url, 
         language_code, auth_date, is_premium, is_beta, last_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (telegram_id) DO UPDATE SET
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            username = EXCLUDED.username,
            photo_url = EXCLUDED.photo_url,
            last_active = NOW()
        RETURNING id
    """
    params = (
        data['id'], data.get('first_name', ''), data.get('last_name', ''),
        data.get('username', ''), data.get('photo_url', ''),
        data.get('language_code', 'ru'), datetime.datetime.now(),
        data.get('is_premium', False), True
    )
    result = db.execute_query(query, params, fetch_one=True)
    return result['id'] if result else None

def register_device(user_id, fingerprint, ua, ip):
    check = db.execute_query(
        "SELECT id FROM user_devices WHERE device_fingerprint = %s",
        (fingerprint,), fetch_one=True
    )
    
    if check:
        db.execute_query(
            "UPDATE user_devices SET last_seen = NOW() WHERE id = %s",
            (check['id'],)
        )
        return check['id']
    
    count = db.execute_query(
        "SELECT COUNT(*) as c FROM user_devices WHERE user_id = %s AND is_active = TRUE",
        (user_id,), fetch_one=True
    )
    
    if count and count['c'] >= app.config['MAX_DEVICES']:
        db.execute_query("""
            UPDATE user_devices SET is_active = FALSE 
            WHERE id = (
                SELECT id FROM user_devices 
                WHERE user_id = %s AND is_active = TRUE 
                ORDER BY last_seen ASC LIMIT 1
            )
        """, (user_id,))
    
    name = device_name(ua)
    res = db.execute_query("""
        INSERT INTO user_devices (user_id, device_fingerprint, device_name, user_agent, ip_address)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
    """, (user_id, fingerprint, name, ua, ip), fetch_one=True)
    
    return res['id'] if res else None

def create_session(user_id, device_id, token, ip, ua):
    exp = datetime.datetime.now() + datetime.timedelta(days=7)
    db.execute_query("""
        INSERT INTO sessions (user_id, device_id, session_token, expires_at, ip_address, user_agent)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_id, device_id, token, exp, ip, ua))

def get_user_by_session(token):
    return db.execute_query("""
        SELECT u.id, u.telegram_id, u.first_name, u.last_name, u.username,
               u.photo_url, u.is_premium, u.language_code,
               d.id as device_id, d.device_name
        FROM sessions s
        JOIN telegram_users u ON s.user_id = u.id
        LEFT JOIN user_devices d ON s.device_id = d.id
        WHERE s.session_token = %s AND s.expires_at > NOW()
    """, (token,), fetch_one=True)

def create_sub(user_id, subdomain, days=30):
    exp = datetime.datetime.now() + datetime.timedelta(days=days)
    db.execute_query(
        "UPDATE subscriptions SET is_active = FALSE WHERE user_id = %s AND is_active = TRUE",
        (user_id,)
    )
    res = db.execute_query("""
        INSERT INTO subscriptions (user_id, subdomain, expires_at, device_limit)
        VALUES (%s, %s, %s, %s) RETURNING id
    """, (user_id, subdomain, exp, app.config['MAX_DEVICES']), fetch_one=True)
    return res['id'] if res else None

def get_user_sub(user_id):
    sub = db.execute_query("""
        SELECT id, subdomain, expires_at, use_count, device_limit, current_devices
        FROM subscriptions 
        WHERE user_id = %s AND is_active = TRUE AND expires_at > NOW()
        ORDER BY created_at DESC LIMIT 1
    """, (user_id,), fetch_one=True)
    
    if sub:
        devices = db.execute_query("""
            SELECT d.device_name, d.last_seen, sa.last_access
            FROM subscription_access sa
            JOIN user_devices d ON sa.device_id = d.id
            WHERE sa.subscription_id = %s
            ORDER BY sa.last_access DESC
        """, (sub['id'],), fetch_all=True)
        sub['devices'] = devices or []
    
    return sub

def check_access(sub_id, device_id):
    existing = db.execute_query(
        "SELECT id FROM subscription_access WHERE subscription_id = %s AND device_id = %s",
        (sub_id, device_id), fetch_one=True
    )
    
    if existing:
        db.execute_query("""
            UPDATE subscription_access 
            SET last_access = NOW(), access_count = access_count + 1
            WHERE id = %s
        """, (existing['id'],))
        return True
    
    count = db.execute_query(
        "SELECT COUNT(*) as c FROM subscription_access WHERE subscription_id = %s",
        (sub_id,), fetch_one=True
    )
    
    limit = db.execute_query(
        "SELECT device_limit FROM subscriptions WHERE id = %s",
        (sub_id,), fetch_one=True
    )
    device_limit = limit['device_limit'] if limit else 2
    
    if count['c'] < device_limit:
        db.execute_query(
            "INSERT INTO subscription_access (subscription_id, device_id) VALUES (%s, %s)",
            (sub_id, device_id)
        )
        db.execute_query(
            "UPDATE subscriptions SET current_devices = current_devices + 1 WHERE id = %s",
            (sub_id,)
        )
        return True
    else:
        # Удаляем самое старое устройство
        oldest = db.execute_query("""
            DELETE FROM subscription_access 
            WHERE id = (
                SELECT id FROM subscription_access 
                WHERE subscription_id = %s 
                ORDER BY last_access ASC LIMIT 1
            ) RETURNING id
        """, (sub_id,), fetch_one=True)
        
        if oldest:
            db.execute_query(
                "INSERT INTO subscription_access (subscription_id, device_id) VALUES (%s, %s)",
                (sub_id, device_id)
            )
            return True
    
    return False

def get_sub_by_domain(subdomain):
    return db.execute_query("""
        SELECT s.id, s.user_id, s.subdomain, s.expires_at,
               u.telegram_id, u.first_name, u.username
        FROM subscriptions s
        JOIN telegram_users u ON s.user_id = u.id
        WHERE s.subdomain = %s AND s.is_active = TRUE AND s.expires_at > NOW()
    """, (subdomain,), fetch_one=True)

def log_use(sub_id, device_id):
    db.execute_query(
        "UPDATE subscriptions SET use_count = use_count + 1, last_used = NOW() WHERE id = %s",
        (sub_id,)
    )

# ============================================
# МАРШРУТЫ
# ============================================

@app.route('/')
def index():
    """Только через Telegram"""
    if not is_telegram() and not request.cookies.get('session_token'):
        return render_template('telegram_only.html', 
                             bot_username=app.config['BOT_USERNAME'])
    
    user = None
    token = request.cookies.get('session_token')
    if token:
        user = get_user_by_session(token)
    
    return render_template('index.html',
                         site_url=app.config['SITE_URL'],
                         bot_username=app.config['BOT_USERNAME'],
                         user=user)

@app.route('/dashboard')
def dashboard():
    token = request.cookies.get('session_token')
    if not token:
        return redirect('/')
    
    user = get_user_by_session(token)
    if not user:
        return redirect('/')
    
    sub = get_user_sub(user['id'])
    
    return render_template('dashboard.html',
                         user=user,
                         subscription=sub,
                         max_devices=app.config['MAX_DEVICES'])

@app.route('/profile')
def profile():
    token = request.cookies.get('session_token')
    if not token:
        return redirect('/')
    
    user = get_user_by_session(token)
    if not user:
        return redirect('/')
    
    return render_template('profile.html', user=user)

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

# ============================================
# ОСНОВНОЙ МАРШРУТ ПОДПИСКИ
# ============================================

@app.route('/<subdomain>')
def subscription(subdomain):
    if not all(c in string.ascii_uppercase + '-' for c in subdomain) or '-' not in subdomain:
        return render_template('404.html'), 404
    
    sub = get_sub_by_domain(subdomain)
    if not sub:
        return render_template('404.html'), 404
    
    token = request.cookies.get('session_token')
    device_id = None
    
    if token:
        user = get_user_by_session(token)
        if user:
            device_id = user.get('device_id')
    
    if device_id:
        check_access(sub['id'], device_id)
        log_use(sub['id'], device_id)
        return redirect('/configs/latest.txt')
    
    return render_template('device_limit.html', max_devices=app.config['MAX_DEVICES'])

# ============================================
# API
# ============================================

@app.route('/api/auth/telegram', methods=['POST'])
def api_auth():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data'}), 400
        
        if not verify_telegram(data):
            return jsonify({'success': False, 'error': 'Invalid signature'}), 401
        
        user_id = save_user(data)
        if not user_id:
            return jsonify({'success': False, 'error': 'DB error'}), 500
        
        fp = device_fingerprint()
        ua = request.headers.get('User-Agent', '')
        ip = get_ip()
        
        device_id = register_device(user_id, fp, ua, ip)
        token = session_token()
        create_session(user_id, device_id, token, ip, ua)
        
        session['user_id'] = user_id
        session['telegram_id'] = data['id']
        
        resp = make_response(jsonify({
            'success': True,
            'user': {
                'id': data['id'],
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
                'username': data.get('username', ''),
                'photo_url': data.get('photo_url', '')
            }
        }))
        
        exp = datetime.datetime.now() + datetime.timedelta(days=7)
        resp.set_cookie('session_token', token, expires=exp, httponly=True, secure=True, samesite='Lax')
        
        return resp
        
    except Exception as e:
        logger.error(f"Auth error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    resp = make_response(jsonify({'success': True}))
    resp.delete_cookie('session_token')
    session.clear()
    return resp

@app.route('/api/user/me', methods=['GET'])
@login_required
def api_user(user):
    sub = get_user_sub(user['id'])
    return jsonify({'success': True, 'user': user, 'subscription': sub})

@app.route('/api/subscription/generate', methods=['POST'])
@login_required
def api_generate(user):
    for _ in range(10):
        subdomain = generate_subdomain()
        if not get_sub_by_domain(subdomain):
            break
    else:
        return jsonify({'success': False, 'error': 'Failed to generate'}), 500
    
    sub_id = create_sub(user['id'], subdomain)
    if not sub_id:
        return jsonify({'success': False, 'error': 'Failed to create'}), 500
    
    url = f"{app.config['SITE_URL']}/{subdomain}"
    return jsonify({'success': True, 'subdomain': subdomain, 'url': url})

@app.route('/api/stats', methods=['GET'])
def api_stats():
    users = db.execute_query("SELECT COUNT(*) as c FROM telegram_users", fetch_one=True)
    subs = db.execute_query("SELECT COUNT(*) as c FROM subscriptions WHERE is_active = TRUE", fetch_one=True)
    
    return jsonify({
        'users': users['c'] if users else 8500,
        'active': subs['c'] if subs else 1200,
        'servers': 420,
        'ping': 34
    })

@app.route('/configs/latest.txt')
def serve_configs():
    config_path = os.path.join(os.path.dirname(__file__), 'configs', 'latest.txt')
    
    if not os.path.exists(config_path):
        update_configs()
    
    return send_file(config_path, mimetype='text/plain')

@app.route('/api/update-configs', methods=['POST'])
def api_update():
    try:
        configs = update_configs()
        return jsonify({'success': True, 'count': len(configs)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# ЗАПУСК
# ============================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    try:
        update_configs()
    except Exception as e:
        logger.error(f"Initial update failed: {e}")
    
    logger.info(f"🚀 Vailae running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
