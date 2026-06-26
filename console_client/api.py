from base.character import Character
from base.display import Display
from base.enums import ImageCategoryEnum
from base.images import display_image
from console_client.client import ConsoleGameClient as GameClient


class ConsoleDisplay(Display):
    """Terminal-based I/O: delegates to print/input."""

    def _output(self, text):
        print(text)

    def _show_window(self, title, text):
        print(f'=== {title} ===')
        print(text)

    def _update_char_info(self, text):
        print(f'Character: {text}')

    def _update_location_text(self, text):
        print(f'\n=== Location: {text} ===\n')

    def print(self, *args, **kwargs):
        print(*args, **kwargs)

    def show_action_countdown(self, seconds_left):
        print(f'Waiting {seconds_left} seconds...', end=' \r')

    def clear_action_countdown(self):
        print(' ' * 40, end='\r')

    def input(self, prompt=''):
        return input(prompt)

    def prompt_int(self, prompt, min_val=None, max_val=None):
        result = None
        done = False
        while not done:
            raw = input(prompt).strip()
            if not raw:
                done = True
                continue
            try:
                value = int(raw)
            except ValueError:
                print('Please enter a whole number (or press Enter to go back).')
                continue
            if min_val is not None and value < min_val:
                print(f'Please enter a number >= {min_val}.')
                continue
            if max_val is not None and value > max_val:
                print(f'Please enter a number <= {max_val}.')
                continue
            result = value
            done = True
        return result

    def prompt_str(self, prompt, allow_empty=True):
        while True:
            raw = input(prompt).strip()
            if not raw and not allow_empty:
                print('Input cannot be empty.')
                continue
            return raw if raw else None

    def prompt_yes_no(self, prompt):
        while True:
            answer = input(prompt).strip().lower()
            if answer in ('y', 'ye', 'yes'):
                return True
            elif answer in ('n', 'no'):
                return False
            print('Please answer y or n.')

    def show_image(self, category, key):
        display_image(category, key)

    def show_location(self, location_data):
        super().show_location(location_data)
        map_skin = location_data.get('skin', '')
        if map_skin:
            display_image(ImageCategoryEnum.MAPS, map_skin)

    def show_basic_actions(self, location_type):
        pass

    def show_advanced_actions(self):
        pass

    def show_character_actions(self):
        pass
