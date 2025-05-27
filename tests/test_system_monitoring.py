import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from pyAdmin.system_monitoring import SystemMonitor
import psutil

@pytest.fixture
def mock_psutil():
    with patch('pyAdmin.system_monitoring.psutil') as mock:
        yield mock

def test_psutil_not_installed():
    with patch.dict('sys.modules', {'psutil': None}):
        monitor = SystemMonitor()
        assert not monitor.psutil_available
        assert monitor.get_system_status() == {}

def test_full_system_status(mock_psutil):
    # Configure mock values
    mock_psutil.disk_usage.return_value = Mock(
        total=1000000000, used=300000000, free=700000000, percent=30.0
    )
    mock_psutil.virtual_memory.return_value = Mock(
        total=16000000000, available=8000000000, used=8000000000, percent=50.0
    )
    mock_psutil.cpu_percent.return_value = 25.5
    mock_psutil.cpu_count.side_effect = [4, 8]  # physical, logical
    mock_psutil.net_io_counters.return_value = Mock(
        bytes_sent=1000, bytes_recv=2000, packets_sent=10, packets_recv=20
    )
    mock_psutil.swap_memory.return_value = Mock(
        total=4000000000, used=1000000000, free=3000000000, percent=25.0
    )
    mock_psutil.getloadavg.return_value = (0.75, 1.25, 1.0)
    mock_psutil.boot_time.return_value = 1600000000
    mock_psutil.sensors_temperatures.return_value = {
        'coretemp': [Mock(label='Core 0', current=45.0, high=90.0, critical=100.0)]
    }
    mock_psutil.pids.return_value = [1, 2, 3]

    monitor = SystemMonitor()
    status = monitor.get_system_status()

    # Disk
    assert status['disk']['total_gb'] == 0.93
    assert status['disk']['percent_used'] == 30.0

    # Memory
    assert status['memory']['available_gb'] == 7.45
    assert status['memory']['percent_used'] == 50.0

    # CPU
    assert status['cpu']['usage_percent'] == 25.5
    assert status['cpu']['cores'] == 4
    assert status['cpu']['threads'] == 8

    # Network
    assert status['network']['bytes_sent'] == 1000

    # Swap
    assert status['swap']['free_gb'] == 2.79

    # Load average
    assert status['load_avg']['5min'] == 1.25

    # Temperatures
    assert status['temperatures']['coretemp'][0]['current'] == 45.0

    # Process count
    assert status['process_count'] == 3

def test_load_average_unavailable(mock_psutil):
    mock_psutil.getloadavg.side_effect = AttributeError
    monitor = SystemMonitor()
    assert monitor._get_load_average() == {}

def test_temperature_sensors_unavailable(mock_psutil):
    mock_psutil.sensors_temperatures.side_effect = AttributeError
    monitor = SystemMonitor()
    assert monitor._get_temperatures() == {}

from datetime import datetime
from pyAdmin.system_monitoring import SystemMonitor
from unittest.mock import patch

def test_uptime_calculation(mock_psutil):
    mock_psutil.boot_time.return_value = 1600000000
    fake_now = datetime.fromtimestamp(1600003600)

    with patch('pyAdmin.system_monitoring.datetime') as mock_datetime:
        mock_datetime.now.return_value = fake_now
        monitor = SystemMonitor()
        uptime = monitor._get_uptime()
        assert uptime == 3600.0

def test_cpu_frequency_unavailable(mock_psutil):
    mock_psutil.cpu_freq.return_value = None
    monitor = SystemMonitor()
    cpu_info = monitor._get_cpu_usage()
    assert cpu_info['frequency'] is None

def test_empty_temperature_data(mock_psutil):
    mock_psutil.sensors_temperatures.return_value = {}
    monitor = SystemMonitor()
    assert monitor._get_temperatures() == {}