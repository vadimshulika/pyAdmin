# pyAdmin

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**pyAdmin** - это комплексный Python-пакет для управления файлами, мониторинга системы и выполнения команд в среде Windows. Предоставляет простой API для автоматизации рутинных задач системного администрирования.
---
## Возможности
# 📁 Управление файлами
- Копирование и перемещение файлов с автоматическим созданием директорий
- Создание ZIP-архивов с валидацией
- Получение метаданных файлов (размер, даты, права доступа)
- Работа с путями относительно вызывающего скрипта

# 📊 Мониторинг системы
- Мониторинг использования диска, памяти и процессора
- Сетевые метрики (трафик, пакеты)
- Температуры компонентов системы
- Статистика запущенных процессов
- Время работы системы (uptime)

# ⚙️ Выполнение команд
- Выполнение одиночных команд и последовательностей
- Потоковый вывод в реальном времени
- Планировщик задач (периодические и одноразовые)
- Управление переменными среды
- Проверка доступности команд
- Повышенные привилегии (администратор)
---
## Установка
Установите пакет через pip:

```bash
pip install git+https://github.com/vadimshulika/pyAdmin.git
```
--- 
## Примеры использования
# Управление файлами
```python
from pyadmin.file_manager import FileManager

fm = FileManager()

# Копирование файла
fm.copy_file("source.txt", "backups/source_backup.txt")

# Создание архива
fm.compress_files(["data.csv", "config.yml"], "archive.zip")

# Получение метаданных
metadata = fm.get_file_metadata("readme.md")
print(f"Размер файла: {metadata['size_bytes']} байт")
```
# Мониторинг системы
```python
from pyadmin.system_monitoring import SystemMonitor

monitor = SystemMonitor()
status = monitor.get_system_status()

print(f"Использование CPU: {status['cpu']['usage_percent']}%")
print(f"Свободно памяти: {status['memory']['free_gb']} GB")
print(f"Температура CPU: {status['temperatures']['coretemp'][0]['current']}°C")
```
# Выполнение команд
```python 
from pyadmin.command_executor import CommandExecutor

executor = CommandExecutor()

# Простое выполнение
stdout, stderr, code = executor.execute_command("echo Hello World")

# Последовательность команд
results = executor.execute_sequence([
    "mkdir new_directory",
    "cd new_directory",
    "echo 'Content' > file.txt"
])

# Планирование задачи
def scheduled_callback(stdout, stderr, code):
    print(f"Задача выполнена с кодом {code}")

task_id = executor.schedule_command(
    "echo Scheduled Task",
    interval=60,
    callback=scheduled_callback
)

# Потоковый вывод
def output_handler(line):
    print(f"OUTPUT: {line}")

executor.realtime_output("ping 127.0.0.1 -n 3", output_handler)
```
