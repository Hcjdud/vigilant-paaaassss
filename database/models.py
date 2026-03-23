from datetime import datetime, timedelta

class Subscription:
    @staticmethod
    def check_device_limit(current, max_devices=2):
        return current < max_devices
    
    @staticmethod
    def format_expiry(expires_at):
        if not expires_at:
            return None
        delta = expires_at - datetime.now()
        if delta.days > 0:
            return f"{delta.days} дней"
        return f"{delta.seconds // 3600} часов"
