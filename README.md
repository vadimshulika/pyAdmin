# pyAdmin

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Утилита для управления файлами и мониторинга системных ресурсов.

## Возможности
- Копирование, перемещение файлов.
- Создание ZIP-архивов.
- Мониторинг использования диска, памяти и CPU.

## Примеры
```python
from pyAdmin import FileManager

fm = FileManager()
# Copy files
fm.copy_file("source.txt", "destination.txt")
# Get information about system
status = fm.get_system_status()
print(f"Free disk space: {status['disk']['free_gb']} GB")
```

## Установка
Установите пакет через pip:

```bash
pip install git+https://github.com/vadimshulika/pyAdmin.git
```