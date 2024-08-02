import configparser
import inspect
import random
import re
import sys
from time import sleep

import requests

from enums import (
    CharacterSexEnum,
    ActionTypeEnum,
    EquipmentSlotsEnum,
)
from scripts import ScenariosStorage


class BaseClient:
    """Basic client for sending requests."""

    def __init__(self):
        self.base_url = "https://api.artifactsmmo.com"
        self.config = self._get_config()

        self.base_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.config.get('General', 'TOKEN')}"
        }

    def _get_config(self):
        """Open config file."""

        config = configparser.ConfigParser()
        config.read('config.ini')

        return config

    def _post(self, url='', data=None):
        """Send POST request."""

        return self._do_request(method='post', url=url, data=data)

    def _get(self, url='', data=None):
        """Send GET request."""

        return self._do_request(method='get', url=url, data=data)

    def _do_request(self, method='get', url='', data=None):
        """Send request to game."""

        request = requests.request(method, self.base_url + url, json=data, headers=self.base_headers)

        return request


class GameClient(BaseClient):
    """Client for interacting with the game world."""

    def __init__(self):
        super().__init__()

        self.check_server_status()

    def main_loop(self):
        """User interaction in an infinite loop."""

        character = self.select_character()
        scenarios_storage = ScenariosStorage(character)

        while True:
            available_actions = {
                idx: action for idx, action in enumerate(ActionTypeEnum.AVAILABLE_ACTIONS.value, 1)
            }
            available_actions_str = "\n".join(f"{idx} - {name}" for idx, name in available_actions.items())
            try:
                current_action_idx = int(input(
                    'What do you want to do?\n'
                    f'{available_actions_str}\n'
                    'Please type a number: '
                ))
                current_action = available_actions[current_action_idx]
            except ValueError:
                print('Invalid input. Please try again.')
                continue

            if current_action == ActionTypeEnum.MOVE.value:
                print('Where do you want to move?')
                x = int(input('X: '))
                y = int(input('Y: '))

                character.move(x, y)
            elif current_action == ActionTypeEnum.FIGHT.value:
                count = input('How many times to fight?: ')
                for _ in range(int(count)):
                    character.fight()

            elif current_action == ActionTypeEnum.GATHERING.value:
                count = input('How many times to gather?: ')
                for _ in range(int(count)):
                    character.gathering()

            elif current_action == ActionTypeEnum.CRAFTING.value:
                craft_name = input('What item do you want to craft?: ')
                quantity = int(input('Нow many do you want to create?: '))

                character.crafting(craft_name, quantity)

            elif current_action in [ActionTypeEnum.EQUIP.value, ActionTypeEnum.UNEQUIP.value]:
                slots_map = {
                    idx: action.value for idx, action in enumerate(EquipmentSlotsEnum, 1)
                }
                slots_map_str = "\n".join(f"{idx} - {name}" for idx, name in slots_map.items())

                if current_action == ActionTypeEnum.EQUIP.value:
                    item_name = input('What item do you want to equip?: ')

                    slot_idx = int(input(
                        'Which slot do you want to equip the item in?\n'
                        f'{slots_map_str}\n'
                        'Please type a number: '
                    ))
                    slot = slots_map[slot_idx]
                    character.equip(item_name, slot)

                elif current_action == ActionTypeEnum.UNEQUIP.value:
                    slot_idx = int(input(
                        'Which slot do you want to unequip?\n'
                        f'{slots_map_str}\n'
                        'Please type a number: '
                    ))
                    slot = slots_map[slot_idx]

                    character.unequip(slot)

            elif current_action == ActionTypeEnum.NEW_TASK.value:
                character.get_task()

            elif current_action == ActionTypeEnum.COMPLETE_TASK.value:
                character.complete_task()

            elif current_action == ActionTypeEnum.BUY_ITEM.value:
                item_name = input('What item do you want to buy?: ')
                quantity = int(input('Нow many do you want to buy?: '))

                character.buy_item(item_name, quantity)

            elif current_action == ActionTypeEnum.SELL_ITEM.value:
                item_name = input('What item do you want to sell?: ')
                quantity = int(input('Нow many do you want to sell?: '))

                character.sell_item(item_name, quantity)

            elif current_action == ActionTypeEnum.USE_SCENARIO.value:
                scenarios_map = dict(
                    (method_name.replace('_', ' '), method)
                    for method_name, method in inspect.getmembers(scenarios_storage)
                    if not method_name.startswith('__') and inspect.ismethod(method)
                )
                scenarios_idx_map = {
                    idx: method_name for idx, method_name in enumerate(scenarios_map.keys(), 1)
                }
                scenarios_str = "\n".join(f"{idx} - {name}" for idx, name in scenarios_idx_map.items())

                scenario_idx_select = int(input(
                    'Which scenario do you want to launch?\n'
                    f'{scenarios_str}\n'
                    'Please type a number: '
                ))
                selected_scenario = scenarios_map[scenarios_idx_map[scenario_idx_select]]
                params = {}
                print('Specify the values of the scenario startup parameters')
                for name, parameter in dict(inspect.signature(selected_scenario).parameters).items():
                    parameter_type = type(parameter.default)
                    params[name] = parameter_type(input(f'{name} (default: {parameter.default}): '))

                selected_scenario(**params)

            else:
                print('This is not a valid action!')

            print('')

    def select_character(self):
        """Selecting a character from the list on the account."""

        characters = self.get_characters_list()
        characters_map = {idx: name for idx, name in enumerate([character["name"] for character in characters], 1)}
        print(f'Characters on account: {", ".join(characters_map.values())}')

        characters_map_string = "\n".join(f"{idx} - {name}" for idx, name in characters_map.items())
        character_selected = False
        while not character_selected:
            character_select = input(
                'Which character do you want to choose?\n'
                f'{characters_map_string}\n'
                'Please type a number: '
            )
            if not int(character_select) in characters_map:
                print('Failed to select a character, try again.')
            else:
                character_selected = True

        selected_character_name = characters_map[int(character_select)]
        selected_character = Character(selected_character_name)
        print(f'Selected character {selected_character_name}.')

        return selected_character

    def check_server_status(self):
        """Checking the status of the server. If unavailable, the process will be terminated."""

        status_request = self._get()

        if status_request.status_code == 200:
            print(f'Server status is "{status_request.json()["data"]["status"]}".')
            for announcement in status_request.json()['data']['announcements']:
                print(announcement['message'])
        else:
            sys.exit('Can\'t reach the server. Please try again later.')

    def get_characters_list(self):
        """Getting a list of characters. If there are no characters, it will create one."""

        url = '/my/characters'

        characters_list = self._get(url=url)

        if characters_list.status_code == 404:
            print(f'{characters_list.json()["error"]["message"]} You have to create a character first.')
            character_created = self.create_new_character()

            if character_created:
                characters_list = self._get(url=url)

        if characters_list.status_code == 200:
            result = characters_list.json()['data']
        else:
            result = []

        return result

    def create_new_character(self):
        """Creating a new character."""

        url = '/characters/create'

        name_correct = False
        while not name_correct:
            character_name = input('What will the new character\'s name be?: ')
            if not re.match(r'^[a-zA-Z0-9_-]{3,12}$', character_name):
                print('That name doesn\'t fit, try another')
            else:
                name_correct = True

        if name_correct:
            character_sex = ''
            while character_sex not in ['m', 'f', 'r']:
                character_sex = input('What sex will the character be? male(m)/female(f)/random(r): ')

            print(f'The new character\'s name is {character_name}, creating...')
            create_request = self._post(
                url=url,
                data={
                    'name': character_name,
                    'skin': random.choice(CharacterSexEnum.SEX_SKIN_MAP.value[character_sex]),
                },
            )

            character_created = create_request.status_code == 200

            if create_request.status_code == 200:
                print(f'Character {character_name} succesfully created.')
            else:
                print(create_request.json()['error']['message'])

            return character_created


class Character(BaseClient):
    """Client for character interaction."""

    def __init__(self, name) -> None:
        super().__init__()

        self.name = name
        self.base_character_action_url = f'/my/{self.name}/action'
        self._get_character_info()

    def _get_character_info(self):
        """Getting all character data and storing in instance."""

        character_info_request = requests.get(
            url=f'{self.base_url}/characters/{self.name}'
        )

        if character_info_request.status_code == 200:
            for key, value in character_info_request.json()['data'].items():
                setattr(self, key, value)

    def _get_last_action(self):
        """Getting info about last action from character log."""

        last_action_data = self._get(
            url=f'/my/{self.name}/logs',
            data={
                'page': 1,
                'size': 1,
            })

        if last_action_data.status_code == 200:
            print(last_action_data.json()['data'][0]['description'])
        elif error_block := last_action_data.json().get('error'):
            print(f'Can\'t get last action. {error_block["message"]}.')

    def _do_action(self, action_name='', action_data=None):
        """General method for sending an action request."""

        if action_data is None:
            action_data = {}

        action_request = self._post(
            url=f'{self.base_character_action_url}/{action_name}',
            data=action_data,
        )

        if action_request.status_code == 200:
            print(
                f'Performing action {action_request.json()["data"]["cooldown"]["reason"]}. '
                f'It\'ll take {action_request.json()["data"]["cooldown"]["total_seconds"]} seconds.'
            )
            for i in range(action_request.json()["data"]["cooldown"]["total_seconds"], 0, -1):
                print(f'Waiting {i} seconds...', end=' \r')
                sleep(1)

            self._get_last_action()
        elif error_block := action_request.json().get('error'):
            print(f'Can\'t perform action. {error_block["message"]}')

    def move(self, x=0, y=0):
        """Move the character to a given map cell."""

        self._do_action(
            action_name=ActionTypeEnum.MOVE.value,
            action_data={
                'x': x,
                'y': y,
            }
        )

    def fight(self):
        """Start fight."""

        self._do_action(
            action_name=ActionTypeEnum.FIGHT.value,
        )

    def gathering(self):
        """Start gathering resources."""

        self._do_action(
            action_name=ActionTypeEnum.GATHERING.value,
        )

    def crafting(self, item_name='', quantity=1):
        """Start crafting items."""

        self._do_action(
            action_name=ActionTypeEnum.CRAFTING.value,
            action_data={
                'code': item_name,
                'quantity': quantity,
            }
        )

    def equip(self, item_name='', slot=''):
        """Equip item."""

        self._do_action(
            action_name=ActionTypeEnum.EQUIP.value,
            action_data={
                'code': item_name,
                'slot': slot,
            }
        )

    def unequip(self, slot=''):
        """Unequip slot."""

        self._do_action(
            action_name=ActionTypeEnum.UNEQUIP.value,
            action_data={
                'slot': slot,
            }
        )

    def get_task(self):
        """Get new quest."""

        self._do_action(
            action_name='task/new',
        )

    def complete_task(self):
        """Complete the current quest."""

        self._do_action(
            action_name='task/complete',
        )

    def _get_item_data(self, item_name=''):
        """Get item data."""

        item_data = self._get(
            url=f'/items/{item_name}',
        )

        if item_data.status_code == 200:
            result = item_data.json()
        else:
            result = {}

        return result

    def buy_item(self, item_name='', quantity=1):
        """Buy an item from General Exchange."""

        item_data = self._get_item_data(item_name)
        current_price = item_data.get('data', {}).get('ge', {}).get('buy_price', 0)

        if current_price:
            self._do_action(
                action_name='ge/buy',
                action_data={
                    'code': item_name,
                    'quantity': quantity,
                    'price': current_price,
                }
            )

    def sell_item(self, item_name='', quantity=1):
        """Sell an item to General Exchange."""

        item_data = self._get_item_data(item_name)
        current_price = item_data.get('data', {}).get('ge', {}).get('sell_price', 0)

        if current_price:
            self._do_action(
                action_name='ge/sell',
                action_data={
                    'code': item_name,
                    'quantity': quantity,
                    'price': current_price,
                }
            )
