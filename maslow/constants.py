import os
CURRENT_DIR_PATH = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.dirname(CURRENT_DIR_PATH)
DATABASE_PATH = os.path.join(BASE_PATH, 'database', 'chat_history.db')
LOG_FILE = os.path.join(BASE_PATH, 'maslow.log')