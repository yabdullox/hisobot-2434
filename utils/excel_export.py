import os
from datetime import datetime

import pandas as pd
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name

def export_reports_to_excel(reports, branch_name="Barcha Filiallar", report_type="Umumiy Hisobot"):
    """
    HISOBOT24 uchun Excel eksport:
    - Har bir mahsulot yoki matn alohida satrda (bitta katakda emas)
    - Formatlangan sarlavha, border, kenglik, wrap
    """

    # Fayl nomi
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"hisobot_{report_type.replace(' ', '_')}_{now}.xlsx"
    folder = "exports"
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, filename)

    # Hisobotni dataframega aylantiramiz
    df = pd.DataFrame(reports)
    if df.empty:
        df = pd.DataFrame([{"Ma'lumot": "Hisobot topilmadi"}])

    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        sheet_name = branch_name[:30]  # Excel varaq nomi cheklangan
        df.to_excel(writer, index=False, startrow=7, sheet_name=sheet_name)

        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # Formatlar
        title_format = workbook.add_format({
            "bold": True,
            "font_size": 18,
            "align": "center",
            "valign": "vcenter",
            "font_color": "white",
            "bg_color": "#1F4E78"
        })

        header_format = workbook.add_format({
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#4472C4",
            "font_color": "white",
            "border": 1
        })

        cell_format = workbook.add_format({
            "valign": "top",
            "align": "left",
            "border": 1
        })

        # Sarlavha
        col_count = len(df.columns)
        last_col = xl_col_to_name(col_count - 1)
        header_range = f"A{{row}}:{last_col}{{row}}"
        worksheet.merge_range(header_range.format(row=1), f"📊 HISOBOT24 — {branch_name}", title_format)

        # Ustun sarlavhalar
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(7, col_num, str(value), header_format)

        # 🔹 Hisobot matnini alohida satrlarga bo‘lish
        for row_idx, report in enumerate(reports, start=8):
            for col_idx, col_name in enumerate(df.columns):
                if col_name.lower() == "hisobot matni":
                    text = str(report[col_name]).strip()
                    lines = text.split("\n")  # Har satrda yangi qatorda chiqadi
                    for i, line in enumerate(lines):
                        worksheet.write(row_idx + i, col_idx, line, cell_format)
                else:
                    worksheet.write(row_idx, col_idx, str(report[col_name]), cell_format)

        # Ustun kengliklari
        for i, col in enumerate(df.columns):
            worksheet.set_column(i, i, 25)

    return file_path




