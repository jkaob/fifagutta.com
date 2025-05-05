from  src.ball25 import TippeData25
import os

YEAR=2025


TippeData25.action_update_csv(dir_prefix=os.getenv('GITHUB_WORKSPACE'), backup_only=False)
