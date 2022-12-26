import os
from os.path import abspath, dirname, join
import platform


PROJ_DIR = join(abspath(dirname(__file__)))
proj_name = "kddcup-2022"

if os.name == 'nt':
    DATA_DIR = 'C:/Users/zfj/research-data/{}'.format(proj_name)
    OUT_DIR = 'C:/Users/zfj/research-out-data/{}'.format(proj_name)
else:
    if platform.system() == "Darwin":
        DATA_DIR = '/Users/zfj/research-data/{}'.format(proj_name)
        OUT_DIR = '/Users/zfj/research-out-data/{}'.format(proj_name)
    else:
        DATA_DIR = '/home/zfj/research-data/{}'.format(proj_name)
        OUT_DIR = '/home/zfj/research-out-data/{}'.format(proj_name)

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)
DATA_PRED_DIR = join(DATA_DIR, "pred")
DATA_TRACE_DIR = join(DATA_DIR, "trace")
os.makedirs(DATA_PRED_DIR, exist_ok=True)
os.makedirs(DATA_TRACE_DIR, exist_ok=True)

MONGO_HOST_kexie = os.environ.get('MONGO_HOST', 'kexie.aminer.cn')
MONGO_PORT_kexie = os.environ.get('MONGO_PORT', 30027)
MONGO_USERNAME_kexie = os.environ.get('MONGO_USERNAME', 'aminer_lab_zfj')
MONGO_PASSWORD_kexie = os.environ.get('MONGO_PASSWORD', 'lab_zfj_123')
MONGO_DBNAME_kexie = os.environ.get('MONGO_DBNAME', 'aminer')

MONGO_HOST_106 = os.environ.get('MONGO_HOST', '166.111.7.106')
MONGO_PORT_106 = os.environ.get('MONGO_PORT', 30019)
MONGO_USERNAME_106 = os.environ.get('MONGO_USERNAME', 'kegger_bigsci')
MONGO_PASSWORD_106 = os.environ.get('MONGO_PASSWORD', 'datiantian123!@#')
MONGO_DBNAME_106 = os.environ.get('MONGO_DBNAME', 'aminerkg')
