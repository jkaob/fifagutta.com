import ball25
import os

YEAR=2025


ball25.action_update_csv(dir_prefix=os.getenv('GITHUB_WORKSPACE'), backup_only=False)
