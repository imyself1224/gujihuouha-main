# Flask 应用配置文件

import os

# 基础配置
class Config:
    """基础配置"""
    # Flask 配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # API 配置
    API_TITLE = '古文事件抽取训练数据接口'
    API_VERSION = '1.0.0'
    
    # 数据集配置
    DATASETS_DIR = os.path.join(os.path.dirname(__file__), 'datasets')
    
    # 缓存配置
    CACHE_ENABLED = True
    CACHE_TIMEOUT = 3600  # 1 小时
    
    # 限流配置
    RATE_LIMIT_ENABLED = False
    
    # CORS 配置
    CORS_ENABLED = True
    CORS_ORIGINS = ['*']


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False
    JSON_AS_ASCII = False  # 支持中文输出


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False
    JSON_AS_ASCII = False


class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    TESTING = True
    JSON_AS_ASCII = False


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """获取配置对象"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    return config.get(config_name, DevelopmentConfig)
