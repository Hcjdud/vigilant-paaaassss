-- migrations/init.sql
-- Полная инициализация базы данных PostgreSQL

-- Таблица пользователей Telegram
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
);

-- Таблица устройств
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
);

-- Таблица подписок
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
);

-- Таблица сессий
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES telegram_users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE,
    device_id INTEGER REFERENCES user_devices(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Таблица доступа к подпискам
CREATE TABLE IF NOT EXISTS subscription_access (
    id SERIAL PRIMARY KEY,
    subscription_id INTEGER REFERENCES subscriptions(id) ON DELETE CASCADE,
    device_id INTEGER REFERENCES user_devices(id) ON DELETE CASCADE,
    last_access TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    UNIQUE(subscription_id, device_id)
);

-- Таблица статистики
CREATE TABLE IF NOT EXISTS stats (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE,
    users_count INTEGER DEFAULT 0,
    active_devices INTEGER DEFAULT 0,
    subscriptions_count INTEGER DEFAULT 0,
    total_requests INTEGER DEFAULT 0
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_telegram_id ON telegram_users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_device_fingerprint ON user_devices(device_fingerprint);
CREATE INDEX IF NOT EXISTS idx_subdomain ON subscriptions(subdomain);
CREATE INDEX IF NOT EXISTS idx_session_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_expires_at ON subscriptions(expires_at) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_devices ON user_devices(user_id, last_seen);
CREATE INDEX IF NOT EXISTS idx_subscription_access ON subscription_access(subscription_id, last_access);

-- Функция для автоматической очистки истекших подписок
CREATE OR REPLACE FUNCTION cleanup_expired_subscriptions()
RETURNS void AS $$
BEGIN
    UPDATE subscriptions 
    SET is_active = FALSE 
    WHERE expires_at < NOW() AND is_active = TRUE;
END;
$$ LANGUAGE plpgsql;

-- Комментарии к таблицам
COMMENT ON TABLE telegram_users IS 'Пользователи Telegram';
COMMENT ON TABLE user_devices IS 'Устройства пользователей для ограничения 2 шт';
COMMENT ON TABLE subscriptions IS 'Подписки с уникальными поддоменами';
COMMENT ON TABLE subscription_access IS 'Журнал доступа устройств к подпискам';
