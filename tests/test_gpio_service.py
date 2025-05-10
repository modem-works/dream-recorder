import pytest
from unittest import mock
import sys

@pytest.fixture
def mock_config(monkeypatch):
    monkeypatch.setattr('functions.config_loader.get_config', lambda: {
        'LOG_LEVEL': 'INFO',
        'GPIO_PIN': 17,
        'GPIO_DEBOUNCE_TIME': 0.01,
        'GPIO_SAMPLING_RATE': 0.01,
        'GPIO_SINGLE_TAP_MAX_DURATION': 0.2,
        'GPIO_DOUBLE_TAP_MAX_INTERVAL': 0.3,
        'GPIO_FLASK_URL': 'http://localhost:5000',
        'GPIO_SINGLE_TAP_ENDPOINT': '/single',
        'GPIO_DOUBLE_TAP_ENDPOINT': '/double',
        'GPIO_STARTUP_DELAY': 0,
    })

@pytest.fixture
def mock_gpio(monkeypatch):
    fake_gpio = mock.Mock()
    fake_gpio.BCM = 'BCM'
    fake_gpio.IN = 'IN'
    fake_gpio.PUD_DOWN = 'PUD_DOWN'
    fake_gpio.HIGH = True
    monkeypatch.setitem(sys.modules, 'RPi', mock.Mock())
    monkeypatch.setitem(sys.modules, 'RPi.GPIO', fake_gpio)
    return fake_gpio

def test_import_and_instantiate_controller(mock_config, mock_gpio):
    import gpio_service
    ctrl = gpio_service.GPIOController()
    assert ctrl.pin == 17
    assert hasattr(ctrl, 'GPIO')

def test_register_callback_and_stop(mock_config, mock_gpio):
    import gpio_service
    ctrl = gpio_service.GPIOController()
    called = {}
    def cb(): called['x'] = True
    ctrl.register_callback(gpio_service.TouchPattern.SINGLE_TAP, cb)
    assert gpio_service.TouchPattern.SINGLE_TAP in ctrl.callbacks
    ctrl.stop_monitoring()
    assert ctrl.is_running is False

def test_cleanup(mock_config, mock_gpio):
    import gpio_service
    ctrl = gpio_service.GPIOController()
    ctrl.GPIO.cleanup = mock.Mock()
    ctrl.cleanup()
    ctrl.GPIO.cleanup.assert_called() 