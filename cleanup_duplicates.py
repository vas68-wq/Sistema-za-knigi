import sqlite3
import os

# --- Настройки ---
DATABASE_FILE = 'library.db'
# -----------------

def capitalize_and_merge(db_path, table_name, column_name):
    """
    Функция за почистване на дубликати в свързани таблици.
    Пример: обединява 'учител' и 'Учител' в едно - 'Учител'.
    """
    if not os.path.exists(db_path):
        print(f"ГРЕШКА: Файлът с базата данни '{db_path}' не е намерен.")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print(f"\n--- Почистване на таблица: {table_name} ---")

    # 1. Намираме всички уникални стойности, без значение от главни/малки букви
    cursor.execute(f"SELECT DISTINCT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL")
    all_entries = [row[column_name] for row in cursor.fetchall()]

    # 2. Групираме ги по тяхната версия с малки букви
    groups = {}
    for entry in all_entries:
        key = entry.lower()
        if key not in groups:
            groups[key] = []
        groups[key].append(entry)

    # 3. Минаваме през групите и обединяваме дубликатите
    for key, entries in groups.items():
        if len(entries) > 1: # Имаме дубликати (напр. 'Учител' и 'учител')
            # Определяме коя е правилната версия (с главна буква или първата)
            correct_version = next((e for e in entries if e == e.capitalize()), entries[0].capitalize())
            duplicates_to_remove = [e for e in entries if e != correct_version]
            
            print(f"Обединяване на '{', '.join(duplicates_to_remove)}' в '{correct_version}'...")

            # 4. Актуализираме основната таблица (readers)
            for dup in duplicates_to_remove:
                cursor.execute(f"UPDATE readers SET {column_name} = ? WHERE {column_name} = ?", (correct_version, dup))
            
            # 5. Изтриваме дубликатите от помощната таблица
            for dup in duplicates_to_remove:
                cursor.execute(f"DELETE FROM {table_name} WHERE {column_name} = ?", (dup,))

    # 6. Минаваме през всички останали записи и ги правим с главна буква
    cursor.execute(f"SELECT {column_name} FROM {table_name}")
    remaining_entries = [row[column_name] for row in cursor.fetchall()]
    for entry in remaining_entries:
        capitalized = entry.capitalize()
        if entry != capitalized:
            print(f"Коригиране на '{entry}' -> '{capitalized}'...")
            # Актуализираме и в двете таблици
            cursor.execute(f"UPDATE {table_name} SET {column_name} = ? WHERE {column_name} = ?", (capitalized, entry))
            cursor.execute(f"UPDATE readers SET {column_name} = ? WHERE {column_name} = ?", (capitalized, entry))

    conn.commit()
    conn.close()
    print(f"Почистването на '{table_name}' завърши.")


if __name__ == '__main__':
    print("Започва почистване на базата данни...")
    
    capitalize_and_merge(DATABASE_FILE, 'professions', 'profession')
    capitalize_and_merge(DATABASE_FILE, 'educations', 'education')
    
    print("\nВсичко е готово!")
    input("Натиснете Enter, за да затворите прозореца.")