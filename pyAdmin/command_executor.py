"""Windows command executor with scheduling and real-time output capabilities."""

import subprocess
import shutil
import logging
import threading
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Callable, Any

class CommandExecutor:
    """Main class for executing and managing shell commands on Windows systems.
    
    Provides features for:
    - Executing single commands and command sequences
    - Real-time output monitoring
    - Scheduled task execution
    - Environment variable management
    
    Attributes:
        env_vars (Dict[str, str]): Custom environment variables
        working_dir (Path): Current working directory
        scheduled_tasks (Dict[int, Dict]): Active scheduled tasks
    """
    
    def __init__(self, log_file: str = "command_executor.log"):
        """Initialize command executor with default settings.
        
        Args:
            log_file (str): Path to log file. Default: 'command_executor.log'
        """
        self._init_logger(log_file)
        self.env_vars = {}
        self.working_dir = Path.cwd()
        self.scheduled_tasks = {}
        self.task_id_counter = 0
        self.scheduler_thread = None
        self.stop_scheduler = threading.Event()
        self.encoding = 'cp866'
        self.logger.info("CommandExecutor initialized")

    def _init_logger(self, log_file: str) -> None:
        """Configure logging handlers.
        
        Args:
            log_file (str): Path to log file
        """
        self.logger = logging.getLogger("CommandExecutor")
        self.logger.setLevel(logging.DEBUG)

        # File handler with detailed format
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)

        # Console handler with simple format
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter("%(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def execute_command(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
        shell: bool = True
    ) -> Tuple[str, str, int]:
        """Execute a single shell command with proper error handling.
        
        Args:
            command (str): Command to execute
            cwd (str, optional): Working directory. Default: current directory
            timeout (int, optional): Maximum execution time in seconds
            shell (bool): Use shell interpreter. Recommended for Windows
            
        Returns:
            Tuple[str, str, int]: (stdout, stderr, return_code)
            
        Examples:
            >>> executor.execute_command("echo Hello World")
            ('Hello World\\r\\n', '', 0)
        """
        self.logger.debug(f"Executing command: {command}")
        try:
            process = subprocess.run(
                command,
                cwd=cwd or str(self.working_dir),
                env={**os.environ, **self.env_vars},
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=shell,
                encoding=self.encoding,
                errors='replace'
            )
            self.logger.info(f"Command executed: {command} Code: {process.returncode}")
            return (process.stdout, process.stderr, process.returncode)
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out: {command}"
            self.logger.error(error_msg)
            return ("", error_msg, -1)
        except Exception as e:
            error_msg = f"Execution failed: {command} - {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ("", error_msg, -1)

    def execute_sequence(
        self,
        commands: List[str],
        stop_on_error: bool = True,
        **kwargs
    ) -> List[Tuple[str, str, int]]:
        """Execute commands sequentially with error propagation control.
        
        Args:
            commands (List[str]): List of commands to execute
            stop_on_error (bool): Stop execution on first error
            **kwargs: Additional arguments for execute_command
            
        Returns:
            List[Tuple[str, str, int]]: Execution results for each command
            
        Examples:
            >>> executor.execute_sequence(["echo 1", "echo 2"])
            [('1\\r\\n', '', 0), ('2\\r\\n', '', 0)]
        """
        results = []
        self.logger.info(f"Executing command sequence ({len(commands)} commands)")
        
        for idx, cmd in enumerate(commands, 1):
            self.logger.debug(f"Executing command {idx}/{len(commands)}: {cmd}")
            result = self.execute_command(cmd, **kwargs)
            results.append(result)
            
            if stop_on_error and result[2] != 0:
                self.logger.warning(f"Stopped sequence on failed command: {cmd}")
                break
                
        return results
    
    def schedule_command(
        self,
        command: str,
        interval: int,
        immediate_run: bool = False,
        max_runs: Optional[int] = None,
        callback: Optional[Callable[[str, str, int], None]] = None
    ) -> int:
        """Schedule periodic command execution with configurable parameters.
        
        Args:
            command (str): Command to execute periodically
            interval (int): Execution interval in seconds
            immediate_run (bool): Run immediately after scheduling
            max_runs (int): Maximum number of executions (None = infinite)
            callback (Callable): Function to call after each execution
            
        Returns:
            int: Unique task ID
            
        Examples:
            >>> task_id = executor.schedule_command("echo Task", interval=5)
            >>> executor.get_scheduled_tasks()[task_id]['command']
            'echo Task'
        """
        self.task_id_counter += 1
        task = {
            'type': 'interval',
            'command': command,
            'interval': interval,
            'max_runs': max_runs,
            'run_count': 0,
            'callback': callback,
            'last_run': 0,
            'active': True
        }
        self.scheduled_tasks[self.task_id_counter] = task
        self.logger.info(f"Scheduled interval task {self.task_id_counter}: {command}")

        if immediate_run:
            self._trigger_task(self.task_id_counter)

        if not self.scheduler_thread:
            self._start_scheduler()

        return self.task_id_counter

    def schedule_at(
        self,
        command: str,
        execution_time: datetime,
        callback: Optional[Callable[[str, str, int], None]] = None
    ) -> int:
        """Schedule one-time command execution at specified time.
        
        Args:
            command (str): Command to execute
            execution_time (datetime): Exact execution time
            callback (Callable): Function to call after execution
            
        Returns:
            int: Unique task ID
            
        Examples:
            >>> from datetime import datetime, timedelta
            >>> run_time = datetime.now() + timedelta(minutes=5)
            >>> task_id = executor.schedule_at("echo Timed", run_time)
        """
        self.task_id_counter += 1
        task = {
            'type': 'at',
            'command': command,
            'execution_time': execution_time.timestamp(),
            'callback': callback,
            'fired': False,
            'active': True,
            'interval': 0,
            'last_run': 0,
            'max_runs': 1,
            'run_count': 0
        }
        self.scheduled_tasks[self.task_id_counter] = task
        self.logger.info(f"Scheduled timed task {self.task_id_counter}: {command}")

        if not self.scheduler_thread:
            self._start_scheduler()

        return self.task_id_counter

    def validate_command(self, command: str) -> bool:
        """Verify if command is available in system PATH.
        
        Args:
            command (str): Command to check (first token only)
            
        Returns:
            bool: True if command exists
            
        Examples:
            >>> executor.validate_command("python --version")
            True
        """
        cmd = command.split()[0]
        exists = shutil.which(cmd) is not None
        self.logger.debug(f"Command validation: {cmd} -> {'Exists' if exists else 'Not found'}")
        return exists
    
    def set_environment(self, env_vars: Dict[str, str]) -> None:
        """Update execution environment variables.
        
        Args:
            env_vars (Dict[str, str]): Key-value pairs to add/update
            
        Examples:
            >>> executor.set_environment({"DEBUG": "true"})
        """
        self.env_vars.update(env_vars)
        self.logger.info(f"Updated environment variables: {list(env_vars.keys())}")

    def _scheduler_loop(self) -> None:
        """Main scheduler loop monitoring task execution times."""
        self.logger.debug("Scheduler loop started")
        while not self.stop_scheduler.is_set():
            try:
                current_time = time.time()
                for task_id, task in list(self.scheduled_tasks.items()):
                    if not task.get('active', False):
                        continue

                    if task['type'] == 'interval':
                        if current_time - task['last_run'] >= task['interval']:
                            self._trigger_task(task_id)
                            
                    elif task['type'] == 'at':
                        if not task['fired'] and current_time >= task['execution_time']:
                            self._trigger_task(task_id)
                            
                time.sleep(1)
            except Exception as e:
                self.logger.critical(f"Scheduler loop failed: {str(e)}", exc_info=True)
                break

    def _execute_scheduled_task(self, task_id: int) -> None:
        """Execute task and handle completion logic."""
        task = self.scheduled_tasks.get(task_id)
        if not task or 'run_count' not in task:
            self.logger.error(f"Invalid task structure: {task_id}")
            return

        try:
            self.logger.info(f"Executing task {task_id}: {task['command']}")
            stdout, stderr, code = self.execute_command(task['command'])
            
        except Exception as e:
            self.logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
            stdout, stderr, code = "", str(e), -1

        finally:
            if task.get('callback'):
                task['callback'](stdout, stderr, code)

            task['run_count'] += 1
            task['last_run'] = time.time()

            if task['type'] == 'at' or (task['max_runs'] is not None and task['run_count'] >= task['max_runs']):
                self.remove_scheduled_task(task_id)

    def realtime_output(
        self,
        command: str,
        output_callback: Callable[[str], None],
        admin: bool = False,
        **kwargs
    ) -> int:
        """Execute command with real-time output streaming.
        
        Args:
            command (str): Command to execute
            output_callback (Callable[[str], None]): Function to handle each output line
            admin (bool): Run with administrator privileges
            **kwargs: Additional arguments for subprocess.Popen
            
        Returns:
            int: Command exit code
            
        Examples:
            >>> def callback(line):
            ...     print(f"OUT: {line}")
            >>> executor.realtime_output("ping yandex.ru -n 2", callback)
        """
        self.logger.info(f"Starting realtime execution: {command}")
        try:
            if admin:
                self.logger.debug("Elevating privileges for command")
                full_command = (
                    f'Start-Process cmd -Verb RunAs -ArgumentList "/c {command}" '
                    '-WindowStyle Hidden -Wait'
                )
                process = subprocess.Popen(
                    ["powershell", "-Command", full_command],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    encoding=self.encoding,
                    errors='replace',
                    bufsize=1,
                    universal_newlines=True
                )
            else:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    encoding=self.encoding,
                    errors='replace',
                    bufsize=1,
                    universal_newlines=True
                )

            while True:
                output = process.stdout.readline()
                if not output and process.poll() is not None:
                    break
                if output:
                    self.logger.debug(f"Realtime output: {output.strip()}")
                    output_callback(output.strip())

            return_code = process.returncode
            self.logger.info(f"Realtime execution completed. Code: {return_code}")
            return return_code

        except Exception as e:
            self.logger.error(f"Realtime execution failed: {str(e)}", exc_info=True)
            return -1

    def remove_scheduled_task(self, task_id: int) -> bool:
        """Remove scheduled task by ID.
        
        Args:
            task_id (int): Task identifier returned by schedule methods
            
        Returns:
            bool: True if task was removed, False if not found
            
        Examples:
            >>> task_id = executor.schedule_command(...)
            >>> executor.remove_scheduled_task(task_id)
            True
        """
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            self.logger.info(f"Removed task {task_id}")
            return True
        self.logger.warning(f"Task {task_id} not found for removal")
        return False

    def pause_scheduler(self) -> None:
        """Pause all scheduled task executions.
        
        Examples:
            >>> executor.pause_scheduler()
            >>> executor.get_scheduled_tasks()
            {}
        """
        self.stop_scheduler.set()
        self.logger.info("Scheduler paused")

        if self.scheduler_thread and self.scheduler_thread.is_alive():
            if self.scheduler_thread is not threading.current_thread():
                self.scheduler_thread.join(timeout=1)
            self.scheduler_thread = None

    def resume_scheduler(self) -> None:
        """Resume paused scheduler operations.
        
        Examples:
            >>> executor.pause_scheduler()
            >>> executor.resume_scheduler()
            >>> executor.get_scheduled_tasks()
            {1: {...}}
        """
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.logger.warning("Scheduler already running")
            return
            
        self.stop_scheduler.clear()
        self._start_scheduler()
        self.logger.info("Scheduler resumed")

    def get_scheduled_tasks(self) -> Dict[int, Dict[str, Any]]:
        """Get snapshot of currently scheduled tasks.
        
        Returns:
            Dict[int, Dict]: Copy of tasks dictionary
            
        Examples:
            >>> tasks = executor.get_scheduled_tasks()
            >>> print(tasks.keys())
            dict_keys([1, 2])
        """
        self.logger.debug("Returning tasks snapshot")
        return {k: v.copy() for k, v in self.scheduled_tasks.items()}

    def _trigger_task(self, task_id: int) -> None:
        """Internal method to launch task execution thread.
        
        Args:
            task_id (int): ID of task to trigger
        """
        try:
            task = self.scheduled_tasks[task_id]
            task['last_run'] = time.time()
            
            thread = threading.Thread(
                target=self._execute_scheduled_task,
                args=(task_id,),
                name=f"TaskExecutor-{task_id}"
            )
            thread.start()
            
            if task['type'] == 'at':
                task['fired'] = True
                self.logger.info(f"Triggered one-time task {task_id}")
            else:
                self.logger.debug(f"Triggered interval task {task_id}")

        except KeyError:
            self.logger.error(f"Failed to trigger missing task {task_id}")
        except Exception as e:
            self.logger.error(f"Task trigger failed: {str(e)}", exc_info=True)

    def _start_scheduler(self) -> None:
        """Initialize and start scheduler background thread."""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.logger.warning("Scheduler thread already running")
            return

        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="TaskScheduler"
        )
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        self.logger.info("Scheduler thread started")

    def __del__(self):
        """Cleanup resources and stop scheduler on object destruction."""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.stop_scheduler.set()
            try:
                if self.scheduler_thread is not threading.current_thread():
                    self.scheduler_thread.join(timeout=0.5)
            except RuntimeError:
                pass
            self.logger.info("Scheduler thread stopped")

    def _handle_task_removal(self, task_id: int) -> None:
        """Internal helper for task cleanup operations.
        
        Args:
            task_id (int): ID of task to clean up
        """
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            self.logger.debug(f"Internal cleanup for task {task_id}")

    def set_working_directory(self, path: str) -> None:
        """Update default working directory for command execution.
        
        Args:
            path (str): Valid directory path
            
        Raises:
            NotADirectoryError: If path is invalid
            
        Examples:
            >>> executor.set_working_directory("C:/projects")
        """
        new_path = Path(path)
        if not new_path.is_dir():
            error_msg = f"Invalid directory: {path}"
            self.logger.error(error_msg)
            raise NotADirectoryError(error_msg)
        
        new_path.mkdir(exist_ok=True, parents=True)
        self.working_dir = new_path.resolve()
        self.logger.info(f"Updated working directory to: {self.working_dir}")

    def export_environment(self) -> Dict[str, str]:
        """Get current environment variables configuration.
        
        Returns:
            Dict[str, str]: Copy of environment variables
            
        Examples:
            >>> env = executor.export_environment()
            >>> env.update({"DEBUG": "true"})
            >>> executor.set_environment(env)
        """
        return self.env_vars.copy()

    def reset_environment(self) -> None:
        """Reset environment variables to system defaults.
        
        Examples:
            >>> executor.reset_environment()
            >>> executor.export_environment()
            {}
        """
        self.env_vars.clear()
        self.logger.info("Environment variables reset")

    def _validate_task_structure(self, task: Dict) -> bool:
        """Internal validation for task dictionary integrity.
        
        Returns:
            bool: True if task structure is valid
        """
        required_keys = {
            'type', 'command', 'active', 
            'last_run', 'max_runs', 'run_count'
        }
        return all(key in task for key in required_keys)
    