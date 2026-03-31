import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '..', '.env'))

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/masterdehostias')
JWT_SECRET = os.getenv('JWT_SECRET', 'change_me')
JWT_ALGORITHM = 'HS256'
JWT_EXP_HOURS = int(os.getenv('JWT_EXP_HOURS', '24'))
