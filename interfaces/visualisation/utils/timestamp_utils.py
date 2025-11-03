from datetime import datetime
from typing import List

def extract_timestamps(flows) -> List[datetime]:
    return [datetime.fromisoformat(f["timestamp"]) for f in flows]
