import ball24
import os

ball24.action_update_csv(dir_prefix=os.getenv('GITHUB_WORKSPACE'), backup_only=True)