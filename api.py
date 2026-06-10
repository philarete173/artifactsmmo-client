import inspect
import random
import re
import sys
from time import sleep

from base import BaseGameClient
from images import display_image
from enums import (
    CharacterSexEnum,
    CharacterSkinsEnum,
    ActionTypeEnum,
    EquipmentSlotsEnum,
    MapTypesEnum,
    ItemTypesEnum,
    GEOrderTypeEnum,
    ImageCategoryEnum,
)
from scripts import ScenariosStorage


class GameClient(BaseGameClient):
    """Client for interacting with the game world (account-level operations)."""

    def __init__(self):
        super().__init__()

        self.main_menu_map = {
            ActionTypeEnum.MOVE: self.character_movement,
            ActionTypeEnum.TRANSITION: self.character_transition,
            ActionTypeEnum.FIGHT: self.character_fight,
            ActionTypeEnum.GATHERING: self.character_gathering,
            ActionTypeEnum.CRAFTING: self.character_crafting,
            ActionTypeEnum.RECYCLING: self.character_recycling,
            ActionTypeEnum.EQUIP: self.character_equip,
            ActionTypeEnum.UNEQUIP: self.character_unequip,
            ActionTypeEnum.USE_ITEM: self.character_use_item,
            ActionTypeEnum.DELETE_ITEM: self.character_delete_item,
            ActionTypeEnum.REST: self.character_rest,
            ActionTypeEnum.CHANGE_SKIN: self.character_change_skin,
            ActionTypeEnum.NEW_TASK: self.character_get_new_task,
            ActionTypeEnum.COMPLETE_TASK: self.character_complete_task,
            ActionTypeEnum.CANCEL_TASK: self.character_cancel_task,
            ActionTypeEnum.EXCHANGE_TASK: self.character_exchange_task_coins,
            ActionTypeEnum.TRADE_TASK: self.character_trade_task,
            ActionTypeEnum.CLAIM_PENDING_ITEM: self.character_claim_pending_item,
            ActionTypeEnum.BUY_NPC_ITEM: self.character_npc_buy_item,
            ActionTypeEnum.SELL_NPC_ITEM: self.character_npc_sell_item,
            ActionTypeEnum.BUY_BANK_EXPANSION: self.character_buy_bank_expansion,
            ActionTypeEnum.DEPOSIT_BANK: self.character_deposit_item_to_bank,
            ActionTypeEnum.DEPOSIT_BANK_GOLD: self.character_deposit_gold_to_bank,
            ActionTypeEnum.WITHDRAW_BANK: self.character_withdraw_item_from_bank,
            ActionTypeEnum.WITHDRAW_GOLD: self.character_withdraw_gold_from_bank,
            ActionTypeEnum.GIVE_GOLD: self.character_give_gold,
            ActionTypeEnum.GIVE_ITEM: self.character_give_item,
            ActionTypeEnum.BUY_GE_ITEM: self.character_ge_buy_item,
            ActionTypeEnum.CANCEL_GE_ORDER: self.character_ge_cancel_order,
            ActionTypeEnum.CREATE_GE_BUY_ORDER: self.character_ge_create_buy_order,
            ActionTypeEnum.CREATE_GE_SELL_ORDER: self.character_ge_create_sell_order,
            ActionTypeEnum.FILL_GE_ORDER: self.character_ge_fill_order,
            ActionTypeEnum.SHOW_BANK: self.show_bank,
            ActionTypeEnum.SHOW_PENDING_ITEMS: self.show_pending_items,
            ActionTypeEnum.SHOW_GE_ORDERS: self.show_ge_orders,
            ActionTypeEnum.USE_SCENARIO: self.use_scenario,
        }

        self.account_menu_map = {
            ActionTypeEnum.SHOW_ACCOUNT_DETAILS: self.get_account_details,
            ActionTypeEnum.CHANGE_PASSWORD: self.change_password,
            ActionTypeEnum.LOGIN_WITH_PASSWORD: self.login_with_password,
        }

        self.show_current_season()

    def main_loop(self):
        """Top-level menu: account-level actions plus character selection.
        Selecting a character enters the per-character action loop; when
        that loop returns, control comes back here so the user can pick
        a different character or perform account-level actions."""

        while True:
            actions_map, actions_str = self._prepare_actions_menu_data(ActionTypeEnum.ACCOUNT_ACTIONS)
            idx = self._prompt_int(
                'What do you want to do at the account level?\n'
                f'{actions_str}\n'
                'Please type a number: '
            )
            if idx is None or idx not in actions_map:
                continue

            current_action = actions_map[idx]

            if current_action == ActionTypeEnum.SELECT_CHARACTER:
                self._choose_character()
                if self.character is not None:
                    self.character_action_loop()
                continue

            self._dispatch_account_action(current_action)

            print('')

    def _dispatch_account_action(self, current_action):
        method = self.account_menu_map.get(current_action)

        if method is None:
            print('This is not a valid action!')
            return

        try:
            method()
        except Exception as error:
            print(f'Something went wrong. Error: {error}. Please try again.')

    def character_action_loop(self):
        """Per-character action menu with 3 top-level categories."""

        while True:
            current_location_data = self.get_location_data(
                self.character.layer, self.character.x, self.character.y,
            )
            self._print_location_info(current_location_data)

            choice = self._prompt_int(
                'What do you want to do?\n'
                '1 - Basic actions\n'
                '2 - Advanced actions\n'
                '3 - Character actions\n'
                'Please type a number: '
            )
            if choice is None:
                continue

            if choice == 1:
                self._handle_basic_actions(current_location_data)
            elif choice == 2:
                self._handle_advanced_actions()
            elif choice == 3:
                self._handle_character_actions()

            print('')

    def _handle_basic_actions(self, location_data):
        location_type = (location_data.get('content') or {}).get('type', None)
        actions = list(ActionTypeEnum.LOCATION_ACTIONS_MAP.get(location_type, []))

        if (location_data.get('interactions') or {}).get('transition'):
            actions.append(ActionTypeEnum.TRANSITION)

        actions_map, actions_str = self._prepare_actions_menu_data(actions)
        idx = self._prompt_int(
            'Basic actions:\n'
            f'{actions_str}\n'
            'Please type a number: '
        )
        if idx is None or idx not in actions_map:
            return

        current_action = actions_map[idx]
        method = self.main_menu_map.get(current_action)
        if method is None:
            print('This is not a valid action!')
        else:
            try:
                method()
            except Exception as error:
                print(f'Something went wrong. Error: {error}. Please try again.')

    def _handle_advanced_actions(self):
        actions_map, actions_str = self._prepare_actions_menu_data(ActionTypeEnum.ADVANCED_ACTIONS)
        idx = self._prompt_int(
            'Advanced actions:\n'
            f'{actions_str}\n'
            'Please type a number: '
        )
        if idx is None or idx not in actions_map:
            return

        current_action = actions_map[idx]
        method = self.main_menu_map.get(current_action)
        if method is None:
            print('This is not a valid action!')
        else:
            try:
                method()
            except Exception as error:
                print(f'Something went wrong. Error: {error}. Please try again.')

    def _handle_character_actions(self):
        actions_map, actions_str = self._prepare_actions_menu_data(ActionTypeEnum.CHARACTER_ACTIONS)
        idx = self._prompt_int(
            'Character actions:\n'
            f'{actions_str}\n'
            'Please type a number: '
        )
        if idx is None or idx not in actions_map:
            return

        current_action = actions_map[idx]
        if current_action == ActionTypeEnum.STATS:
            self._show_character_stats()
        elif current_action == ActionTypeEnum.SKILLS:
            self._show_character_skills()
        elif current_action == ActionTypeEnum.INVENTORY:
            self._show_character_inventory()
        elif current_action == ActionTypeEnum.EQUIPMENT:
            self._show_character_equipment()
        elif current_action == ActionTypeEnum.CHANGE_SKIN:
            self.character_change_skin()

    def _show_character_stats(self):
        print('=== Character Stats ===')
        print(f'Level {self.character.level} ({self.character.xp} / {self.character.max_xp})')
        print('Core Stats:')
        print(f'  HP: {self.character.hp} / {self.character.max_hp}')
        print(f'  Haste: {self.character.haste}')
        print(f'  Critical Strike: {self.character.critical_strike}')
        print(f'  Initiative: {self.character.initiative}')
        print(f'  Threat: {self.character.threat}')
        print(f'  Prospecting: {self.character.prospecting}')
        print(f'  Wisdom: {self.character.wisdom}')
        print(f'  Damage: {self.character.dmg}%')
        print('Attack:')
        print(f'  Fire: {self.character.attack_fire}')
        print(f'  Earth: {self.character.attack_earth}')
        print(f'  Water: {self.character.attack_water}')
        print(f'  Air: {self.character.attack_air}')
        print('Elemental Damage:')
        print(f'  Fire: {self.character.dmg_fire}%')
        print(f'  Earth: {self.character.dmg_earth}%')
        print(f'  Water: {self.character.dmg_water}%')
        print(f'  Air: {self.character.dmg_air}%')
        print('Resistance:')
        print(f'  Fire: {self.character.res_fire}%')
        print(f'  Earth: {self.character.res_earth}%')
        print(f'  Water: {self.character.res_water}%')
        print(f'  Air: {self.character.res_air}%')
        print('Effects:')
        effects = getattr(self.character, 'effects', None) or []
        if effects:
            for effect in effects:
                print(f'  {effect.get("code", "?")}: {effect.get("value", 0)}')
        else:
            print('  (none)')

    def _show_character_skills(self):
        print('=== Character Skills ===')
        skills = [
            ('Mining', 'mining'),
            ('Woodcutting', 'woodcutting'),
            ('Fishing', 'fishing'),
            ('Weaponcrafting', 'weaponcrafting'),
            ('Gearcrafting', 'gearcrafting'),
            ('Jewelrycrafting', 'jewelrycrafting'),
            ('Cooking', 'cooking'),
            ('Alchemy', 'alchemy'),
        ]
        for skill_name, skill_code in skills:
            skill_level = getattr(self.character, f'{skill_code}_level', 0)
            current_xp = getattr(self.character, f'{skill_code}_xp', 0)
            max_skill_xp = getattr(self.character, f'{skill_code}_max_xp', 0)
            print(f'{skill_name}: Level {skill_level} ({current_xp} / {max_skill_xp})')

    def _show_character_inventory(self):
        inventory = getattr(self.character, 'inventory', None) or []
        max_items = getattr(self.character, 'inventory_max_items', 0)
        total_quantity = sum(slot.get('quantity', 0) for slot in inventory if slot.get('code'))
        filled_slots = sum(1 for slot in inventory if slot.get('code'))

        unique_codes = set(slot.get('code') for slot in inventory if slot.get('code'))
        print('Loading items data...', end='\r')
        item_names = {}
        for item_code in unique_codes:
            item = self.get_item(item_code)
            item_names[item_code] = (item or {}).get('name', item_code)

        print('=== Character Inventory ===')
        print(f'Fill: {total_quantity} / {max_items} (slots: {filled_slots})')
        for slot in inventory:
            item_code = slot.get('code')
            if not item_code:
                continue
            quantity = slot.get('quantity', 1)
            item_name = item_names.get(item_code, item_code)
            print(f'  {item_name} x{quantity}')

    def _show_character_equipment(self):
        effects_data = self.get_effects()
        effect_names = {effect['code']: effect['name'] for effect in effects_data if 'code' in effect}

        slot_entries = []
        unique_codes = set()
        for slot in EquipmentSlotsEnum:
            attr = f'{slot}_slot'
            label = re.sub(r'(\d)', r' \1', slot.replace('_', ' ')).capitalize()
            item_code = getattr(self.character, attr, None)
            slot_entries.append((label, item_code))
            if item_code:
                unique_codes.add(item_code)

        print('Loading items data...', end='\r')
        items_data = {}
        for code in unique_codes:
            items_data[code] = self.get_item(code)

        print('=== Character Equipment ===')
        for label, item_code in slot_entries:
            if item_code:
                item = items_data.get(item_code, {})
                item_name = item.get('name', item_code)
                print(f'  {label}: {item_name}')
                effects = item.get('effects', []) or []
                if effects:
                    for effect in effects:
                        effect_code = effect.get('code', '')
                        value = effect.get('value', 0)
                        effect_name = effect_names.get(effect_code, effect_code)
                        print(f'    {effect_name}: {value}')
            else:
                print(f'  {label}: (empty)')

    def _print_location_info(self, location_data):
        """Print current location information: coordinates and name."""

        name = location_data.get('name', 'Unknown')
        x = location_data.get('x', '?')
        y = location_data.get('y', '?')
        layer = location_data.get('layer', '?')

        print(f'\n=== Location: {name} ({x}, {y}) [{layer}] ===\n')
        map_skin = location_data.get('skin', '')
        if map_skin:
            display_image(ImageCategoryEnum.MAPS, map_skin)

    def _choose_character(self):
        """Pick a character and bind it (plus its scenario storage) to this
        client. Called when the user picks "select character" in the
        account-level menu. Leaves self.character untouched if the user
        pressed Enter to go back."""

        character = self.select_character()
        if character is None:
            return

        self.character = character
        self.scenarios_storage = ScenariosStorage(self.character)

    def select_character(self):
        """Selecting a character from the list on the account. Returns the
        Character instance, or None if the user pressed Enter to go back."""

        characters = self.get_my_characters()

        if not characters:
            print('You have no characters. Creating a new one...')
            created = self.create_character()
            if not created:
                sys.exit('Failed to create a character. Aborting.')
            characters = self.get_my_characters()

        if not characters:
            sys.exit('No characters available and the API is unreachable with the current token.')

        return self._prompt_character_choice(characters)

    def _prompt_character_choice(self, characters):
        characters_map, characters_map_str = self._prepare_actions_menu_data(
            [character["name"] for character in characters],
        )
        print(f'Characters on account: {", ".join(characters_map.values())}')

        idx = self._prompt_int(
            'Which character do you want to choose?\n'
            f'{characters_map_str}\n'
            'Please type a number: '
        )

        if idx is None or idx not in characters_map:
            return None

        return self._build_character(characters_map[idx])

    def _build_character(self, name):
        character = Character(name, parent=self)
        print(f'Selected character {name}.')
        print(f'Level {character.level}, HP {character.hp}/{character.max_hp}, '
              f'Gold {character.gold}, Cooldown {character.cooldown}s.')
        display_image(ImageCategoryEnum.CHARACTERS, character.skin)

        return character

    def show_current_season(self):
        """Show the current season info at startup. Also acts as a
        network availability check (exits if the server is unreachable)."""

        response = self._get()

        if response.status_code != 200:
            sys.exit('Can\'t reach the server. Please try again later.')

        data = response.json().get('data', {})
        print(f'Game version: {data.get("version", "?")}.')

        season = data.get('season') or {}
        name = season.get('name', '?')
        number = season.get('number', '?')
        start = season.get('start_date', '?')
        print(f'Current season: {name} (#{number}), started {start}.')

    def _get_with_reauth(self, url, data=None):
        """Run an authenticated GET, automatically offering a re-login if
        the token is rejected. Returns the response object."""

        response = self._get(url=url, data=data)

        if self.is_invalid_token_error(response) and self.ensure_valid_token(probe_response=response):
            self._propagate_token_to_characters()
            response = self._get(url=url, data=data)

        return response

    def _post_with_reauth(self, url, data=None):
        """Run an authenticated POST, automatically offering a re-login if
        the token is rejected. Returns the response object."""

        response = self._post(url=url, data=data)

        if self.is_invalid_token_error(response) and self.ensure_valid_token(probe_response=response):
            self._propagate_token_to_characters()
            response = self._post(url=url, data=data)

        return response

    def get_my_characters(self):
        """Get a list of characters on the account."""

        response = self._get_with_reauth(url='/my/characters')
        result = []

        if response.status_code == 200:
            result = response.json().get('data', [])
        else:
            self._print_error_silently(response)

        return result

    @staticmethod
    def _print_error_silently(response):
        try:
            if error_block := response.json().get('error'):
                print(error_block.get('message', 'Unknown error.'))
        except ValueError:
            pass

    def create_character(self, name=None, sex=None):
        """Create a new character."""

        if name is None:
            name = self._prompt_character_name()
        if sex is None:
            sex = self._prompt_character_sex()

        print(f'The new character\'s name is {name}, creating...')

        create_request = self._post_with_reauth(
            url='/characters/create',
            data={
                'name': name,
                'skin': random.choice(CharacterSexEnum.SEX_SKIN_MAP[sex]),
            },
        )

        if create_request.status_code == 200:
            print(f'Character {name} successfully created.')
            return True

        if error_block := create_request.json().get('error'):
            print(error_block.get('message', 'Unknown error.'))

        return False

    def _prompt_character_name(self):
        result = ''
        done = False

        while not done:
            name = input('What will the new character\'s name be?: ')
            if re.match(r'^[a-zA-Z0-9_-]{3,12}$', name):
                result = name
                done = True
            else:
                print('That name doesn\'t fit, try another.')

        return result

    def _prompt_character_sex(self):
        result = ''
        done = False

        while not done:
            sex = input('What sex will the character be? male(m)/female(f)/random(r): ')
            if sex in ('m', 'f', 'r'):
                result = sex
                done = True

        return result

    def delete_character(self, name=''):
        """Delete a character."""

        if not name:
            name = input('What is the name of the character to delete?: ')

        confirm = self._prompt_yes_no(f'Are you sure you want to permanently delete {name}?')
        if not confirm:
            print('Deletion cancelled.')
            return False

        response = self._post_with_reauth(url='/characters/delete', data={'name': name})

        if response.status_code == 200:
            print(f'Character {name} successfully deleted.')
            return True

        if error_block := response.json().get('error'):
            print(error_block.get('message', 'Unknown error.'))

        return False

    def get_account_details(self):
        """Show account details."""

        response = self._get_with_reauth(url='/my/details')
        if response.status_code != 200:
            print('Failed to get account details.')
            return

        data = response.json().get('data', {})
        print('=== Account details ===')
        for key, value in data.items():
            print(f'  {key}: {value}')

    def change_password(self):
        """Change account password."""

        current = input('Enter current password: ')
        new = input('Enter new password: ')
        response = self._post_with_reauth(url='/my/change_password', data={
            'current_password': current,
            'new_password': new,
        })

        if response.status_code == 200:
            print('Password changed. Note: your token has been reset, update config.ini.')
            return

        if error_block := response.json().get('error'):
            print(error_block.get('message', 'Unknown error.'))

    def login_with_password(self):
        """Force a fresh login (replace the current token with one obtained
        from username/password). Useful when the saved token is expired or
        has been reset."""

        if self.request_new_token():
            self._propagate_token_to_characters()
            self.character.refresh()

    def _propagate_token_to_characters(self):
        """Copy the current auth header to every Character instance we
        know about, so that they reuse the freshly-issued token without
        having to be rebuilt."""

        for attr in ('character',):
            obj = getattr(self, attr, None)
            if obj is not None and hasattr(obj, 'base_headers'):
                obj.base_headers['Authorization'] = self.base_headers.get('Authorization', '')

    def _prepare_actions_menu_data(self, iterable):
        def _display(item):
            value = getattr(item, 'value', None)
            if isinstance(value, str):
                return value
            if isinstance(item, dict):
                for key in ('name', 'code'):
                    if key in item:
                        return str(item[key])
            return str(item)

        items_map = {idx: item for idx, item in enumerate(iterable, 1)}
        items_map_str = "\n".join(
            f"{idx} - {_display(name).replace('_', ' ').capitalize()}" for idx, name in items_map.items()
        )

        return items_map, items_map_str

    def _prompt_int(self, prompt, min_val=None, max_val=None):
        """Prompt the user for an integer. Empty input (just Enter) returns
        None, which nested menus treat as 'go back to the parent menu'.
        Non-numeric input and out-of-range values are re-prompted."""

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

    def character_movement(self):
        layer = getattr(self.character, 'layer', 'overworld')
        maps = self.get_maps_data(layer=layer)
        available_types_map, available_types_str = self._build_location_type_menu(maps)

        location_type_idx = self._prompt_int(
            'What type of location do you want to move to?\n'
            f'{available_types_str}\n'
            '0 - any type\n'
            'Please type a number: '
        )

        if location_type_idx is None:
            return

        chosen_locations = self._select_destinations(maps, available_types_map, location_type_idx)
        if not chosen_locations:
            return

        self._prompt_and_move(chosen_locations)

    def _build_location_type_menu(self, maps):
        available_types = sorted({(m.get('content') or {}).get('type', '') for m in maps if m.get('content')})
        return self._prepare_actions_menu_data(available_types)

    def _select_destinations(self, maps, available_types_map, location_type_idx):
        if location_type_idx == 0:
            return maps

        chosen_location_type = available_types_map[location_type_idx]
        return [m for m in maps if (m.get('content') or {}).get('type') == chosen_location_type]

    def _prompt_and_move(self, chosen_locations):
        chosen_locations_map, chosen_locations_str = self._prepare_actions_menu_data(
            [(m.get('content') or {}).get('code') or f"({m['x']},{m['y']})" for m in chosen_locations]
        )

        if len(chosen_locations_map) == 0:
            print('No destinations of the chosen type.')
            return

        if len(chosen_locations_map) == 1:
            chosen_location_idx = 1
        else:
            chosen_location_idx = self._prompt_int(
                'Where do you want to move?\n'
                f'{chosen_locations_str}\n'
                'Please type a number: '
            )
            if chosen_location_idx is None:
                return

        chosen_location = chosen_locations[chosen_location_idx - 1]
        self.character.move(x=chosen_location['x'], y=chosen_location['y'])

    def character_transition(self):
        self.character.transition()

    def character_fight(self):
        count = self._prompt_int('How many times to fight?: ', min_val=1)
        if count is None:
            return

        self._do_fight(count)

    def _do_fight(self, count):
        participants = self._collect_boss_participants() if self._at_boss() else []

        for _ in range(count):
            self.character.fight(participants=participants or None)

    def _at_boss(self):
        cur_location = self.get_location_data(self.character.layer, self.character.x, self.character.y)
        monster_code = (cur_location.get('content') or {}).get('code')
        if not monster_code:
            return False
        monster = self.get_monster(monster_code)
        return monster.get('type') == 'boss'

    def _collect_boss_participants(self):
        use_multi = self._prompt_yes_no('Boss detected. Use multi-character fight?')
        if not use_multi:
            return []

        my_chars = self.get_my_characters()
        others = [c['name'] for c in my_chars if c['name'] != self.character.name]
        if not others:
            return []

        return self._parse_participants(others)

    def _parse_participants(self, others):
        others_map, others_str = self._prepare_actions_menu_data(others)
        sel = input(
            'Select participants (comma separated, max 2):\n'
            f'{others_str}\n'
        )

        result = []
        try:
            result = [others_map[int(s.strip())] for s in sel.split(',') if s.strip().isdigit()]
        except (ValueError, KeyError):
            result = []

        return result

    def character_gathering(self):
        count = self._prompt_int('How many times to gather?: ', min_val=1)
        if count is None:
            return

        self._do_gather(count)

    def _do_gather(self, count):
        for _ in range(count):
            self.character.gathering()

    def character_crafting(self):
        items_list = self._fetch_craftable_items()
        if items_list is None:
            return

        items_map, items_map_str = self._prepare_actions_menu_data([item['name'] for item in items_list])
        craft_idx = self._prompt_int(
            'What item do you want to craft?\n'
            f'{items_map_str}\n'
            'Please type a number: '
        )
        if craft_idx is None:
            return

        self._do_crafting(items_list, items_map, craft_idx)

    def _do_crafting(self, items_list, items_map, craft_idx):
        craft_code = self._resolve_craft_code(items_list, items_map, craft_idx)
        quantity = self._prompt_int('How many do you want to create?: ', min_val=1)
        if quantity is None:
            return

        self.character.crafting(craft_code, quantity)

    def _fetch_craftable_items(self):
        location_data = self.get_location_data(self.character.layer, self.character.x, self.character.y)
        content = location_data.get('content') or {}

        if content.get('type') != MapTypesEnum.WORKSHOP:
            print('You can\'t craft anything at this location.')
            return None

        workshop_type = content.get('code', '')
        items_list = self.get_items(
            craft_skill=workshop_type,
            max_level=getattr(self.character, f'{workshop_type}_level', 1),
        )

        if not items_list:
            print('No craftable items available for your level at this workshop.')
            return None

        return items_list

    @staticmethod
    def _resolve_craft_code(items_list, items_map, craft_idx):
        return next(
            (it['code'] for it in items_list if it['name'] == items_map[craft_idx]),
            '',
        )

    def character_recycling(self):
        if not self._at_workshop():
            print('You can\'t recycle anything at this location.')
            return

        inventory = self._non_empty_inventory()
        if not inventory:
            print('Your inventory is empty.')
            return

        inventory_map, inventory_map_str = self._prepare_actions_menu_data(
            [f"{slot['code']} (x{slot.get('quantity', 1)})" for slot in inventory]
        )
        chosen_item_idx = self._prompt_int(
            'What item do you want to recycle?\n'
            f'{inventory_map_str}\n'
            'Please type a number: '
        )
        if chosen_item_idx is None:
            return

        self._do_recycle(inventory, inventory_map, chosen_item_idx)

    def _do_recycle(self, inventory, inventory_map, chosen_item_idx):
        chosen_label = inventory_map[chosen_item_idx]
        item_code = chosen_label.split(' (')[0]
        max_qty = next(
            (s.get('quantity', 1) for s in inventory if s['code'] == item_code),
            1,
        )
        quantity = self._prompt_int(f'How many do you want to recycle (max {max_qty})?: ', min_val=1)
        if quantity is None:
            return

        self.character.recycling(item_code, quantity)

    def _at_workshop(self):
        location_data = self.get_location_data(self.character.layer, self.character.x, self.character.y)
        return (location_data.get('content') or {}).get('type') == MapTypesEnum.WORKSHOP

    def _non_empty_inventory(self):
        return [slot for slot in self.character.inventory if slot.get('code')]

    def character_equip(self):
        inventory = self._non_empty_inventory()
        if not inventory:
            print('Your inventory is empty.')
            return

        inventory_map, inventory_map_str = self._prepare_actions_menu_data(
            [slot['code'] for slot in inventory]
        )
        chosen_item_idx = self._prompt_int(
            'What item do you want to equip?\n'
            f'{inventory_map_str}\n'
            'Please type a number: '
        )
        if chosen_item_idx is None:
            return

        self._do_equip(inventory_map, chosen_item_idx)

    def _do_equip(self, inventory_map, chosen_item_idx):
        item_code = inventory_map[chosen_item_idx]
        item_data = self.get_item(item_code)
        if item_data['type'] not in ItemTypesEnum.EQUIP_TYPES:
            print('This item type is not equippable.')
            return

        if item_data.get('level', 0) > self.character.level:
            print(f"You need to be level {item_data['level']} to equip this item.")
            return

        equipment_slot = self._find_equipment_slot(item_data, item_code)
        if equipment_slot is None:
            print('Could not determine a slot for this item.')
            return

        self.character.equip(item_code, equipment_slot)

    @staticmethod
    def _find_equipment_slot(item_data, item_code):
        return next(
            (s for s in EquipmentSlotsEnum
             if s == item_data['type']
             or s.startswith(item_data['type'])
             or s == item_code),
            None,
        )

    def character_unequip(self):
        slots_map, slots_map_str = self._prepare_actions_menu_data(
            [action for action in EquipmentSlotsEnum]
        )
        slot_idx = self._prompt_int(
            'Which slot do you want to unequip?\n'
            f'{slots_map_str}\n'
            'Please type a number: '
        )
        if slot_idx is None:
            return

        self.character.unequip(slots_map[slot_idx])

    def character_use_item(self):
        inventory = self._non_empty_inventory()
        if not inventory:
            print('Your inventory is empty.')
            return

        inventory_map, inventory_map_str = self._prepare_actions_menu_data(
            [slot['code'] for slot in inventory]
        )
        chosen_item_idx = self._prompt_int(
            'What item do you want to use?\n'
            f'{inventory_map_str}\n'
            'Please type a number: '
        )
        if chosen_item_idx is None:
            return

        self._do_use_item(inventory, inventory_map, chosen_item_idx)

    def _do_use_item(self, inventory, inventory_map, chosen_item_idx):
        item_code = inventory_map[chosen_item_idx]
        max_qty = next(
            (s.get('quantity', 1) for s in inventory if s['code'] == item_code),
            1,
        )
        quantity = self._prompt_int(f'How many do you want to use (max {max_qty})?: ', min_val=1)
        if quantity is None:
            return

        self.character.use_item(item_code, quantity)

    def character_delete_item(self):
        inventory = self._non_empty_inventory()
        if not inventory:
            print('Your inventory is empty.')
            return

        inventory_map, inventory_map_str = self._prepare_actions_menu_data(
            [f"{slot['code']} (x{slot.get('quantity', 1)})" for slot in inventory]
        )
        chosen_item_idx = self._prompt_int(
            'What item do you want to delete?\n'
            f'{inventory_map_str}\n'
            'Please type a number: '
        )
        if chosen_item_idx is None:
            return

        self._do_delete_item(inventory, inventory_map, chosen_item_idx)

    def _do_delete_item(self, inventory, inventory_map, chosen_item_idx):
        chosen_label = inventory_map[chosen_item_idx]
        item_code = chosen_label.split(' (')[0]
        max_qty = next(
            (s.get('quantity', 1) for s in inventory if s['code'] == item_code),
            1,
        )
        quantity = self._prompt_int(f'How many do you want to delete (max {max_qty})?: ', min_val=1)
        if quantity is None:
            return

        self.character.delete_item(item_code, quantity)

    def character_rest(self):
        self.character.rest()

    def character_change_skin(self):
        skins_map, skins_str = self._prepare_actions_menu_data(
            [skin for skin in CharacterSkinsEnum]
        )
        locked = ', '.join(s for s in CharacterSkinsEnum.SEASON_SKINS)
        sel = self._prompt_int(
            'What skin do you want to change to?\n'
            f'{skins_str}\n'
            f'Season skins ({locked}) require unlocking via achievement points.\n'
            'Please type a number: '
        )
        if sel is None:
            return

        self.character.change_skin(skins_map[sel])

    def character_get_new_task(self):
        self.character.get_task()

    def character_complete_task(self):
        self.character.complete_task()

    def character_cancel_task(self):
        self.character.cancel_task()

    def character_exchange_task_coins(self):
        self.character.exchange_task_coins()

    def character_trade_task(self):
        items_map, items_str = self._prepare_actions_menu_data(
            [slot['code'] for slot in self.character.inventory if slot.get('code')]
        )
        idx = self._prompt_int(
            'What item do you want to trade with the Tasks Master?\n'
            f'{items_str}\n'
            'Please type a number: '
        )
        if idx is None:
            return

        self._do_trade_task(items_map, idx)

    def _do_trade_task(self, items_map, idx):
        item_code = items_map[idx]
        qty = self._prompt_int('How many?: ', min_val=1)
        if qty is None:
            return

        self.character.trade_task(item_code, qty)

    def character_claim_pending_item(self):
        items = self.get_my_pending_items()
        if not items:
            print('No pending items to claim.')
            return

        items_map, items_str = self._prepare_actions_menu_data(
            [f"{it['id']} - {it['description']}" for it in items]
        )
        idx = self._prompt_int(
            'Which pending item do you want to claim?\n'
            f'{items_str}\n'
            'Please type a number: '
        )
        if idx is None:
            return

        self.character.claim_pending_item(items[idx - 1]['id'])

    def character_npc_buy_item(self):
        item_code = input('What item code do you want to buy from the NPC?: ')
        quantity = self._prompt_int('How many?: ', min_val=1)
        if quantity is None:
            return

        self.character.npc_buy(item_code, quantity)

    def character_npc_sell_item(self):
        inventory = self._non_empty_inventory()
        items_map, items_str = self._prepare_actions_menu_data(
            [slot['code'] for slot in inventory]
        )
        idx = self._prompt_int(
            'What item do you want to sell to the NPC?\n'
            f'{items_str}\n'
            'Please type a number: '
        )
        if idx is None:
            return

        self._do_npc_sell(inventory, items_map, idx)

    def _do_npc_sell(self, inventory, items_map, idx):
        item_code = items_map[idx]
        max_qty = next(
            (s.get('quantity', 1) for s in inventory if s['code'] == item_code),
            1,
        )
        qty = self._prompt_int(f'How many (max {max_qty})?: ', min_val=1)
        if qty is None:
            return

        self.character.npc_sell(item_code, qty)

    def character_buy_bank_expansion(self):
        self.character.buy_bank_expansion()

    def character_deposit_item_to_bank(self):
        inventory = self._non_empty_inventory()
        if not inventory:
            print('Your inventory is empty.')
            return

        inventory_map, inventory_map_str = self._prepare_actions_menu_data(
            [slot['code'] for slot in inventory]
        )
        chosen_item_idx = self._prompt_int(
            'What item do you want to deposit?\n'
            f'{inventory_map_str}\n'
            'Please type a number: '
        )
        if chosen_item_idx is None:
            return

        self._do_deposit_item(inventory, inventory_map, chosen_item_idx)

    def _do_deposit_item(self, inventory, inventory_map, chosen_item_idx):
        item_code = inventory_map[chosen_item_idx]
        max_qty = next(
            (s.get('quantity', 1) for s in inventory if s['code'] == item_code),
            1,
        )
        quantity = self._prompt_int(f'How many do you want to deposit (max {max_qty})?: ', min_val=1)
        if quantity is None:
            return

        self.character.deposit_item(item_code, quantity)

    def character_withdraw_item_from_bank(self):
        bank_items = self.get_my_bank_items()
        if not bank_items:
            print('Bank is empty.')
            return

        bank_items_map, bank_items_map_str = self._prepare_actions_menu_data(
            [item['code'] for item in bank_items]
        )
        chosen_item_idx = self._prompt_int(
            'What item do you want to withdraw?\n'
            f'{bank_items_map_str}\n'
            'Please type a number: '
        )
        if chosen_item_idx is None:
            return

        self._do_withdraw_item(bank_items, bank_items_map, chosen_item_idx)

    def _do_withdraw_item(self, bank_items, bank_items_map, chosen_item_idx):
        item_code = bank_items_map[chosen_item_idx]
        max_qty = next(
            (s.get('quantity', 0) for s in bank_items if s['code'] == item_code),
            0,
        )
        quantity = self._prompt_int(f'How many do you want to withdraw (bank has {max_qty})?: ', min_val=1)
        if quantity is None:
            return

        self.character.withdraw_item(item_code, quantity)

    def character_deposit_gold_to_bank(self):
        quantity = self._prompt_int(f'How many gold do you want to deposit (you have {self.character.gold})?: ', min_val=1)
        if quantity is None:
            return

        self.character.deposit_gold(quantity)

    def character_withdraw_gold_from_bank(self):
        bank = self.get_my_bank()
        quantity = self._prompt_int(f'How many gold do you want to withdraw (bank has {bank.get("gold", 0)})?: ', min_val=1)
        if quantity is None:
            return

        self.character.withdraw_gold(quantity)

    def character_give_gold(self):
        my_chars = self.get_my_characters()
        others_map, others_str = self._prepare_actions_menu_data(
            [c['name'] for c in my_chars if c['name'] != self.character.name]
        )
        if not others_map:
            print('You have no other characters.')
            return

        idx = self._prompt_int(
            'To which character do you want to give gold?\n'
            f'{others_str}\n'
            'Please type a number: '
        )
        if idx is None:
            return

        self._do_give_gold(others_map, idx)

    def _do_give_gold(self, others_map, idx):
        target = others_map[idx]
        qty = self._prompt_int(f'How many gold to give to {target} (you have {self.character.gold})?: ', min_val=1)
        if qty is None:
            return

        self.character.give_gold(target, qty)

    def character_give_item(self):
        my_chars = self.get_my_characters()
        others_map, others_str = self._prepare_actions_menu_data(
            [c['name'] for c in my_chars if c['name'] != self.character.name]
        )
        if not others_map:
            print('You have no other characters.')
            return

        idx = self._prompt_int(
            'To which character do you want to give items?\n'
            f'{others_str}\n'
            'Please type a number: '
        )
        if idx is None:
            return

        self._do_give_item(others_map, idx)

    def _do_give_item(self, others_map, idx):
        target = others_map[idx]
        inventory = self._non_empty_inventory()
        if not inventory:
            print('Your inventory is empty.')
            return

        items_map, items_str = self._prepare_actions_menu_data(
            [slot['code'] for slot in inventory]
        )
        iidx = self._prompt_int(
            'What item do you want to give?\n'
            f'{items_str}\n'
            'Please type a number: '
        )
        if iidx is None:
            return

        self._finish_give_item(inventory, items_map, iidx, target)

    def _finish_give_item(self, inventory, items_map, iidx, target):
        item_code = items_map[iidx]
        max_qty = next(
            (s.get('quantity', 1) for s in inventory if s['code'] == item_code),
            1,
        )
        qty = self._prompt_int(f'How many (max {max_qty})?: ', min_val=1)
        if qty is None:
            return

        self.character.give_item(target, item_code, qty)

    def character_ge_buy_item(self):
        orders = self.get_my_ge_orders(order_type=GEOrderTypeEnum.SELL)
        if not orders:
            print('No sell orders available to buy from.')
            return

        orders_map, orders_str = self._prepare_actions_menu_data(
            [f"{o['code']} @ {o['price']}g (x{o['quantity']})" for o in orders]
        )
        idx = self._prompt_int(
            'Which order do you want to buy from?\n'
            f'{orders_str}\n'
            'Please type a number: '
        )
        if idx is None:
            return

        self._do_ge_buy(orders, idx)

    def _do_ge_buy(self, orders, idx):
        order = orders[idx - 1]
        qty = self._prompt_int(f'How many to buy (max {order["quantity"]})?: ', min_val=1)
        if qty is None:
            return

        self.character.ge_buy(order['id'], qty)

    def character_ge_create_sell_order(self):
        inventory = self._non_empty_inventory()
        items_map, items_str = self._prepare_actions_menu_data(
            [slot['code'] for slot in inventory]
        )
        idx = self._prompt_int(
            'What item do you want to sell on the GE?\n'
            f'{items_str}\n'
            'Please type a number: '
        )
        if idx is None:
            return

        self._do_ge_create_sell_order(inventory, items_map, idx)

    def _do_ge_create_sell_order(self, inventory, items_map, idx):
        item_code = items_map[idx]
        max_qty = next(
            (s.get('quantity', 1) for s in inventory if s['code'] == item_code),
            1,
        )
        qty = self._prompt_int(f'How many to sell (max {max_qty})?: ', min_val=1)
        if qty is None:
            return

        price = self._prompt_int('At what price per unit?: ', min_val=1)
        if price is None:
            return

        self.character.ge_create_sell_order(item_code, qty, price)

    def character_ge_create_buy_order(self):
        item_code = input('What item code do you want to create a buy order for?: ')
        qty = self._prompt_int('How many?: ', min_val=1)
        if qty is None:
            return

        price = self._prompt_int('At what price per unit?: ', min_val=1)
        if price is None:
            return

        self.character.ge_create_buy_order(item_code, qty, price)

    def character_ge_fill_order(self):
        orders = self.get_my_ge_orders(order_type=GEOrderTypeEnum.BUY)
        if not orders:
            print('No buy orders to fill.')
            return

        orders_map, orders_str = self._prepare_actions_menu_data(
            [f"{o['code']} @ {o['price']}g (x{o['quantity']})" for o in orders]
        )
        idx = self._prompt_int(
            'Which buy order do you want to fill?\n'
            f'{orders_str}\n'
            'Please type a number: '
        )
        if idx is None:
            return

        self._do_ge_fill(orders, idx)

    def _do_ge_fill(self, orders, idx):
        order = orders[idx - 1]
        qty = self._prompt_int(f'How many to fill (max {order["quantity"]})?: ', min_val=1)
        if qty is None:
            return

        self.character.ge_fill(order['id'], qty)

    def character_ge_cancel_order(self):
        orders = self.get_my_ge_orders()
        if not orders:
            print('You have no open GE orders.')
            return

        orders_map, orders_str = self._prepare_actions_menu_data(
            [f"[{o['type']}] {o['code']} @ {o['price']}g (x{o['quantity']})" for o in orders]
        )
        idx = self._prompt_int(
            'Which order do you want to cancel?\n'
            f'{orders_str}\n'
            'Please type a number: '
        )
        if idx is None:
            return

        self.character.ge_cancel(orders[idx - 1]['id'])

    def show_bank(self):
        bank = self.get_my_bank()
        bank_items = self.get_my_bank_items()
        if not bank:
            print('Could not get bank details.')
            return

        self._print_bank(bank, bank_items)

    def _print_bank(self, bank, bank_items):
        print('=== Bank details ===')
        print(f'  Slots: {bank.get("slots")}')
        print(f'  Expansions: {bank.get("expansions")}')
        print(f'  Next expansion cost: {bank.get("next_expansion_cost")}g')
        print(f'  Gold: {bank.get("gold")}g')

        if bank_items:
            print('  Items:')
            for it in bank_items:
                print(f'    {it["code"]} x{it.get("quantity", 1)}')
        else:
            print('  Items: (empty)')

    def show_pending_items(self):
        items = self.get_my_pending_items()
        if not items:
            print('No pending items.')
            return

        print('=== Pending items ===')
        for it in items:
            print(f'  [{it.get("source", "?")}] {it.get("description", "")} '
                  f'(id={it.get("id")}, gold={it.get("gold", 0)})')
            for sub in it.get('items', []) or []:
                print(f'    -> {sub["code"]} x{sub.get("quantity", 1)}')

    def show_ge_orders(self):
        orders = self.get_my_ge_orders()
        if not orders:
            print('No open GE orders.')
            return

        print('=== My GE orders ===')
        for o in orders:
            print(f'  [{o["type"]}] {o["code"]} x{o["quantity"]} @ {o["price"]}g '
                  f'(id={o["id"]}, created={o.get("created_at", "?")})')

    def use_scenario(self):
        scenarios_category_map, scenarios_category_str = self._prepare_actions_menu_data(
            list(self.scenarios_storage.scenarios_category_map.keys()),
        )

        category_idx = self._prompt_int(
            'Which type of scenario do you want to launch?\n'
            f'{scenarios_category_str}\n'
            'Please type a number: '
        )
        if category_idx is None:
            return

        category = scenarios_category_map[category_idx]
        category_scenarios = self.scenarios_storage.scenarios_category_map[category]()
        scenarios_map, scenarios_map_str = self._prepare_actions_menu_data(
            [GameClient._scenario_name(scenario) for scenario in category_scenarios]
        )

        if not scenarios_map:
            print('No scenarios available in this category yet.')
            return

        if len(scenarios_map) == 1:
            scenario_idx = next(iter(scenarios_map))
        else:
            scenario_idx = self._prompt_int(
                'Which scenario do you want to launch?\n'
                f'{scenarios_map_str}\n'
                'Please type a number: '
            )
            if scenario_idx is None:
                return

        self._run_scenario(category_scenarios, scenarios_map, scenario_idx)

    def _run_scenario(self, category_scenarios, scenarios_map, scenario_idx):
        selected_scenario = next(
            scenario for scenario in category_scenarios
            if GameClient._scenario_name(scenario) == scenarios_map[scenario_idx]
        )
        params = self._collect_scenario_params(selected_scenario)
        repeats = self._scenario_repeats(params)
        self._invoke_scenario(selected_scenario, params, repeats)

    @staticmethod
    def _scenario_name(scenario):
        name = getattr(scenario, '__name__', None)
        if name is None:
            name = scenario.func.__name__
        return name

    @staticmethod
    def _collect_scenario_params(selected_scenario):
        params = {}
        print('Specify the values of the scenario startup parameters')
        for name, parameter in dict(inspect.signature(selected_scenario).parameters).items():
            parameter_type = type(parameter.default)
            raw = input(f'{name} (default: {parameter.default}): ')
            if raw == '':
                params[name] = parameter.default
            else:
                try:
                    params[name] = parameter_type(raw)
                except (ValueError, TypeError):
                    params[name] = raw
        return params

    def _scenario_repeats(self, params):
        result = 1
        if bool(params.get('sell', '')):
            prompted = self._prompt_int('How many times to repeat the scenario?: ', min_val=1)
            if prompted is not None:
                result = prompted
        return result

    @staticmethod
    def _invoke_scenario(scenario, params, repeats):
        for _ in range(max(1, repeats)):
            scenario(**params)

    def get_location_data(self, layer='overworld', x=0, y=0):
        location_data = self._get_with_reauth(url=f'/maps/{layer}/{x}/{y}')
        if location_data.status_code == 200:
            return location_data.json().get('data', {})

        if error_block := location_data.json().get('error'):
            print(error_block.get('message', 'Unknown error.'))

        return {}

    def get_maps_data(self, content_type='', content_code='', layer=''):
        params = {}
        if content_type:
            params['content_type'] = content_type
        if content_code:
            params['content_code'] = content_code
        if layer:
            params['layer'] = layer

        return self._get_all_pages('/maps', params, default=[])

    def _get_all_pages(self, url, params, default=None):
        """Fetch all pages of a paginated GET endpoint."""

        if default is None:
            default = {}
        page_params = dict(params)
        page_params.setdefault('size', 100)
        page_params['page'] = 1
        result = []
        done = False

        while not done:
            response = self._get_with_reauth(url=url, data=page_params)
            if response.status_code != 200:
                if error_block := response.json().get('error'):
                    print(error_block.get('message', 'Unknown error.'))
                return result if result else default

            payload = response.json()
            data = payload.get('data', [])
            if isinstance(data, list):
                result.extend(data)
            else:
                result.append(data)

            total_pages = payload.get('pages', 1)
            if page_params['page'] >= total_pages:
                done = True
            else:
                page_params['page'] += 1

        return result

    def get_items(self, name='', min_level=None, max_level=None, type_='',
                  craft_skill='', craft_material=''):
        params = {}
        if name:
            params['name'] = name
        if min_level is not None:
            params['min_level'] = min_level
        if max_level is not None:
            params['max_level'] = max_level
        if type_:
            params['type'] = type_
        if craft_skill:
            params['craft_skill'] = craft_skill
        if craft_material:
            params['craft_material'] = craft_material

        return self._get_all_pages('/items', params, default=[])

    def get_item(self, code=''):
        response = self._get_with_reauth(url=f'/items/{code}')
        if response.status_code == 200:
            return response.json().get('data', {})
        return {}

    def get_monsters(self, name='', min_level=None, max_level=None, drop=''):
        params = {}
        if name:
            params['name'] = name
        if min_level is not None:
            params['min_level'] = min_level
        if max_level is not None:
            params['max_level'] = max_level
        if drop:
            params['drop'] = drop

        return self._get_all_pages('/monsters', params, default=[])

    def get_monster(self, code=''):
        response = self._get_with_reauth(url=f'/monsters/{code}')
        if response.status_code == 200:
            return response.json().get('data', {})
        return {}

    def get_resources(self, min_level=None, max_level=None, skill='', drop=''):
        params = {}
        if min_level is not None:
            params['min_level'] = min_level
        if max_level is not None:
            params['max_level'] = max_level
        if skill:
            params['skill'] = skill
        if drop:
            params['drop'] = drop

        return self._get_all_pages('/resources', params, default=[])

    def get_resource(self, code=''):
        response = self._get_with_reauth(url=f'/resources/{code}')
        if response.status_code == 200:
            return response.json().get('data', {})
        return {}

    def get_maps(self, content_type='', content_code='', layer='',
                 hide_blocked_maps=False, page=1, size=100):
        params = {'page': page, 'size': size}
        if content_type:
            params['content_type'] = content_type
        if content_code:
            params['content_code'] = content_code
        if layer:
            params['layer'] = layer
        if hide_blocked_maps:
            params['hide_blocked_maps'] = 'true'

        return self._get_all_pages('/maps', params, default=[])

    def get_map_by_id(self, map_id=0):
        response = self._get_with_reauth(url=f'/maps/id/{map_id}')
        if response.status_code == 200:
            return response.json().get('data', {})
        return {}

    def get_layer_maps(self, layer='', content_type='', content_code='',
                       hide_blocked_maps=False):
        params = {}
        if content_type:
            params['content_type'] = content_type
        if content_code:
            params['content_code'] = content_code
        if hide_blocked_maps:
            params['hide_blocked_maps'] = 'true'

        return self._get_all_pages(f'/maps/{layer}', params, default=[])

    def get_map_by_position(self, layer='', x=0, y=0):
        response = self._get_with_reauth(url=f'/maps/{layer}/{x}/{y}')
        if response.status_code == 200:
            return response.json().get('data', {})
        return {}

    def get_npcs(self, name='', type_='', currency='', item=''):
        params = {}
        if name:
            params['name'] = name
        if type_:
            params['type'] = type_
        if currency:
            params['currency'] = currency
        if item:
            params['item'] = item

        return self._get_all_pages('/npcs/details', params, default=[])

    def get_npc(self, code=''):
        response = self._get_with_reauth(url=f'/npcs/details/{code}')
        if response.status_code == 200:
            return response.json().get('data', {})
        return {}

    def get_npc_items(self, code='', npc='', currency=''):
        params = {}
        if npc:
            params['npc'] = npc
        if currency:
            params['currency'] = currency

        return self._get_all_pages(f'/npcs/items/{code}', params, default=[])

    def get_all_npc_items(self, code='', npc='', currency=''):
        params = {}
        if code:
            params['code'] = code
        if npc:
            params['npc'] = npc
        if currency:
            params['currency'] = currency

        return self._get_all_pages('/npcs/items', params, default=[])

    def get_tasks(self, min_level=None, max_level=None, skill='', type_=''):
        params = {}
        if min_level is not None:
            params['min_level'] = min_level
        if max_level is not None:
            params['max_level'] = max_level
        if skill:
            params['skill'] = skill
        if type_:
            params['type'] = type_

        return self._get_all_pages('/tasks/list', params, default=[])

    def get_task(self, code=''):
        response = self._get_with_reauth(url=f'/tasks/list/{code}')
        if response.status_code == 200:
            return response.json().get('data', {})
        return {}

    def get_task_rewards(self):
        return self._get_all_pages('/tasks/rewards', {}, default=[])

    def get_task_reward(self, code=''):
        response = self._get_with_reauth(url=f'/tasks/rewards/{code}')
        if response.status_code == 200:
            return response.json().get('data', {})
        return {}

    def get_achievements(self, type_=''):
        params = {}
        if type_:
            params['type'] = type_

        return self._get_all_pages('/achievements', params, default=[])

    def get_achievement(self, code=''):
        response = self._get_with_reauth(url=f'/achievements/{code}')
        if response.status_code == 200:
            return response.json().get('data', {})
        return {}

    def get_account_achievements(self, account='', type_='', completed=None):
        params = {}
        if type_:
            params['type'] = type_
        if completed is not None:
            params['completed'] = 'true' if completed else 'false'

        return self._get_all_pages(f'/accounts/{account}/achievements', params, default=[])

    def get_badges(self):
        return self._get_all_pages('/badges', {}, default=[])

    def get_badge(self, code=''):
        response = self._get_with_reauth(url=f'/badges/{code}')
        if response.status_code == 200:
            return response.json().get('data', {})
        return {}

    def get_effects(self):
        return self._get_all_pages('/effects', {}, default=[])

    def get_effect(self, code=''):
        response = self._get_with_reauth(url=f'/effects/{code}')
        if response.status_code == 200:
            return response.json().get('data', {})
        return {}

    def get_events(self, type_=''):
        params = {}
        if type_:
            params['type'] = type_

        return self._get_all_pages('/events', params, default=[])

    def get_active_events(self):
        return self._get_all_pages('/events/active', {}, default=[])

    def spawn_event(self, code=''):
        """Spawn an event (consumes account event token)."""

        if not code:
            code = input('What event code do you want to spawn?: ')

        response = self._post_with_reauth(url='/events/spawn', data={'code': code})
        if response.status_code == 200:
            print(f'Event {code} spawned.')
            return

        if error_block := response.json().get('error'):
            print(error_block.get('message', 'Unknown error.'))

    def get_ge_history_by_code(self, code='', account=''):
        params = {}
        if account:
            params['account'] = account

        return self._get_all_pages(f'/grandexchange/history/{code}', params, default=[])

    def get_ge_orders(self, code='', account='', order_type=''):
        params = {}
        if code:
            params['code'] = code
        if account:
            params['account'] = account
        if order_type:
            params['type'] = order_type

        return self._get_all_pages('/grandexchange/orders', params, default=[])

    def get_ge_order(self, order_id=''):
        response = self._get_with_reauth(url=f'/grandexchange/orders/{order_id}')
        if response.status_code == 200:
            return response.json().get('data', {})
        return {}

    def get_my_ge_orders(self, code='', order_type=''):
        params = {}
        if code:
            params['code'] = code
        if order_type:
            params['type'] = order_type

        return self._get_all_pages('/my/grandexchange/orders', params, default=[])

    def get_my_ge_history(self, code='', order_id=''):
        params = {}
        if code:
            params['code'] = code
        if order_id:
            params['id'] = order_id

        return self._get_all_pages('/my/grandexchange/history', params, default=[])

    def get_my_pending_items(self):
        return self._get_all_pages('/my/pending-items', {}, default=[])

    def get_my_logs(self):
        return self._get_all_pages('/my/logs', {'size': 50}, default=[])

    def get_character_logs(self, name=''):
        return self._get_all_pages(f'/my/logs/{name}', {'size': 50}, default=[])

    def get_my_bank(self):
        response = self._get_with_reauth(url='/my/bank')
        if response.status_code == 200:
            return response.json().get('data', {})
        return {}

    def get_my_bank_items(self, item_code=''):
        params = {}
        if item_code:
            params['item_code'] = item_code

        return self._get_all_pages('/my/bank/items', params, default=[])

    def get_leaderboard_accounts(self, sort='', name='', page=1, size=20):
        params = {'page': page, 'size': size}
        if sort:
            params['sort'] = sort
        if name:
            params['name'] = name

        return self._get_all_pages('/leaderboard/accounts', params, default=[])

    def get_leaderboard_characters(self, sort='', name='', page=1, size=20):
        params = {'page': page, 'size': size}
        if sort:
            params['sort'] = sort
        if name:
            params['name'] = name

        return self._get_all_pages('/leaderboard/characters', params, default=[])

    def get_active_characters(self):
        return self._get_all_pages('/characters/active', {}, default=[])

    def get_account_characters(self, account=''):
        response = self._get_with_reauth(url=f'/accounts/{account}/characters')
        if response.status_code == 200:
            return response.json().get('data', [])
        return []

    def get_account_info(self, account=''):
        response = self._get_with_reauth(url=f'/accounts/{account}')
        if response.status_code == 200:
            return response.json().get('data', {})
        return {}

    def run_fight_simulation(self):
        """Simulate a fight using fake characters."""

        monster_code = input('Monster code to simulate against: ')
        iterations = self._prompt_iterations()
        characters = self._prompt_simulation_characters()

        response = self._post_with_reauth(url='/simulation/fight_simulation', data={
            'monster': monster_code,
            'iterations': iterations,
            'characters': characters,
        })
        if response.status_code == 200:
            self._print_simulation_result(response, iterations)
        elif error_block := response.json().get('error'):
            print(error_block.get('message', 'Unknown error.'))

    @staticmethod
    def _prompt_iterations():
        try:
            return int(input('Iterations (default 1000): ') or 1000)
        except ValueError:
            return 1000

    @staticmethod
    def _prompt_simulation_characters():
        chars_raw = input('Character config as JSON (list of dicts, see docs). Press Enter to use defaults: ')
        if not chars_raw.strip():
            return []

        try:
            import json as _json
            return _json.loads(chars_raw)
        except ValueError as err:
            print(f'Invalid JSON: {err}')
            return None

    @staticmethod
    def _print_simulation_result(response, iterations):
        data = response.json().get('data', {})
        print('=== Simulation result ===')
        print(f'  Monster: {data.get("monster", {}).get("name", "?")} (lvl {data.get("monster", {}).get("level", "?")})')
        print(f'  Win rate: {data.get("win_rate", "?")}%')
        print(f'  Average turns: {data.get("average_turns", "?")}')
        print(f'  Total simulations: {iterations}')


class Character(BaseGameClient):
    """Client for character-level interaction."""

    CHARACTER_INFO_FIELDS = (
        'name', 'account', 'skin', 'level', 'xp', 'max_xp', 'gold',
        'mining_level', 'mining_xp', 'mining_max_xp',
        'woodcutting_level', 'woodcutting_xp', 'woodcutting_max_xp',
        'fishing_level', 'fishing_xp', 'fishing_max_xp',
        'weaponcrafting_level', 'weaponcrafting_xp', 'weaponcrafting_max_xp',
        'gearcrafting_level', 'gearcrafting_xp', 'gearcrafting_max_xp',
        'jewelrycrafting_level', 'jewelrycrafting_xp', 'jewelrycrafting_max_xp',
        'cooking_level', 'cooking_xp', 'cooking_max_xp',
        'alchemy_level', 'alchemy_xp', 'alchemy_max_xp',
        'hp', 'max_hp', 'haste', 'critical_strike', 'wisdom', 'prospecting',
        'initiative', 'threat',
        'attack_fire', 'attack_earth', 'attack_water', 'attack_air',
        'dmg', 'dmg_fire', 'dmg_earth', 'dmg_water', 'dmg_air',
        'res_fire', 'res_earth', 'res_water', 'res_air',
        'effects',
        'x', 'y', 'layer', 'map_id',
        'cooldown', 'cooldown_expiration',
        'weapon_slot', 'shield_slot', 'helmet_slot', 'body_armor_slot',
        'leg_armor_slot', 'boots_slot', 'ring1_slot', 'ring2_slot',
        'amulet_slot', 'artifact1_slot', 'artifact2_slot', 'artifact3_slot',
        'rune_slot', 'utility1_slot', 'utility1_slot_quantity',
        'utility2_slot', 'utility2_slot_quantity', 'bag_slot',
        'task', 'task_type', 'task_progress', 'task_total',
        'inventory_max_items', 'inventory',
    )

    def __init__(self, name, parent=None) -> None:
        super().__init__()

        self.name = name
        self.parent = parent
        self.base_character_action_url = f'/my/{self.name}/action'
        self.refresh()

    def _get_with_reauth(self, url, data=None):
        """Run an authenticated GET, automatically offering a re-login if
        the token is rejected. Mirrors GameClient's wrapper but also
        propagates the new token to the parent client so account-level
        calls don't have to re-auth again."""

        response = self._get(url=url, data=data)

        if self.is_invalid_token_error(response) and self.ensure_valid_token(probe_response=response):
            self._propagate_token_to_parent()
            response = self._get(url=url, data=data)

        return response

    def _post_with_reauth(self, url, data=None):
        """Run an authenticated POST with the same re-login behaviour as
        _get_with_reauth."""

        response = self._post(url=url, data=data)

        if self.is_invalid_token_error(response) and self.ensure_valid_token(probe_response=response):
            self._propagate_token_to_parent()
            response = self._post(url=url, data=data)

        return response

    def _propagate_token_to_parent(self):
        """Copy the freshly-issued token to the parent GameClient so that
        subsequent account-level calls don't have to re-auth separately."""

        if self.parent is not None and hasattr(self.parent, 'base_headers'):
            self.parent.base_headers['Authorization'] = self.base_headers.get('Authorization', '')

    def refresh(self):
        """Pull fresh character data from the API."""

        self._get_character_info()
        return self

    def _get_character_info(self):
        response = self._get_with_reauth(url=f'/characters/{self.name}')
        if response.status_code != 200:
            if error_block := response.json().get('error'):
                print(error_block.get('message', 'Unknown error.'))
            return

        for key in self.CHARACTER_INFO_FIELDS:
            if key in response.json().get('data', {}):
                setattr(self, key, response.json()['data'][key])

    def _get_last_action(self):
        last_action_data = self._get_with_reauth(
            url=f'/my/logs',
            data={
                'page': 1,
                'size': 1,
            },
        )

        if last_action_data.status_code == 200:
            logs = last_action_data.json().get('data', [])
            if logs:
                print(logs[0].get('description', ''))
            else:
                print('No recent actions.')
        elif error_block := last_action_data.json().get('error'):
            print(f'Can\'t get last action. {error_block.get("message", "Unknown error.")}.')

        self.refresh()

    def _do_action(self, action_name='', action_data=None):
        if action_data is None:
            action_data = {}

        url = f'{self.base_character_action_url}/{action_name}'
        action_request = self._post_with_reauth(url=url, data=action_data)
        result = self._handle_action_response(action_request, action_name)

        return result

    def _handle_action_response(self, action_request, action_name):
        result = None

        if action_request.status_code == 200:
            data = action_request.json().get('data', {})
            cooldown = data.get('cooldown', {})
            reason = cooldown.get('reason', action_name)
            total_seconds = cooldown.get('total_seconds', 0)
            print(f'Performing action {reason}. It\'ll take {total_seconds} seconds.')

            for i in range(total_seconds, 0, -1):
                print(f'Waiting {i} seconds...', end=' \r')
                sleep(1)

            print(' ' * 40, end='\r')
            self._get_last_action()
            result = data
        elif error_block := action_request.json().get('error'):
            print(f'Can\'t perform action. {error_block.get("message", "Unknown error.")}')

        return result

    def move(self, x=0, y=0, map_id=None):
        data = {}
        if map_id is not None:
            data['map_id'] = map_id
        else:
            data['x'] = x
            data['y'] = y
        return self._do_action('move', data)

    def transition(self):
        return self._do_action('transition')

    def fight(self, participants=None):
        data = {}
        if participants:
            data['participants'] = participants

        return self._do_action('fight', data)

    def _get_gathering_skill_at_location(self):
        response = self._get(url=f'/maps/{self.layer}/{self.x}/{self.y}')
        if response.status_code != 200:
            return None

        map_data = response.json().get('data', {})
        content = map_data.get('interactions', {}).get('content', {})
        if content.get('type') != 'resource':
            return None

        resource_code = content.get('code', '')
        if not resource_code:
            return None

        resource_response = self._get(url=f'/resources/{resource_code}')
        if resource_response.status_code != 200:
            return None

        return resource_response.json().get('data', {}).get('skill')

    def _equip_best_gathering_weapon(self, skill_code):
        if not skill_code:
            return

        current_weapon = getattr(self, 'weapon_slot', None)
        best_code = None
        best_value = 0

        for slot in self.inventory or []:
            code = slot.get('code')
            if not code or code == current_weapon:
                continue

            item_response = self._get(url=f'/items/{code}')
            if item_response.status_code != 200:
                continue

            item = item_response.json().get('data', {})
            if item.get('type') != 'weapon':
                continue

            for effect in item.get('effects') or []:
                if effect.get('code') == skill_code:
                    value = abs(effect.get('value', 0))
                    if value > best_value:
                        best_value = value
                        best_code = code
                    break

        if best_code is None:
            return

        current_value = 0
        if current_weapon:
            item_response = self._get(url=f'/items/{current_weapon}')
            if item_response.status_code == 200:
                current_item = item_response.json().get('data', {})
                for effect in current_item.get('effects') or []:
                    if effect.get('code') == skill_code:
                        current_value = abs(effect.get('value', 0))
                        break

        if best_value > current_value:
            print(f'Equipping {best_code} (+{best_value} {skill_code})...')
            self.equip(best_code, 'weapon')

    def gathering(self):
        skill_code = self._get_gathering_skill_at_location()
        if skill_code:
            self._equip_best_gathering_weapon(skill_code)

        return self._do_action('gathering')

    def crafting(self, code='', quantity=1):
        return self._do_action('crafting', {'code': code, 'quantity': quantity})

    def recycling(self, code='', quantity=1):
        return self._do_action('recycling', {'code': code, 'quantity': quantity})

    def equip(self, code='', slot='', quantity=None):
        data = {'code': code, 'slot': slot}
        if quantity is not None:
            data['quantity'] = quantity
        return self._do_action('equip', data)

    def unequip(self, slot='', quantity=None):
        data = {'slot': slot}
        if quantity is not None:
            data['quantity'] = quantity
        return self._do_action('unequip', data)

    def use_item(self, code='', quantity=1):
        return self._do_action('use', {'code': code, 'quantity': quantity})

    def delete_item(self, code='', quantity=1):
        return self._do_action('delete', {'code': code, 'quantity': quantity})

    def rest(self):
        return self._do_action('rest')

    def change_skin(self, skin=''):
        return self._do_action('change_skin', {'skin': skin})

    def get_task(self):
        return self._do_action('task/new')

    def complete_task(self):
        return self._do_action('task/complete')

    def cancel_task(self):
        return self._do_action('task/cancel')

    def exchange_task_coins(self):
        return self._do_action('task/exchange')

    def trade_task(self, code='', quantity=1):
        return self._do_action('task/trade', {'code': code, 'quantity': quantity})

    def deposit_item(self, code='', quantity=1):
        return self._do_action('bank/deposit/item', {'code': code, 'quantity': quantity})

    def deposit_gold(self, quantity=0):
        return self._do_action('bank/deposit/gold', {'quantity': quantity})

    def withdraw_item(self, code='', quantity=1):
        return self._do_action('bank/withdraw/item', {'code': code, 'quantity': quantity})

    def withdraw_gold(self, quantity=0):
        return self._do_action('bank/withdraw/gold', {'quantity': quantity})

    def buy_bank_expansion(self):
        return self._do_action('bank/buy_expansion')

    def give_gold(self, character='', quantity=0):
        return self._do_action('give/gold', {'character': character, 'quantity': quantity})

    def give_item(self, character='', code='', quantity=1):
        return self._do_action('give/item', {
            'character': character,
            'items': [{'code': code, 'quantity': quantity}],
        })

    def claim_pending_item(self, pending_id=''):
        return self._do_action(f'claim_item/{pending_id}')

    def ge_buy(self, order_id='', quantity=1):
        return self._do_action('grandexchange/buy', {'id': order_id, 'quantity': quantity})

    def ge_sell(self, code='', quantity=1, price=0):
        return self._do_action(
            'grandexchange/create-sell-order',
            {'code': code, 'quantity': quantity, 'price': price},
        )

    def ge_create_buy_order(self, code='', quantity=1, price=0):
        return self._do_action(
            'grandexchange/create-buy-order',
            {'code': code, 'quantity': quantity, 'price': price},
        )

    def ge_create_sell_order(self, code='', quantity=1, price=0):
        return self._do_action(
            'grandexchange/create-sell-order',
            {'code': code, 'quantity': quantity, 'price': price},
        )

    def ge_fill(self, order_id='', quantity=1):
        return self._do_action('grandexchange/fill', {'id': order_id, 'quantity': quantity})

    def ge_cancel(self, order_id=''):
        return self._do_action('grandexchange/cancel', {'id': order_id})

    def npc_buy(self, code='', quantity=1):
        return self._do_action('npc/buy', {'code': code, 'quantity': quantity})

    def npc_sell(self, code='', quantity=1):
        return self._do_action('npc/sell', {'code': code, 'quantity': quantity})
