from SQLmanager import *
from datetime import datetime

now = datetime.now()

reserve_space(1, now.replace(hour=8).replace(minute=0).replace(second=0), now.replace(hour=16).replace(minute=0).replace(second=0))
reserve_space(2, now.replace(hour=8).replace(minute=0).replace(second=0), now.replace(hour=16).replace(minute=0).replace(second=0))
reserve_space(3, now.replace(hour=8).replace(minute=0).replace(second=0), now.replace(hour=14).replace(minute=0).replace(second=0))
reserve_space(3, now.replace(hour=15).replace(minute=30).replace(second=0), now.replace(hour=18).replace(minute=0).replace(second=0))