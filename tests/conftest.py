"""pytest ortak konfigürasyon — proje kökünü import yoluna ekle."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
