import os
from datetime import datetime

import pandas as pd
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name

def export_reports_to_excel(reports, branch_name="Barcha Filiallar", report_type="Umumiy Hisobot"):
    """
    HISOBOT24 uchun mukammal Excel eksport.
    - Rangli sarlavha
    - Avtomatik ustun kengligi
    - Border va markazlashtirilgan matnlar
    - Sana, filial va hisobot turi avtomatik yoziladi
    """

    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"hisobot_{report_type.replace(' ', '_')}_{now}.xlsx"
    folder = "exports"
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, filename)

    # DataFrame yaratish
    df = pd.DataFrame(reports)
    if df.empty:
        df = pd.DataFrame([{"Ma'lumot": "Hisobot topilmadi"}])

    # Excel yozish
    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        sheet_name = "Hisobot"
        df.to_excel(writer, index=False, startrow=7, sheet_name=sheet_name)

        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # ====== FORMATLAR ======
        title_format = workbook.add_format({
            "bold": True,
            "font_size": 18,
            "align": "center",
            "valign": "vcenter",
            "font_color": "white",
            "bg_color": "#1F4E78"
        })

        subtitle_format = workbook.add_format({
            "italic": True,
            "font_size": 11,
            "align": "left",
            "font_color": "#404040"
        })

        header_format = workbook.add_format({
            "bold": True,
            "font_size": 12,
            "text_wrap": True,
            "valign": "vcenter",
            "align": "center",
            "bg_color": "#4472C4",
            "font_color": "white",
            "border": 1
        })

        cell_format = workbook.add_format({
            "text_wrap": True,
            "valign": "top",
            "align": "left",
            "border": 1
        })

        footer_format = workbook.add_format({
            "italic": True,
            "font_color": "#606060",
            "align": "right",
        })

        # ====== Sarlavha ======
        col_count = max(len(df.columns), 1)
        last_col_letter = xl_col_to_name(col_count - 1)
        header_range = f"A{{row}}:{last_col_letter}{{row}}"

        worksheet.merge_range(header_range.format(row=1), "🧾 HISOBOT24 — Ishchi Hisobotlar", title_format)
        worksheet.merge_range(header_range.format(row=2), f"📁 Hisobot turi: {report_type}", subtitle_format)
        worksheet.merge_range(header_range.format(row=3), f"🏢 Filial: {branch_name}", subtitle_format)
        worksheet.merge_range(
            header_range.format(row=4),
            f"📅 Yaratilgan sana: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            subtitle_format,
        )
        worksheet.merge_range(header_range.format(row=5), " ", subtitle_format)

        # ====== Jadval ustunlari ======
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(7, col_num, str(value), header_format)

        # Jadval qiymatlarini yozish
        for row in range(len(df)):
            for col in range(len(df.columns)):
                worksheet.write(row + 8, col, str(df.iloc[row, col]), cell_format)

        # Ustun kengliklarini avtomatik sozlash
        for i, col in enumerate(df.columns):
            column_series = df[col].astype(str)
            max_len = max(column_series.map(len).max(), len(str(col)))
            worksheet.set_column(i, i, min(max_len + 3, 40))

        # ====== Footer (pastda) ======
        footer_row = len(df) + 10
        worksheet.merge_range(
            header_range.format(row=footer_row),
            "📌 Ushbu hisobot HISOBOT24 tizimi tomonidan avtomatik yaratildi.",
            footer_format
        )

    return file_path
