import time
from pynput import mouse
from collections import deque
import obspython as S

version = '1.0.0'
text_format = 'CPS'

click_times_left = deque(maxlen=200)
click_times_right = deque(maxlen=200)
last_update_time = time.time()

listener = None
listener_thread = None

def calculate_cps(click_times):
    current_time = time.time()

    while click_times and current_time - click_times[0] > 1:
        click_times.popleft()

    return len(click_times)

def on_click(x, y, button, pressed):
    if pressed:
        if button == mouse.Button.left:
            click_times_left.append(time.time())
        elif button == mouse.Button.right:
            click_times_right.append(time.time())

def update_display():
    left_cps = calculate_cps(click_times_left)
    right_cps = calculate_cps(click_times_right)
    display_text = f"[{left_cps} | {right_cps}]"
    
    text = S.obs_get_source_by_name(text_format)
    if text is not None:
        settings = S.obs_source_get_settings(text)
        S.obs_data_set_string(settings, 'text', display_text)
        S.obs_source_update(text, settings)
        S.obs_source_release(text)
        S.obs_data_release(settings)

def execute():
    update_display()

def start_listener():
    global listener
    listener = mouse.Listener(on_click=on_click)
    listener.start()

def stop_listener():
    global listener
    if listener is not None:
        listener.stop()
        listener.join()
        listener = None

def script_description():
    return f'CPS v{version}'

def script_update(settings):
    global listener, listener_thread, click_times_left, click_times_right
    
    click_times_left.clear()
    click_times_right.clear()

    if listener is None:
        start_listener()

    S.timer_add(execute, 25)

def script_load(settings):
    script_update(settings)

def script_unload():
    stop_listener()