# ============================================
# 📦 handlers/__init__.py
# --------------------------------------------
# Bu fayl botning barcha modullarini (routerlarni)
# yagona joydan import qilish uchun xizmat qiladi.
# worker.py ni bu yerda chaqirmaymiz,
# chunki u main.py da bevosita dp.include_router() bilan ulanadi.
# ============================================

from . import start
from . import admin
from . import superadmin

# ⚠️ Diqqat: worker.py ni bu yerda import QILMAYMIZ!
# Chunki worker.router allaqachon main.py ichida dp.include_router(worker.router)
# orqali ulanadi. Aks holda "Router is already attached" xatosi chiqadi.
#
# Agar kelajakda boshqa handler fayllar (masalan: finance.py, products.py)
# qo‘shilsa, ularni ham shu yerga import qilishingiz mumkin:
# from . import finance
# from . import products
