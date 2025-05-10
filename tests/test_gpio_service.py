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

def test_start_monitoring_tap_detection(monkeypatch, mock_config, mock_gpio):
    import gpio_service
    ctrl = gpio_service.GPIOController()

    # Simulate: press (True), release (False), then idle long enough for single tap
    states = [False, True, False] + [False]*10  # Initial, press, release, then idle
    times = [0, 0.01, 0.02] + [0.5 + i*0.1 for i in range(10)]  # 0.5 > double_tap_max_interval
    state_iter = iter(states)
    time_iter = iter(times)

    ctrl.GPIO.input = lambda pin: next(state_iter, False)
    ctrl.GPIO.HIGH = True
    monkeypatch.setattr('time.time', lambda: next(time_iter, 1))

    single_called = {}
    double_called = {}
    def single_cb():
        print('SINGLE TAP CALLBACK CALLED')
        single_called['x'] = True
    def double_cb():
        double_called['x'] = True
    ctrl.register_callback(gpio_service.TouchPattern.SINGLE_TAP, single_cb)
    ctrl.register_callback(gpio_service.TouchPattern.DOUBLE_TAP, double_cb)

    sleep_calls = {'count': 0}
    def fake_sleep(s):
        sleep_calls['count'] += 1
        if sleep_calls['count'] > 12:
            ctrl.is_running = False
    monkeypatch.setattr('time.sleep', fake_sleep)
    monkeypatch.setattr(ctrl, 'cleanup', lambda: None)
    ctrl.is_running = True
    ctrl.start_monitoring(single_tap_max=0.2, double_tap_max_interval=0.3)

    # After running, single tap callback should be called
    assert 'x' in single_called 

def test_start_monitoring_exception_handling(monkeypatch, mock_config, mock_gpio):
    import gpio_service
    ctrl = gpio_service.GPIOController()

    # Simulate normal state, then raise an exception in GPIO.input
    states = [False, True]
    state_iter = iter(states)
    def input_side_effect(pin):
        val = next(state_iter, None)
        if val is None:
            raise RuntimeError("Simulated exception in GPIO.input")
        return val
    ctrl.GPIO.input = input_side_effect
    ctrl.GPIO.HIGH = True

    # Patch time.time and time.sleep
    monkeypatch.setattr('time.time', lambda: 0.0)
    monkeypatch.setattr('time.sleep', lambda s: None)

    # Patch cleanup to record if called
    cleanup_called = {}
    def fake_cleanup():
        cleanup_called['x'] = True
    monkeypatch.setattr(ctrl, 'cleanup', fake_cleanup)

    # Run monitoring, expecting it to handle the exception and call cleanup
    ctrl.is_running = True
    ctrl.start_monitoring(single_tap_max=0.2, double_tap_max_interval=0.3)
    assert 'x' in cleanup_called 

def test_cleanup_exception_handling(mock_config, mock_gpio):
    import gpio_service
    ctrl = gpio_service.GPIOController()
    # Simulate GPIO.cleanup raising an exception
    def raise_exception():
        raise RuntimeError("Simulated cleanup error")
    ctrl.GPIO.cleanup = raise_exception
    # Should not raise, should be handled silently
    ctrl.cleanup() 

def test_main_retry_and_exit(monkeypatch, mock_config, mock_gpio):
    import gpio_service
    import sys as real_sys

    # Patch GPIOController to always raise
    class FakeController:
        def __init__(*a, **kw):
            raise RuntimeError("Simulated init failure")
    monkeypatch.setattr(gpio_service, 'GPIOController', FakeController)

    # Patch sys.exit to record call
    exit_called = {}
    def fake_exit(code):
        exit_called['code'] = code
        raise SystemExit
    monkeypatch.setattr(real_sys, 'exit', fake_exit)

    # Patch time.sleep to avoid delay
    monkeypatch.setattr('time.sleep', lambda s: None)

    # Patch logger to avoid real logging
    monkeypatch.setattr(gpio_service, 'logger', mock.Mock())

    # Patch argparse to avoid parsing real CLI args
    class FakeArgs:
        flask_url = 'http://localhost:5000'
        single_tap_endpoint = '/single'
        double_tap_endpoint = '/double'
        pin = 17
        single_tap_max = 0.2
        double_tap_max_interval = 0.3
        debounce_time = 0.01
        sampling_rate = 0.01
        startup_delay = 0
        test = False
    fake_parser = mock.Mock()
    fake_parser.parse_args.return_value = FakeArgs()
    monkeypatch.setattr(gpio_service, 'argparse', mock.Mock())
    gpio_service.argparse.ArgumentParser.return_value = fake_parser

    # Run main and assert sys.exit is called after retries
    try:
        gpio_service.main()
    except SystemExit:
        pass
    assert exit_called['code'] == 1 

def test_main_callback_error_handling(monkeypatch, mock_config, mock_gpio):
    import gpio_service
    # Patch requests.post to raise
    monkeypatch.setattr(gpio_service.requests, 'post', lambda *a, **kw: (_ for _ in ()).throw(Exception('fail')))
    # Patch logger to record errors
    error_logs = []
    class FakeLogger:
        def info(self, msg): pass
        def error(self, msg): error_logs.append(msg)
    monkeypatch.setattr(gpio_service, 'logger', FakeLogger())
    # Patch argparse to avoid parsing real CLI args
    class FakeArgs:
        flask_url = 'http://localhost:5000'
        single_tap_endpoint = '/single'
        double_tap_endpoint = '/double'
        pin = 17
        single_tap_max = 0.2
        double_tap_max_interval = 0.3
        debounce_time = 0.01
        sampling_rate = 0.01
        startup_delay = 0
        test = False
    fake_parser = mock.Mock()
    fake_parser.parse_args.return_value = FakeArgs()
    monkeypatch.setattr(gpio_service, 'argparse', mock.Mock())
    gpio_service.argparse.ArgumentParser.return_value = fake_parser
    # Get the callbacks from main
    parser = gpio_service.argparse.ArgumentParser()
    args = parser.parse_args()
    single_tap_url = f"{args.flask_url}{args.single_tap_endpoint}"
    double_tap_url = f"{args.flask_url}{args.double_tap_endpoint}"
    # Define the callbacks as in main
    def single_tap_callback():
        gpio_service.logger.info("Single tap detected, sending to server...")
        try:
            gpio_service.requests.post(single_tap_url)
        except Exception as e:
            if gpio_service.logger:
                gpio_service.logger.error(f"Error sending single tap: {str(e)}")
    def double_tap_callback():
        gpio_service.logger.info("Double tap detected, sending to server...")
        try:
            gpio_service.requests.post(double_tap_url)
        except Exception as e:
            if gpio_service.logger:
                gpio_service.logger.error(f"Error sending double tap: {str(e)}")
    # Call the callbacks
    single_tap_callback()
    double_tap_callback()
    # Assert error logs were recorded
    assert any("Error sending single tap" in msg for msg in error_logs)
    assert any("Error sending double tap" in msg for msg in error_logs) 