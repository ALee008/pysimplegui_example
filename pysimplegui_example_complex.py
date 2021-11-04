import multiprocessing
import sys
import json
import pathlib
import decimal

from loguru import logger
import PySimpleGUI as sg

decimal.getcontext().prec = 6

logger.add(pathlib.Path(r".\my_log_path.log"), mode="w")
sg.theme('DarkGreen4')
sg.user_settings_filename("my_gui_settings.json", pathlib.Path(__file__).parent)

# SETTINGS
current_path = pathlib.Path(sys.executable)
SETTINGS_FILE_PATH = current_path.joinpath(current_path.parent, r'settings_file.json')
DEFAULT_SETTINGS = {'path_power': None, 'path_gas': None
                    , 'export_path_power': None
                    , 'export_path_gas': None
                    }
# "Map" from the settings dictionary keys to the window's element keys
SETTINGS_KEYS_TO_ELEMENT_KEYS = dict.fromkeys(DEFAULT_SETTINGS)
SETTINGS_KEYS_TO_ELEMENT_KEYS['path_power'] = '-PATH_POWER-'
SETTINGS_KEYS_TO_ELEMENT_KEYS['path_gas'] = '-PATH_GAS-'
SETTINGS_KEYS_TO_ELEMENT_KEYS['export_path_power'] = '-EXPORT_PATH_POWER-'
SETTINGS_KEYS_TO_ELEMENT_KEYS['export_path_gas'] = '-EXPORT_PATH_GAS-'


def load_settings(settings_file: str, default_settings: dict):
    """load settings file"""
    try:
        with open(settings_file, 'r') as f:
            settings = json.load(f)
    except Exception as e:
        sg.popup_quick_message(f'exception {e}', 'No settings file found... will create one for you',
                               keep_on_top=True, background_color='red', text_color='white')
        settings = default_settings
        save_settings(settings_file, settings, None)
    return settings


def save_settings(settings_file: str, settings: dict, values: list):
    if values:  # if there are stuff specified by another window, fill in those values
        for key in SETTINGS_KEYS_TO_ELEMENT_KEYS:  # update window with the values read from settings file
            try:
                settings[key] = values[SETTINGS_KEYS_TO_ELEMENT_KEYS[key]]
            except Exception as e:
                print(f'Problem updating settings from window values. Key = {key}')

    with open(settings_file, 'w') as f:
        json.dump(settings, f)

    print("Saving global settings successful.")
    logger.info("Saving global settings successful.")


def report_an_error(dummy) -> None:
    sg.popup("An error has occurred. Please check log my_log_path.log file for details.")
    return None


@logger.catch(onerror=report_an_error)
def prepare_parameters(value: dict, settings) -> dict:
    """"""
    # create function that first converts "," to ".
    float_ = lambda x: float(x.replace(",", "."))
    if value["-GAS-"]:
        import_path_spot_prices = settings["path_gas"]
        import_path = pathlib.Path(import_path_spot_prices)
        export_path = settings["export_path_gas"]
    else:
        import_path_spot_prices = settings["path_power"]
        import_path = pathlib.Path(import_path_spot_prices)
        export_path = settings["export_path_power"]

    params = {'interest_rate': float_(value['-IR-']) / 36000,
              'start_date': value['-CAL_START-'],
              'end_date': value['-CAL_END-'],
              'use_scenarios': int(value['-NUM_SCENARIOS-']),
              'initial_storage_volume': float_(value['-INIT_VOL-']),
              'speicher_wert_besteht': True if value['-SPEICHERWERT-'] == 'Yes' else False,
              'ausspeicherleistung_min_max': [float_(value['-AUS_L_MIN-']), float_(value['-AUS_L_MAX-'])],
              'einspeicherleistung_min_max': [float_(value['-EIN_L_MIN-']), float_(value['-EIN_L_MAX-'])],
              'total_min_max_volume': [float_(value['-TOT_VOL_MIN-']), float_(value['-TOT_VOL_MAX-'])],
              'vol_min_max_start': [float_(value['-VOL_START_MIN-']), float_(value['-VOL_START_MAX-'])],
              'vol_min_max_end': [float_(value['-VOL_END_MIN-']), float_(value['-VOL_END_MAX-'])],
              'inject_costs': float_(value['-INJ_COSTS-']),
              'eject_costs': float_(value['-EJ_COSTS-']),
              'run_delta': True if value['-RUN_DELTA-'] == 'Yes' else False,
              'variation': float_(value['-VARIATION-']),
              'up': 1 if 'UP' in value['-ACTION-'] else 0,  # to activate up direction set value to 1
              'down': -1 if 'DOWN' in value['-ACTION-'] else 0,  # to activate down direction set value to -1
              'means_only': True if value['-MEANS_ONLY-'] == 'Yes' else False,
              'show_statistics': True if value['-SHOW_STATISTICS-'] == 'Yes' else False,
              'export_path': export_path,
              }

    return params


def check_assertions(params: dict) -> bool:
    """Return True if all checks succeed, False otherwise."""
    error_message = "Parameter Input Problem: {} = {} <= {} = {} <= {} = {} not met -> aborting calculation."
    error_message1 = "Parameter Input Problem: {} = {} <= {} = {} not met -> aborting calculation."
    try:
        assert params['vol_min_max_start'][0] <= params['initial_storage_volume'] <= params['vol_min_max_start'][
            1], error_message.format('Volume Start (min)', params['vol_min_max_start'][0],
                                     'Initial Storage Volume', params['initial_storage_volume'],
                                     'Volume Start (max)', params['vol_min_max_start'][1])
        assert params['total_min_max_volume'][0] <= params['initial_storage_volume'] <= params['total_min_max_volume'][
            1], error_message.format('Total Volume (min)', params['total_min_max_volume'][0],
                                     'Initial Storage Volume', params['initial_storage_volume'],
                                     'Total Volume (max)', params['total_min_max_volume'][1])

        assert params['vol_min_max_end'][0] <= params['total_min_max_volume'][0], error_message1.format(
            'Volume End (min)', params['vol_min_max_end'][0], 'Total Volume (min)', params['total_min_max_volume'][0]
        )
        assert params['vol_min_max_end'][1] <= params['total_min_max_volume'][1], error_message1.format(
            'Volume End (max)', params['vol_min_max_end'][1], 'Total Volume (max)', params['total_min_max_volume'][1]
        )
    except AssertionError as msg:
        logger.warning(msg)
        sg.Popup(msg, title="Invalid Parameters")
        return False

    return True


@logger.catch(onerror=report_an_error)
def run(params):
    """"""
    params_without_S = params.copy()
    params_without_S.update({'S': 'removed from log.'})
    params_without_S.update({'date_range': 'removed from log.'})
    logger.info(params_without_S)


start_lsm = "Start LSM"


# Create main window
def create_main_window() -> sg.Window:
    """"""
    # Layout the design of the GUI
    frame_data_layout = [
        [sg.CalendarButton('Start Date',
                           target='-CAL_START-',
                           format='%Y-%m-%d',
                           begin_at_sunday_plus=1),
         sg.Input(sg.user_settings_get_entry('start_date', ''), key='-CAL_START-', size=(10, 1))],
        [sg.CalendarButton('End Date ',
                           target='-CAL_END-',
                           format='%Y-%m-%d',
                           begin_at_sunday_plus=1),
         sg.Input(sg.user_settings_get_entry('end_date', ''), key='-CAL_END-', size=(10, 1))],
        [sg.Text('Number of Scenarios'), sg.Input(sg.user_settings_get_entry('num_scenarios', ''),
                                                  key='-NUM_SCENARIOS-',
                                                  enable_events=True
                                                  , size=(10, 1))],
    ]

    mwh_objects_1 = [
        [sg.Text('Total Volume (min) [MWh]'),
         sg.Input(sg.user_settings_get_entry('tot_vol_min', ''), key='-TOT_VOL_MIN-', enable_events=True,
                  size=(10, 1))],
        [sg.Text('Total Volume (max) [MWh]'),
         sg.Input(sg.user_settings_get_entry('tot_vol_max', ''), key='-TOT_VOL_MAX-', enable_events=True,
                  size=(10, 1))],
        [sg.Text('Volume Start (min) [MWh]'),
         sg.Input(sg.user_settings_get_entry('vol_start_min', ''), key='-VOL_START_MIN-', enable_events=True,
                  size=(10, 1))],
        [sg.Text('Volume Start (max) [MWh]'),
         sg.Input(sg.user_settings_get_entry('vol_start_max', ''), key='-VOL_START_MAX-', enable_events=True,
                  size=(10, 1))],
        [sg.Text('Volume End (min) [MWh]'),
         sg.Input(sg.user_settings_get_entry('vol_end_min', ''), key='-VOL_END_MIN-', enable_events=True,
                  size=(10, 1))],
        [sg.Text('Volume End (max) [MWh]'),
         sg.Input(sg.user_settings_get_entry('vol_end_max', ''), key='-VOL_END_MAX-', enable_events=True,
                  size=(10, 1))],
        [sg.Text('Initial Storage Volume [MWh]'),
         sg.Input(sg.user_settings_get_entry('init_vol', ''), key='-INIT_VOL-', enable_events=True, size=(10, 1))],
        ]
    mw_objects = [
        [sg.Text('Einspeicherleistung (min) [MW]'),
         sg.Input(sg.user_settings_get_entry('einspeicher_leistung_min', ''), key='-EIN_L_MIN-', enable_events=True,
                  size=(10, 1))],
        [sg.Text('Einspeicherleistung (max) [MW]'),
         sg.Input(sg.user_settings_get_entry('einspeicher_leistung_max', ''), key='-EIN_L_MAX-', enable_events=True,
                  size=(10, 1))],
        [sg.Text('Ausspeicherleistung (min) [MW]'),
         sg.Input(sg.user_settings_get_entry('ausspeicher_leistung_min', ''), key='-AUS_L_MIN-', enable_events=True,
                  size=(10, 1))],
        [sg.Text('Ausspeicherleistung (max) [MW]'),
         sg.Input(sg.user_settings_get_entry('ausspeicher_leistung_max', ''), key='-AUS_L_MAX-', enable_events=True,
                  size=(10, 1))],
        ]
    mwh_objects_2 = [
        [sg.Text('Einspeicherarbeit (min) [MWh]'),
         sg.Text(sg.user_settings_get_entry('einspeicher_arbeit_min', ''), key='-EIN_A_MIN-', enable_events=True,
                  size=(10, 1))],
        [sg.Text('Einspeicherarbeit (max) [MWh]'),
         sg.Text(sg.user_settings_get_entry('einspeicher_arbeit_max', ''), key='-EIN_A_MAX-', enable_events=True,
                  size=(10, 1))],
        [sg.Text('Ausspeicherarbeit (min) [MWh]'),
         sg.Text(sg.user_settings_get_entry('ausspeicher_arbeit_min', ''), key='-AUS_A_MIN-', enable_events=True,
                  size=(10, 1))],
        [sg.Text('Ausspeicherarbeit (max) [MWh]'),
         sg.Text(sg.user_settings_get_entry('ausspeicher_arbeit_max', ''), key='-AUS_A_MAX-', enable_events=True,
                  size=(10, 1))],
        ]
    misc_objects = [
        [sg.Text('Inject Costs [€/MWh]'),
         sg.Input(sg.user_settings_get_entry('inject_costs', ''), key='-INJ_COSTS-', enable_events=True,
                  size=(10, 1))],
        [sg.Text('Eject Costs [€/MWh]'),
         sg.Input(sg.user_settings_get_entry('eject_costs', ''), key='-EJ_COSTS-', enable_events=True,
                  size=(10, 1))],
        [sg.Text('Speicherwert Besteht?', ),
         sg.DropDown(('Yes', 'No'), default_value=sg.user_settings_get_entry('speicherwert'), key='-SPEICHERWERT-')],
    ]

    delta_calculation_frame = [
        [sg.Text('Run Delta Calculation?'),
         sg.DropDown(('Yes', 'No'), default_value=sg.user_settings_get_entry('run_delta'), key='-RUN_DELTA-')],
        [sg.Text('Price Variation [€/MWh]'),
         sg.Input(sg.user_settings_get_entry('variation', ''), key='-VARIATION-', enable_events=True,
                  size=(10, 1))],
        [sg.Text('UP/DOWN MODE'),
         sg.DropDown(('UP&DOWN', ), key='-ACTION-', default_value=sg.user_settings_get_entry('action'),
                     size=(10, 1))],
    ]

    misc_frame = [
        [sg.Text('Calculate Means Only?'),
         sg.DropDown(('Yes', 'No'), key='-MEANS_ONLY-', default_value=sg.user_settings_get_entry('means_only'))],
        [sg.Text('Show Statistics'),
         sg.DropDown(('Yes', 'No'), key='-SHOW_STATISTICS-',
                     default_value=sg.user_settings_get_entry('show_statistics'))],
    ]
    frame_layout = [
        [sg.Radio('Gas', 'RADIO1', default=True, key='-GAS-'), sg.Radio('Power', 'RADIO1', key='-POWER-')],
        [sg.Text('interest rate p.a. (in %)'),
         sg.Input(sg.user_settings_get_entry('interest_rate', ''), key='-IR-', enable_events=True, size=(10, 1))],
        [sg.Text('interest rate p.a.:'), sg.Text("", key='-IR_PA-', enable_events=True, size=(8, 1))],
        [sg.Frame('Data Info', frame_data_layout)],
        [sg.Frame('Volumes', mwh_objects_1, element_justification="right")],
    ]
    right_frame_layout = [
        [sg.Frame('Delta Calculation Parameters', delta_calculation_frame, element_justification="right")],
        [sg.Frame('Misc Settings', misc_frame, element_justification="right")],
        [sg.Button(start_lsm, disabled=True), sg.Quit(), sg.B('Save'), sg.B('Settings')],
    ]
    width, height = sg.Window.get_screen_size()
    window_width, window_height, output_height = round(0.77 * width), round(0.75 * height), round(0.15 * height)
    layout = [
        [
            sg.Column([[sg.Frame('User Inputs', frame_layout)]], ),
            sg.Column([
                [sg.Frame('Volumes', mw_objects, element_justification="right")],
                [sg.Frame('Volumes', mwh_objects_2, element_justification="right")],
                [sg.Frame('Costs', misc_objects, element_justification="right")],
                ]),
            sg.Column([
                [sg.Image(filename="./logo.png", size=(260, 260))],
                [sg.Frame('User Inputs', right_frame_layout)],
            ]),
        ],
        [sg.Output(size=(window_width, output_height), key='-LOG-', echo_stdout_stderr=True, font="Any 8")],
    ]
    # Show the Window to the user
    window = sg.Window('Simulation Tool', layout, size=(window_width, window_height), font="Any 11")

    return window


# Make a Settings Window
def create_settings_window(settings):
    d = SETTINGS_KEYS_TO_ELEMENT_KEYS

    def TextLabel(text, object_type=""):
        text_label_object = sg.Text(text + ':', justification='r', size=(20, 1))
        if object_type == 'text':
            return text_label_object

        input_object = sg.Input(key=d[text])
        if object_type == 'folder':
            return [text_label_object, input_object, sg.FolderBrowse(target=d[text])]

        return [text_label_object, input_object]

    layout = [[sg.Text('Settings')],
              TextLabel("path_power", "folder"),
              TextLabel("path_gas", "folder"),
              TextLabel('export_path_power', "folder"),
              TextLabel('export_path_gas', "folder"),
              [sg.Button('Save Settings'), sg.Button('OK')]]

    window = sg.Window('Settings', layout, keep_on_top=True, finalize=True)

    for key in SETTINGS_KEYS_TO_ELEMENT_KEYS:  # update window with the values read from settings file
        try:
            window[SETTINGS_KEYS_TO_ELEMENT_KEYS[key]].update(value=settings[key])
        except Exception as e:
            print(f'Problem updating PySimpleGUI window from settings. Key = {key}')

    return window


def save_user_settings(value):
    """Default path for json-file is documented here: https://github.com/PySimpleGUI/PySimpleGUI/issues/3371
    On Windows this is the default path: \\user\\username\\AppData\\Local\\PySimpleGUI\\settings"""
    sg.user_settings_set_entry('interest_rate', value['-IR-'])
    sg.user_settings_set_entry('start_date', value['-CAL_START-'])
    sg.user_settings_set_entry('end_date', value['-CAL_END-'])
    sg.user_settings_set_entry('num_scenarios', value['-NUM_SCENARIOS-'])
    sg.user_settings_set_entry('init_vol', value['-INIT_VOL-'])
    sg.user_settings_set_entry('speicherwert', value['-SPEICHERWERT-'])
    sg.user_settings_set_entry('ausspeicher_leistung_min', value['-AUS_L_MIN-'])
    sg.user_settings_set_entry('ausspeicher_leistung_max', value['-AUS_L_MAX-'])
    sg.user_settings_set_entry('einspeicher_leistung_min', value['-EIN_L_MIN-'])
    sg.user_settings_set_entry('einspeicher_leistung_max', value['-EIN_L_MAX-'])
    sg.user_settings_set_entry('tot_vol_min', value['-TOT_VOL_MIN-'])
    sg.user_settings_set_entry('tot_vol_max', value['-TOT_VOL_MAX-'])
    sg.user_settings_set_entry('vol_start_min', value['-VOL_START_MIN-'])
    sg.user_settings_set_entry('vol_start_max', value['-VOL_START_MAX-'])
    sg.user_settings_set_entry('vol_end_min', value['-VOL_END_MIN-'])
    sg.user_settings_set_entry('vol_end_max', value['-VOL_END_MAX-'])
    sg.user_settings_set_entry('inject_costs', value['-INJ_COSTS-'])
    sg.user_settings_set_entry('eject_costs', value['-EJ_COSTS-'])
    sg.user_settings_set_entry('run_delta', value['-RUN_DELTA-'])
    sg.user_settings_set_entry('variation', value['-VARIATION-'])
    sg.user_settings_set_entry('action', value['-ACTION-'])
    sg.user_settings_set_entry('means_only', value['-MEANS_ONLY-'])
    sg.user_settings_set_entry('show_statistics', value['-SHOW_STATISTICS-'])
    print("Saving user settings successful.")
    logger.info("Saving user settings successful.")

    return None


def check_float(window, event, value, key):
    if event == key and value[key] and value[key][-1] not in '0123456789.,':
        window[key].update(value[key][:-1])


def check_int(window, event, value, key):
    if event == key and value[key] and value[key][-1] not in '0123456789':
        window[key].update(value[key][:-1])


def calculate_arbeit(leistung: str) -> str:
    # check if leistung exists. Might be empty if user deletes input that creates 'leistung'.
    if leistung:
        leistung = leistung.replace(",", ".")
        # try converting leistung to float. Might fail if user tries to type non-valid characters that are passed here
        # from the coller.
        try:
            return str(int(float(leistung) * 24))
        except ValueError:
            pass


def main():
    # Event loop. Read buttons, make callbacks
    window, settings = None, load_settings(SETTINGS_FILE_PATH, DEFAULT_SETTINGS)
    while True:
        # Read the Window
        if window is None:
            window = create_main_window()
        event, value = window.read()
        if event in ('Quit', sg.WIN_CLOSED):
            break
        if event == 'Settings':
            event, settings_value = create_settings_window(settings).read(close=True)
            if event == 'Save Settings':
                window.close()
                window = None
                save_settings(SETTINGS_FILE_PATH, settings, settings_value)
        # check if initial prices are of type float
        check_int(window, event, value, '-NUM_SCENARIOS-')
        check_float(window, event, value, '-TOT_VOL_MIN-')
        check_float(window, event, value, '-TOT_VOL_MAX-')
        check_float(window, event, value, '-INIT_VOL-')
        check_float(window, event, value, '-AUS_L_MIN-')
        if event in ('-AUS_L_MIN-', 'Save', start_lsm):
            arbeit = calculate_arbeit(value['-AUS_L_MIN-'])
            window['-AUS_A_MIN-'].update(arbeit)
        check_float(window, event, value, '-AUS_L_MAX-')
        if event in ('-AUS_L_MAX-', 'Save', start_lsm):
            arbeit = calculate_arbeit(value['-AUS_L_MAX-'])
            window['-AUS_A_MAX-'].update(arbeit)
        check_float(window, event, value, '-EIN_L_MIN-')
        if event in ('-EIN_L_MIN-', 'Save', start_lsm):
            arbeit = calculate_arbeit(value['-EIN_L_MIN-'])
            window['-EIN_A_MIN-'].update(arbeit)
        check_float(window, event, value, '-EIN_L_MAX-')
        if event in ('-EIN_L_MAX-', 'Save', start_lsm):
            arbeit = calculate_arbeit(value['-EIN_L_MAX-'])
            window['-EIN_A_MAX-'].update(arbeit)
        check_float(window, event, value, '-VOL_START_MIN-')
        check_float(window, event, value, '-VOL_START_MAX-')
        check_float(window, event, value, '-VOL_END_MIN-')
        check_float(window, event, value, '-VOL_END_MAX-')
        check_float(window, event, value, '-INJ_COSTS-')
        check_float(window, event, value, '-EJ_COSTS-')
        check_float(window, event, value, '-VARIATION-')
        check_float(window, event, value, '-IR-')
        ir = value['-IR-'].replace(",", ".")
        if not ir:
            ir = '0.'
        ir_per_annum = decimal.Decimal(ir) / 360
        ir_percent = str(round(ir_per_annum.normalize(), 4)) + '%'
        if event == 'Save':
            window["-IR_PA-"].update(ir_percent)
            save_user_settings(value)
        if event == start_lsm:
            window["-IR_PA-"].update(ir_percent)
            params = prepare_parameters(value, settings)
            if check_assertions(params):
                run(params)
            print("Calculation finished.")

    window.close()


if __name__ == '__main__':
    main()
