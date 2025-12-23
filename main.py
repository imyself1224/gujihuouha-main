# -*- coding: utf-8 -*-
"""
主程序入口 - Flask应用启动
"""

import sys
import io

# 设置UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 导入Flask应用
from app import app

if __name__ == '__main__':
    print("=" * 60)
    print("Character Portrait Analysis Model Service Started")
    print("Listening on port: 5002")
    print("=" * 60)
    
    # Start Flask application
    app.run(host='0.0.0.0', port=5002, debug=False)

