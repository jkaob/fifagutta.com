import os
import json


PRESEASON = False
DEFAULT_N_DAYS = 7
DOWNLOAD_ADMIN = True

PASSWORD_ID = json.loads(os.getenv('FIFAGUTTA_PASSWORDS_ID_JSON'))