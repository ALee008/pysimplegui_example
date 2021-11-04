import sys
import json
import pathlib

from loguru import logger
import PySimpleGUI as sg

logger.add(pathlib.Path(r".\mein_log_pfad.log"), mode="w")
sg.theme('DarkGreen4')

# SETTINGS
current_path = pathlib.Path(sys.executable)
SETTINGS_FILE_PATH = current_path.joinpath(current_path.parent, r'settings_file.json')
sg.user_settings_filename("./my_gui_settings.json")
DEFAULT_SETTINGS = {'path_power': None, 'path_gas': None, 'time_step': 1, 'annualization_factor': 250,
                    'jump_distance_factor': 3
                    , 'TermPrices_YEAR.csv': None
                    , 'month_factors_mr.csv': None
                    , 'actual_spot_prices.csv': None
                    , 'month_prices.csv': None
                    , 'export_path_power': None
                    , 'export_path_gas': None
                    }

# "Map" from the settings dictionary keys to the window's element keys
SETTINGS_KEYS_TO_ELEMENT_KEYS = dict.fromkeys(DEFAULT_SETTINGS)
SETTINGS_KEYS_TO_ELEMENT_KEYS['path_reuters'] = '-PATH-REUTERS-'
SETTINGS_KEYS_TO_ELEMENT_KEYS['path_power'] = '-PATH_POWER-'
SETTINGS_KEYS_TO_ELEMENT_KEYS['path_gas'] = '-PATH_GAS-'
SETTINGS_KEYS_TO_ELEMENT_KEYS['time_step'] = '-PATH_STEP-'
SETTINGS_KEYS_TO_ELEMENT_KEYS['annualization_factor'] = '-ANNUAL_FACTOR-'
SETTINGS_KEYS_TO_ELEMENT_KEYS['jump_distance_factor'] = '-JUMP_DISTANCE-'
SETTINGS_KEYS_TO_ELEMENT_KEYS['TermPrices_YEAR.csv'] = '-TERM_PRICES-'
SETTINGS_KEYS_TO_ELEMENT_KEYS['month_factors_mr.csv'] = '-MONTH_FACTORS-'
SETTINGS_KEYS_TO_ELEMENT_KEYS['actual_spot_prices.csv'] = '-ACTUAL_SPOT_PRICES-'
SETTINGS_KEYS_TO_ELEMENT_KEYS['month_prices.csv'] = '-MONTH_PRICES-'
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
              TextLabel("path_reuters", "folder"),
              TextLabel("path_power", "folder"),
              TextLabel("path_gas", "folder"),
              TextLabel('time_step'),
              TextLabel('annualization_factor'),
              TextLabel('jump_distance_factor'),
              TextLabel('TermPrices_YEAR.csv'),
              TextLabel('month_factors_mr.csv'),
              TextLabel('actual_spot_prices.csv'),
              TextLabel('month_prices.csv'),
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


def report_an_error(dummy) -> None:
    sg.popup("An error has occurred. Please check log file for details.")
    return None


def update_volatility(json_path: str) -> dict:
    with open(json_path, "rb") as infile:
        volatilites = json.load(infile)

    return volatilites


@logger.catch(onerror=report_an_error)
def run(params):
    """"""
    logger.info(params)
    # callback function here.


start_simulation = "Start Simulation"


# Create main window
def create_main_window() -> sg.Window:
    """"""
    # Layout the design of the GUI
    frame_years_layout = [
        [sg.Text('Year 0 (€/MWh)'),
         sg.Input(sg.user_settings_get_entry('year0', ''), key='-YEAR0-', enable_events=True, size=(10, 1))],
        [sg.Text('Year 1 (€/MWh)'),
         sg.Input(sg.user_settings_get_entry('year1', ''), key='-YEAR1-', enable_events=True, size=(10, 1))],
        [sg.Text('Year 2 (€/MWh)'),
         sg.Input(sg.user_settings_get_entry('year2', ''), key='-YEAR2-', enable_events=True, size=(10, 1))],

    ]

    frame_layout = [
        [sg.B('Export CSV from Reuters', key="-CREATE-CSV-", button_color=("white", "green"), disabled=True)],
        [sg.Radio('Gas', 'RADIO1', default=sg.user_settings_get_entry('gas', True), key='-GAS-'),
         sg.Radio('Power', 'RADIO1', default=sg.user_settings_get_entry('power', False), key='-POWER-')],
        [sg.CalendarButton('Start Date',
                           target='-CAL-',
                           format='%d.%m.%Y',
                           locale='de_DE',
                           begin_at_sunday_plus=1),
         sg.Input(sg.user_settings_get_entry('start_date', ''), key='-CAL-', size=(10, 1))],
        [sg.Text('Years to Future'),
         sg.DropDown((1, 2), default_value=sg.user_settings_get_entry('years_to_future', 2), key='-DD1-')],
        [sg.Text('Reference Year'), sg.DropDown(('initial year', 'initial year + 1'),
                                                default_value=sg.user_settings_get_entry('reference_year',
                                                                                         'initial year + 1'),
                                                key='-DD2-', size=(12, 1), )],
        [sg.Frame('Initial Prices', frame_years_layout)],
        [sg.Text('Number of Simulations'), sg.Input(sg.user_settings_get_entry('num_sim', ''),
                                                    key='-NUM_SIM-',
                                                    enable_events=True
                                                    , size=(10, 1))],
        [sg.Text('Year Volatility:'), sg.Text("", key='-year_vola-', enable_events=True, size=(8, 1))],
        [sg.Text('Spot Volatility w/ Jumps:'), sg.Text("", key='-spot_vola_w_jumps-', enable_events=True, size=(8, 1))],
        [sg.Text('Spot Volatility w/o Jumps:'),
         sg.Text("", key='-year_vola_wo_jumps-', enable_events=True, size=(8, 1))]
    ]
    width, height = sg.Window.get_screen_size()
    # window_width, window_height, output_height = round(0.3 * width), round(0.56 * height), round(0.07 * height)
    window_width, window_height, output_height = round(0.5 * width), round(0.84 * height), round(0.105 * height)
    layout = [
        [
            sg.Column([[sg.Frame('User Inputs', frame_layout)]]),

            # sg.Column([[sg.Image(filename="./logo-transparent.png")],  # hiermit kann man ein Bild einfuegen.
            #            [sg.Button(start_simulation), sg.Quit(), sg.B('Save'), sg.B('Settings')],
            #            ])

        ],

        [sg.Output(size=(window_width, output_height), key='-LOG-', echo_stdout_stderr=True, font="Any 8")],
    ]
    # Show the Window to the user
    window = sg.Window('Simulation Tool', layout, size=(window_width, window_height), font="Any 11", )

    return window


def save_user_settings(value):
    sg.user_settings_set_entry('gas', value['-GAS-'])
    sg.user_settings_set_entry('power', value['-POWER-'])
    sg.user_settings_set_entry('years_to_future', value['-DD1-'])
    sg.user_settings_set_entry('reference_year', value['-DD2-'])
    sg.user_settings_set_entry('year0', value['-YEAR0-'])
    sg.user_settings_set_entry('year1', value['-YEAR1-'])
    sg.user_settings_set_entry('year2', value['-YEAR2-'])
    sg.user_settings_set_entry('num_sim', value['-NUM_SIM-'])
    sg.user_settings_set_entry('start_date', value['-CAL-'])
    print("Saving user settings successful.")
    logger.info("Saving user settings successful.")

    return None


def format_vola(vola: float):
    vola = round(vola * 100, 2)

    return str(vola) + '%'


@logger.catch(onerror=report_an_error)
def export_reuters_csv(settings: dict) -> None:
    """Create csv-files from main excel sheet.

    :param settings: dictionary containing settings values
    """
    reuters_path = pathlib.Path(settings["path_reuters"])
    export_path_gas = settings["path_gas"]
    print(f"INFO - actual_spot_prices.csv was successfully created at {export_path_gas}")

    return None


def main():
    window, settings = None, load_settings(SETTINGS_FILE_PATH, DEFAULT_SETTINGS)
    # Event loop. Read buttons, make callbacks
    while True:
        # Read the Window
        if window is None:
            window = create_main_window()

        event, value = window.read()
        if event in ('Quit', sg.WIN_CLOSED):
            break
        if event == "-CREATE-CSV-":
            export_reuters_csv(settings)
        # check if initial prices are of type float
        if event == '-YEAR0-' and value['-YEAR0-'] and value['-YEAR0-'][-1] not in '0123456789.,':
            window['-YEAR0-'].update(value['-YEAR0-'][:-1])
        if event == '-YEAR1-' and value['-YEAR1-'] and value['-YEAR1-'][-1] not in '0123456789.,':
            window['-YEAR1-'].update(value['-YEAR1-'][:-1])
        if event == '-YEAR2-' and value['-YEAR2-'] and value['-YEAR2-'][-1] not in '0123456789.,':
            window['-YEAR2-'].update(value['-YEAR2-'][:-1])
        if event == '-NUM_SIM-' and value['-NUM_SIM-'] and value['-NUM_SIM-'][-1] not in '0123456789':
            window['-NUM_SIM-'].update(value['-NUM_SIM-'][:-1])
        if event == 'Settings':
            event, value = create_settings_window(settings).read(close=True)
            if event == 'Save Settings':
                window.close()
                window = None
                save_settings(SETTINGS_FILE_PATH, settings, value)
        if event == 'Save':
            save_user_settings(value)
        if event == start_simulation:
            ref_year = {'initial year': 0, 'initial year + 1': 1}
            if value["-GAS-"]:
                import_data_path = settings["path_gas"]
                path = pathlib.Path(import_data_path)
                export_path = pathlib.Path(settings["export_path_gas"])
            else:
                import_data_path = settings["path_power"]
                path = pathlib.Path(import_data_path)
                export_path = pathlib.Path(settings["export_path_power"])

            # in case float delimiter is ','.
            value['-YEAR0-'] = float(value['-YEAR0-'].replace(",", "."))
            value['-YEAR1-'] = float(value['-YEAR1-'].replace(",", "."))
            value['-YEAR2-'] = float(value['-YEAR2-'].replace(",", "."))

            params = {"t": int(settings["time_step"]), "m": int(settings["annualization_factor"]),
                      "start_date": value["-CAL-"],
                      "years_to_future": int(value["-DD1-"]),
                      "reference_year": ref_year[value["-DD2-"]],
                      "initial_prices": [value['-YEAR0-'], value['-YEAR1-'], value['-YEAR2-']],
                      "term_prices": path.joinpath(settings["TermPrices_YEAR.csv"]),
                      "actual_spot_prices": path.joinpath(settings["actual_spot_prices.csv"]),
                      "month_prices": path.joinpath(settings["month_prices.csv"]),
                      "jump_distance": int(settings["jump_distance_factor"]),
                      "month_factors_mr": path.joinpath(settings["month_factors_mr.csv"]),
                      "num_sim": int(value["-NUM_SIM-"]),
                      "spot_price_simulation": str(export_path.joinpath("spot_price_simulation")),
                      "export_path": path,  # this is export path of volas_for_gui.json, not spot_price_simulation.csv
                      }
            run(params)
            volatilities = update_volatility(path.joinpath("volas_for_gui.json"))
            anualized_vola, jump_vola, no_jump_vola = map(format_vola,
                                                          [volatilities["vola"], volatilities["jump_vola"],
                                                           volatilities["no_jumps_vola"]])
            window["-year_vola-"].update(anualized_vola)
            window["-spot_vola_w_jumps-"].update(jump_vola)
            window["-year_vola_wo_jumps-"].update(no_jump_vola)
            print("Calculation finished.")

    window.close()


main()
