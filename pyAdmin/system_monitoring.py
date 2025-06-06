"""System resource monitoring module for pyAdmin package."""

import psutil
from datetime import datetime
from typing import Dict, List, Optional
from pyAdmin.utils import bytes_to_gb


class SystemMonitor:
    """Monitor system resources and performance metrics using psutil.

    Provides comprehensive system statistics including:
    - Disk, memory, and CPU utilization
    - Network activity metrics
    - Swap memory usage
    - System load averages
    - Hardware temperatures (platform-dependent)
    - Process and uptime information

    Attributes:
        psutil_available (bool): Indicates if psutil package is installed and available.
    """

    def __init__(self) -> None:
        """Initialize system monitor and verify psutil availability.

        Automatically checks for psutil installation during initialization.
        Prints installation instructions if package is missing.
        """
        self.psutil_available = self._check_psutil()

    @staticmethod
    def _check_psutil() -> bool:
        """Verify psutil package installation status.

        Returns:
            bool: True if psutil is available, False otherwise
        """
        try:
            import psutil
            return True
        except ImportError:
            print("Error: psutil required for system monitoring.")
            print("Install with: pip install psutil")
            return False

    def get_system_status(self) -> Dict:
        """Get complete system status snapshot.

        Returns:
            Dict: Composite dictionary containing:
                - disk: Disk usage statistics (see _get_disk_usage)
                - memory: Physical memory metrics (see _get_memory_usage)
                - cpu: Processor utilization data (see _get_cpu_usage)
                - network: Network I/O counters (see _get_network_stats)
                - swap: Swap memory usage (see _get_swap_usage)
                - load_avg: System load averages (see _get_load_average)
                - uptime: System uptime in seconds (float)
                - temperatures: Sensor data if available (see _get_temperatures)
                - process_count: Running processes count (int)

            Example:
                >>> monitor = SystemMonitor()
                >>> status = monitor.get_system_status()
                >>> print(status['cpu']['usage_percent'])
                23.7

                >>> print(status['disk']['total_gb'])
                465.76
        """
        if not self.psutil_available:
            return {}

        return {
            'disk': self._get_disk_usage(),
            'memory': self._get_memory_usage(),
            'cpu': self._get_cpu_usage(),
            'network': self._get_network_stats(),
            'swap': self._get_swap_usage(),
            'load_avg': self._get_load_average(),
            'uptime': self._get_uptime(),
            'temperatures': self._get_temperatures(),
            'process_count': self._get_process_count()
        }

    def _get_disk_usage(self) -> Dict[str, float]:
        """Get root partition disk usage statistics.

        Returns:
            Dict: Disk metrics with keys:
                - total_gb: Total space in gigabytes (float)
                - used_gb: Used space in gigabytes (float)
                - free_gb: Free space in gigabytes (float)
                - percent_used: Usage percentage (float)

            Example:
                >>> monitor._get_disk_usage()
                {'total_gb': 465.76, 'used_gb': 230.15,
                 'free_gb': 235.61, 'percent_used': 49.4}
        """
        disk = psutil.disk_usage('/')
        return {
            'total_gb': round(bytes_to_gb(disk.total), 2),
            'used_gb': round(bytes_to_gb(disk.used), 2),
            'free_gb': round(bytes_to_gb(disk.free), 2),
            'percent_used': disk.percent
        }

    def _get_memory_usage(self) -> Dict[str, float]:
        """Get physical memory utilization metrics.

        Returns:
            Dict: Memory metrics with keys:
                - total_gb: Total RAM in gigabytes (float)
                - available_gb: Available RAM in gigabytes (float)
                - used_gb: Used RAM in gigabytes (float)
                - percent_used: Usage percentage (float)

            Example:
                >>> monitor._get_memory_usage()
                {'total_gb': 15.6, 'available_gb': 8.2,
                 'used_gb': 7.4, 'percent_used': 47.4}
        """
        memory = psutil.virtual_memory()
        return {
            'total_gb': round(bytes_to_gb(memory.total), 2),
            'available_gb': round(bytes_to_gb(memory.available), 2),
            'used_gb': round(bytes_to_gb(memory.used), 2),
            'percent_used': memory.percent
        }

    def _get_cpu_usage(self) -> Dict[str, Optional[float]]:
        """Collect CPU performance metrics.

        Returns:
            Dict: CPU metrics with keys:
                - usage_percent: Current load percentage (float)
                - cores: Physical core count (int)
                - threads: Logical thread count (int)
                - frequency: Current clock speed (GHz) (float or None if unavailable)

            Example:
                >>> monitor._get_cpu_usage()
                {'usage_percent': 32.1, 'cores': 4,
                 'threads': 8, 'frequency': 3.6}
        """
        return {
            'usage_percent': psutil.cpu_percent(interval=0.5),
            'cores': psutil.cpu_count(logical=False),
            'threads': psutil.cpu_count(logical=True),
            'frequency': getattr(psutil.cpu_freq(), 'current', None)
        }

    def _get_network_stats(self) -> Dict[str, int]:
        """Get network input/output counters.

        Returns:
            Dict: Network metrics with keys:
                - bytes_sent: Total bytes sent (int)
                - bytes_recv: Total bytes received (int)
                - packets_sent: Total packets sent (int)
                - packets_recv: Total packets received (int)

            Example:
                >>> monitor._get_network_stats()
                {'bytes_sent': 4589321, 'bytes_recv': 7832104,
                 'packets_sent': 12045, 'packets_recv': 18567}
        """
        net = psutil.net_io_counters()
        return {
            'bytes_sent': net.bytes_sent,
            'bytes_recv': net.bytes_recv,
            'packets_sent': net.packets_sent,
            'packets_recv': net.packets_recv
        }

    def _get_swap_usage(self) -> Dict[str, float]:
        """Retrieve swap memory utilization statistics.

        Returns:
            Dictionary with keys:
            - total_gb: Total swap space in gigabytes (float)
            - used_gb: Used swap space in gigabytes (float)
            - free_gb: Free swap space in gigabytes (float)
            - percent_used: Percentage of swap used (float)

        Example:
            >>> monitor._get_swap_usage()
            {'total_gb': 4.0, 'used_gb': 0.32,
             'free_gb': 3.68, 'percent_used': 8.0}
        """
        swap = psutil.swap_memory()
        return {
            'total_gb': round(bytes_to_gb(swap.total), 2),
            'used_gb': round(bytes_to_gb(swap.used), 2),
            'free_gb': round(bytes_to_gb(swap.free), 2),
            'percent_used': swap.percent
        }

    def _get_load_average(self) -> Dict[str, Optional[float]]:
        """Get system load averages for 1, 5 and 15 minute intervals.

        Returns:
            Dictionary with keys:
            - 1min: 1-minute load average (float)
            - 5min: 5-minute load average (float)
            - 15min: 15-minute load average (float)

            Returns empty dict if not supported

        Example:
            >>> monitor._get_load_average()
            {'1min': 0.75, '5min': 1.2, '15min': 0.95}
        """
        try:
            load = psutil.getloadavg()
            return {'1min': load[0], '5min': load[1], '15min': load[2]}
        except AttributeError:
            return {}

    def _get_uptime(self) -> float:
        """Calculate system uptime in seconds since last boot.

        Returns:
            Uptime duration in seconds as floating point number

        Example:
            >>> monitor._get_uptime()
            123456.78  # 34 hours 17 minutes
        """
        return datetime.now().timestamp() - psutil.boot_time()

    def _get_temperatures(self) -> Dict[str, List[Dict]]:
        """Retrieve hardware temperature sensor readings.

        Returns:
            Nested dictionary with structure:
            {
                'sensor_name': [
                    {
                        'label': Sensor label (str),
                        'current': Current temperature in °C (float),
                        'high': High threshold in °C (float or None),
                        'critical': Critical threshold in °C (float or None)
                    },
                    ...
                ]
            }

            Returns empty dictionary if no sensors available or unsupported.

        Example:
            >>> monitor._get_temperatures()
            {
                'acpitz': [
                    {'label': '', 'current': 45.0, 'high': 90.0, 'critical': 100.0}
                ],
                'coretemp': [
                    {'label': 'Core 0', 'current': 56.0, 'high': 100.0, 'critical': 100.0},
                    {'label': 'Core 1', 'current': 54.0, 'high': 100.0, 'critical': 100.0}
                ]
            }
        """
        try:
            temps = psutil.sensors_temperatures()
            return {
                sensor: [{
                    'label': entry.label,
                    'current': entry.current,
                    'high': entry.high,
                    'critical': entry.critical
                } for entry in entries]
                for sensor, entries in temps.items()
            }
        except AttributeError:
            return {}

    def _get_process_count(self) -> int:
        """Count currently running processes.

        Returns:
            Integer representing number of active processes

        Example:
            >>> monitor._get_process_count()
            137  # Typical value for desktop system
        """
        return len(psutil.pids())
