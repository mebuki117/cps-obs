import time
from pynput import mouse
from collections import deque
import obspython as S

version = '1.1.0'

click_times_left = deque(maxlen=200)
click_times_right = deque(maxlen=200)

listener = None
text_source_name = ""
format_string = ""


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
    if not text_source_name:
        return

    left_cps = calculate_cps(click_times_left)
    right_cps = calculate_cps(click_times_right)
    total_cps = left_cps + right_cps

    display_text = (
        format_string
        .replace("%left%", str(left_cps))
        .replace("%right%", str(right_cps))
        .replace("%total%", str(total_cps))
    )

    text = S.obs_get_source_by_name(text_source_name)
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
    return f'CPS Counter v{version}\n\n' \
           "Available Placeholders: %left%, %right%, %total%"


def script_properties():
    props = S.obs_properties_create()

    p = S.obs_properties_add_list(
        props,
        "text_source_name",
        "Text Source",
        S.OBS_COMBO_TYPE_EDITABLE,
        S.OBS_COMBO_FORMAT_STRING,
    )

    sources = S.obs_enum_sources()
    if sources is not None:
        for source in sources:
            source_id = S.obs_source_get_unversioned_id(source)
            if source_id in ("text_gdiplus", "text_ft2_source"):
                name = S.obs_source_get_name(source)
                S.obs_property_list_add_string(p, name, name)
        S.source_list_release(sources)

    S.obs_properties_add_text(
        props,
        "format_string",
        "Display Format\n(Example: [ %left% | %right%])",
        S.OBS_TEXT_DEFAULT
    )

    return props


def script_update(settings):
    global listener, text_source_name, click_times_left, click_times_right, format_string
    text_source_name = S.obs_data_get_string(settings, "text_source_name")
    format_string = S.obs_data_get_string(settings, "format_string")

    click_times_left.clear()
    click_times_right.clear()

    if listener is None:
        start_listener()

    S.timer_add(execute, 25)


def script_load(settings):
    script_update(settings)


def script_unload():
    stop_listener()
