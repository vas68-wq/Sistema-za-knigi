import csv
import re
from datetime import datetime, date

def clean_price(p_str):
    if isinstance(p_str, (int, float)): return p_str
    if not p_str: return 0.0
    c_str = re.sub(r'[^\d,.]', '', str(p_str)).replace(',', '.')
    try: return float(c_str)
    except (ValueError, TypeError): return 0.0

def clean_date(d_str):
    if not d_str: return date.today().strftime('%d.%m.%Y')
    d_str = str(d_str).strip()
    m_map = { 'януари': '01', 'февруари': '02', 'март': '03', 'април': '04', 'май': '05', 'юни': '06', 'юли': '07', 'август': '08', 'септември': '09', 'октомври': '10', 'ноември': '11', 'декември': '12' }
    try:
        parts = re.split(r'[.\s/-]', d_str)
        if len(parts) == 3:
            day, m_str, y_str = parts
            day = day.zfill(2)
            month = m_map.get(m_str.lower(), m_str).zfill(2)
            year = f"20{y_str}" if len(y_str) == 2 else y_str
            if month.isdigit() and year.isdigit() and day.isdigit(): return f"{day}.{month}.{year}"
    except Exception: pass
    try: return datetime.strptime(d_str, '%Y-%m-%d').strftime('%d.%m.%Y')
    except (ValueError, TypeError): return date.today().strftime('%d.%m.%Y')
    return d_str

def clean_int(i_str):
    if isinstance(i_str, int): return i_str
    if not i_str: return None
    c_str = re.sub(r'\D', '', str(i_str))
    if not c_str: return None
    try: return int(c_str)
    except (ValueError, TypeError): return None

input_filename = 'КНИГИ.csv'
output_filename = 'КНИГИ_коригиран.csv'

try:
    # КОРЕКЦИЯТА Е ТУК: Променяме encoding на 'utf-8-sig'
    with open(input_filename, 'r', encoding='windows-1251') as infile, open(output_filename, 'w', newline='', encoding='utf-8-sig') as outfile:
        reader = csv.reader(infile, delimiter=';')
        writer = csv.writer(outfile)

        header = next(reader)
        writer.writerow(header)
        
        processed_count = 0
        for row in reader:
            if len(row) < 8:
                continue

            tom_no = row[0].strip()
            isbn = row[1].strip()
            author = row[2].strip()
            title = row[3].strip()
            genre = row[4].strip()
            publish_year = clean_int(row[5])
            record_date = clean_date(row[6])
            price = clean_price(row[7])

            writer.writerow([tom_no, isbn, author, title, genre, publish_year, record_date, price])
            processed_count += 1

    print(f"Готово! Обработени са {processed_count} реда.")
    print(f"Резултатът е записан в нов файл: '{output_filename}'")

except FileNotFoundError:
    print(f"ГРЕШКА: Не мога да намеря файла '{input_filename}'. Уверете се, че е в същата папка.")
except Exception as e:
    print(f"Възникна неочаквана грешка: {e}")