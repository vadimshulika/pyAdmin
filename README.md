# pyAdmin

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Утилита для управления файлами и мониторинга системных ресурсов.

## Возможности
- Копирование, перемещение файлов.
- Создание ZIP-архивов.
- Мониторинг использования диска, памяти и CPU.

## Использование
Все пути к файлам указываются **относительно директории вашего скрипта**:
```python
from pyAdmin import FileManager

fm = FileManager()
    
# Тестирование копирования
fm.copy_file('test.txt', 'copy_test.txt')
    
# Тестирование перемещения
fm.move_file('move_test.txt', 'moved/move_test.txt')
    
# Тестирование архивации
fm.compress_files(['file1.txt', 'file2.txt'], 'archive.zip')
    
# Получение информации о системе
status = fm.get_system_status()
print("\nСистемная информация:")
print(f"Диск: {status['disk']['free']} GB свободно из {status['disk']['total']} GB")
print(f"Память: {status['memory']['used']} GB использовано из {status['memory']['total']} GB")
print(f"CPU: {status['cpu']['usage_percent']}% загрузки")
```

## Установка
Установите пакет через pip:

```bash
pip install git+https://github.com/vadimshulika/pyAdmin.git
```