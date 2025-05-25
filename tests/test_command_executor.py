from pathlib import Path
import threading
import pytest
import shutil
from datetime import datetime, timedelta
import subprocess
import time
import os
import sys
import logging
from unittest.mock import Mock, patch
from pyAdmin.command_executor import CommandExecutor

@pytest.fixture
def executor():
    ex = CommandExecutor(log_file="test.log")
    ex.logger.setLevel(logging.CRITICAL)
    yield ex
    ex.pause_scheduler()

def test_execute_command_basic(executor):
    """Test basic command execution"""
    stdout, stderr, code = executor.execute_command("echo Hello")
    assert code == 0
    assert "Hello" in stdout

def test_schedule_command(executor):
    """Test task scheduling"""
    task_id = executor.schedule_command("echo Test", interval=1)
    assert task_id in executor.get_scheduled_tasks()
    time.sleep(1.5)
    executor.pause_scheduler()

@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_windows_specific(executor):
    """Test Windows-specific command"""
    stdout, stderr, code = executor.execute_command("dir")
    assert code == 0
    # Универсальная проверка для любой локализации
    assert any(keyword in stdout for keyword in ["Directory", "Папка", "<DIR>"])
    assert "байт" in stdout  # Проверка наличия информации о размере

def test_complex_command_sequence(executor):
    """Тест сложной последовательности команд"""
    commands = [
        "echo Start",
        "mkdir test_dir",
        "dir" if sys.platform == "win32" else "ls"
    ]
    
    try:
        results = executor.execute_sequence(commands)
        assert len(results) == 3
        assert results[0][2] == 0  # echo Start
        assert results[1][2] == 0  # mkdir
        assert results[2][2] == 0  # dir/ls
        assert "test_dir" in results[2][0]
    finally:
        # Удаление папки независимо от результата теста
        if os.path.exists("test_dir"):
            if sys.platform == "win32":
                executor.execute_command("rmdir /s /q test_dir")
            else:
                shutil.rmtree("test_dir", ignore_errors=True)

def test_scheduled_task_removal(executor):
    """Тест удаления задачи"""
    task_id = executor.schedule_command("echo Test", interval=1)
    assert executor.remove_scheduled_task(task_id) is True
    assert task_id not in executor.get_scheduled_tasks()

def test_schedule_at_task(executor):
    """Тестирование одноразового задания по времени"""
    run_time = datetime.now() + timedelta(seconds=2)
    task_id = executor.schedule_at("echo Timed", run_time)
    time.sleep(3)
    tasks = executor.get_scheduled_tasks()
    assert task_id not in tasks  # Задача должна удалиться после выполнения

def test_realtime_output(executor):
    """Тестирование вывода в реальном времени"""
    mock_callback = Mock()
    cmd = "echo Realtime Test" if sys.platform == "win32" else "echo 'Realtime Test'"
    code = executor.realtime_output(cmd, mock_callback)
    assert code == 0
    mock_callback.assert_called_with("Realtime Test")

def test_environment_management(executor):
    """Тестирование управления переменными окружения"""
    executor.set_environment({"TEST_ENV": "123"})
    assert executor.export_environment()["TEST_ENV"] == "123"
    
    executor.reset_environment()
    assert "TEST_ENV" not in executor.export_environment()

def test_working_directory(executor):
    """Тестирование смены рабочей директории"""
    test_dir = "test_dir_123"
    try:
        # Создание и проверка директории
        executor.execute_command(f"mkdir {test_dir}")
        executor.set_working_directory(test_dir)
        assert executor.working_dir.name == test_dir
        
        # Проверка обработки неверного пути
        with pytest.raises(NotADirectoryError):
            executor.set_working_directory("invalid_path_999")
            
    finally:
        # Возврат в исходную директорию
        executor.set_working_directory(os.getcwd())
        # Удаление тестовой директории
        if os.path.exists(test_dir):
            if sys.platform == "win32":
                executor.execute_command(f"rmdir /s /q {test_dir}")
            else:
                shutil.rmtree(test_dir, ignore_errors=True)

@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_admin_execution(executor):
    """Тест выполнения команды с правами администратора с мокированием"""
    mock_process = Mock()
    mock_process.stdout = Mock()

    # Генератор вывода для readline
    def readline_gen():
        yield "Admin\n"
        yield ""
        while True:
            yield ""

    mock_process.stdout.readline.side_effect = readline_gen()
    mock_process.poll.side_effect = [None, 0]
    mock_process.returncode = 0

    mock_callback = Mock()

    with patch("pyAdmin.command_executor.subprocess.Popen", return_value=mock_process):
        code = executor.realtime_output("echo Admin", mock_callback, admin=True)

        assert code == 0
        mock_callback.assert_called_with("Admin")

def test_error_handling(executor):
    """Тестирование обработки ошибок"""
    # Несуществующая команда, ожидаем ненулевой код возврата, но не обязательно -1
    stdout, stderr, code = executor.execute_command("invalid_command_xyz")

    # Проверяем, что код возврата сигнализирует об ошибке
    assert code != 0, f"Ожидался код ошибки, но получен {code}"
    assert stderr  # stderr должен содержать сообщение об ошибке

def test_scheduler_pause_resume(executor):
    """Тестирование паузы и возобновления планировщика"""
    import sys
    finished = threading.Event()

    def on_finish(stdout, stderr, code):
        finished.set()

    # Команда, которая выполняется медленно
    command = "timeout /T 2 >nul" if sys.platform == "win32" else "sleep 2"

    executor.resume_scheduler()
    task_id = executor.schedule_command(command, interval=5, max_runs=1, callback=on_finish)

    # Ждём появления задачи
    for _ in range(10):
        task = executor.get_scheduled_tasks().get(task_id)
        if task and task["active"]:
            break
        time.sleep(0.1)

    executor.pause_scheduler()

    # Проверка: задача существует и не выполнена
    task = executor.get_scheduled_tasks().get(task_id)
    assert task is not None and task["active"] is True
    assert not finished.is_set()

    # Возобновление и ожидание выполнения
    executor.resume_scheduler()
    assert finished.wait(timeout=7), "Задача не была выполнена"

    executor.pause_scheduler()
    assert task_id not in executor.get_scheduled_tasks(), "Задача не удалилась после выполнения"

def test_thread_safety(executor):
    """Тестирование конкурентного доступа к планировщику"""
    from concurrent.futures import ThreadPoolExecutor
    
    def schedule_task(_):
        return executor.schedule_command("echo Concurrent", interval=0.1)
    
    with ThreadPoolExecutor(5) as pool:
        tasks = list(pool.map(schedule_task, range(10)))
    
    assert len(executor.get_scheduled_tasks()) == 10

def test_execute_command_timeout(executor):
    """Тест обработки таймаута команды"""
    # Команда, которая будет выполняться 2 секунды с таймаутом 1 секунда
    cmd = "timeout /T 5" if sys.platform == "win32" else "sleep 5"
    stdout, stderr, code = executor.execute_command(cmd, timeout=1)
    assert code != 0
    

def test_execute_sequence_stop_on_error(executor):
    """Тест остановки последовательности при ошибке"""
    commands = [
        "echo Start",
        "invalid_command_xyz",
        "echo This should not run"
    ]
    results = executor.execute_sequence(commands, stop_on_error=True)
    assert len(results) == 2
    assert results[1][2] != 0

def test_schedule_immediate_run(executor):
    """Тест немедленного выполнения задачи"""
    mock_callback = Mock()
    task_id = executor.schedule_command(
        "echo Immediate", 
        interval=10, 
        immediate_run=True,
        callback=mock_callback
    )
    time.sleep(0.5)  # Даем время на выполнение
    mock_callback.assert_called_once()

def test_schedule_at_execution(executor):
    """Тест выполнения задачи по расписанию"""
    run_time = datetime.now() + timedelta(seconds=2)
    mock_callback = Mock()
    task_id = executor.schedule_at("echo ScheduledAt", run_time, mock_callback)
    time.sleep(3)
    mock_callback.assert_called_once()

def test_validate_command_invalid(executor):
    """Тест проверки несуществующей команды"""
    assert not executor.validate_command("nonexistent_command_123")

def test_set_environment_update(executor):
    """Тест обновления переменных окружения"""
    executor.set_environment({"KEY1": "val1", "KEY2": "val2"})
    executor.set_environment({"KEY2": "new_val"})
    assert executor.export_environment()["KEY2"] == "new_val"

def test_scheduler_at_task_handling(executor):
    """Тест обработки задач типа 'at' в планировщике"""
    task_id = executor.schedule_at(
        "echo TestAt", 
        datetime.now() + timedelta(seconds=1)
    )
    time.sleep(2)
    assert task_id not in executor.get_scheduled_tasks()

def test_trigger_invalid_task(executor):
    """Тест запуска несуществующей задачи"""
    with patch.object(executor.logger, 'error') as mock_log:
        executor._trigger_task(999)
        mock_log.assert_called_with("Failed to trigger missing task 999")

def test_resume_running_scheduler(executor):
    """Тест возобновления уже работающего планировщика"""
    with patch.object(executor.logger, 'warning') as mock_log:
        executor.resume_scheduler()
        executor.resume_scheduler()
        mock_log.assert_called_with("Scheduler already running")

def test_start_scheduler_alive(executor):
    """Тест запуска уже работающего планировщика"""
    with patch.object(executor.logger, 'warning') as mock_log:
        executor._start_scheduler()
        executor._start_scheduler()
        mock_log.assert_called_with("Scheduler thread already running")

def test_handle_task_removal(executor):
    """Тест внутренней очистки задач"""
    task_id = executor.schedule_command("echo Cleanup", interval=10)
    executor._handle_task_removal(task_id)
    assert task_id not in executor.scheduled_tasks

def test_set_invalid_working_directory(executor):
    """Тест установки неверного рабочего каталога"""
    with pytest.raises(NotADirectoryError):
        executor.set_working_directory("invalid_path_xyz")

def test_export_environment_copy(executor):
    """Тест возврата копии переменных окружения"""
    executor.set_environment({"TEST_KEY": "value"})
    env_copy = executor.export_environment()
    env_copy.pop("TEST_KEY")
    assert "TEST_KEY" in executor.export_environment()

def test_reset_environment_clear(executor):
    """Тест сброса переменных окружения"""
    executor.set_environment({"TEST_KEY": "value"})
    executor.reset_environment()
    assert not executor.export_environment()

def test_validate_task_structure(executor):
    """Тест валидации структуры задачи"""
    valid_task = {
        'type': 'interval',
        'command': 'echo Test',
        'active': True,
        'last_run': 0,
        'max_runs': None,
        'run_count': 0
    }
    assert executor._validate_task_structure(valid_task)
    
    invalid_task = {'command': 'echo Broken'}
    assert not executor._validate_task_structure(invalid_task)

def test_timeout_expired_handling(executor):
    """Тест обработки исключения TimeoutExpired"""
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 1)):
        stdout, stderr, code = executor.execute_command("any_command")
        assert code != 0

def test_scheduler_double_resume(executor):
    """Тест двойного возобновления планировщика"""
    with patch.object(executor.logger, 'warning') as mock_log:
        executor.resume_scheduler()
        executor.resume_scheduler()
        mock_log.assert_called_with("Scheduler already running")

def test_trigger_nonexistent_task(executor):
    """Тест триггера несуществующей задачи"""
    with patch.object(executor.logger, 'error') as mock_log:
        executor._trigger_task(9999)
        mock_log.assert_called_with("Failed to trigger missing task 9999")

def test_task_validation_edge_cases(executor):
    """Тест валидации структуры задач"""
    # Неполная структура задачи
    assert not executor._validate_task_structure({'type': 'interval'})
    
    # Все обязательные поля
    valid_task = {
        'type': 'interval',
        'command': 'test',
        'active': True,
        'last_run': 0,
        'max_runs': None,
        'run_count': 0
    }
    assert executor._validate_task_structure(valid_task)