# config.py

import os

class Config:
    """
    Клас за конфигурация на Flask приложението.
    Съдържа всички настройки, изнесени от основния файл.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a-very-secret-and-secure-key-for-prod')
    
    # --- Настройки на базата данни и папки ---
    DATABASE = 'library.db'
    SIGNATURES_FOLDER = 'signatures'
    COVERS_FOLDER = 'covers'
    
    # --- Настройки на приложението ---
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    BOOKS_PER_PAGE = 25
    FINE_PER_DAY = 0.20
    
    # --- Настройки за сигурност при вход ---
    LOGIN_ATTEMPTS_LIMIT = 3
    LOGIN_LOCKOUT_MINUTES = 15