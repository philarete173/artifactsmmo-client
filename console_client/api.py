import random
import re
import sys
from time import sleep

from base import BaseGameClient
from base.display import Display
from base.enums import (
    CharacterSexEnum,
    CharacterSkinsEnum,
    ActionTypeEnum,
    EquipmentSlotsEnum,
    MapTypesEnum,
    ItemTypesEnum,
    GEOrderTypeEnum,
    ImageCategoryEnum,
    MapLayerEnum,
)
from scripts import ScenariosStorage
from base.images import display_image


class GameClient(BaseGameClient):
    """Client for interacting with the game world (account-level operations)."""

    def __init__(self, display=None):
        super().__init__()

        self.display = display or ConsoleDisplay()

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
            ActionTypeEnum.SHOW_ACCOUNT_DETAILS: self._show_account_details,
            ActionTypeEnum.CHANGE_PASSWORD: self.change_password,
            ActionTypeEnum.LOGIN_WITH_PASSWORD: self.login_with_password,
            ActionTypeEnum.CREATE_CHARACTER: self._prompt_and_create_character,
        }

    def main_loop(self):
        """Top-level menu: account-level actions plus character selection.
        Selecting a character enters the per-character action loop; when
        that loop returns, control comes back here so the user can pick
        a different character or perform account-level actions."""

        self.show_current_season()

        while True:
            actions_map, actions_str = self.display.prepare_menu(ActionTypeEnum.ACCOUNT_ACTIONS)
            idx = self.display.prompt_int(
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

            self.display.print('')

    def _dispatch_account_action(self, current_action):
        method = self.account_menu_map.get(current_action)

        if method is None:
            self.display.print('This is not a valid action!')
            return

        try:
            method()
        except Exception as error:
            self.display.print(f'Something went wrong. Error: {error}. Please try again.')

    def character_action_loop(self):
        """Per-character action menu with 3 top-level categories."""

        while True:
            current_location_data = self.get_location_data(
                self.character.layer, self.character.x, self.character.y,
            )
            self.display.show_location(current_location_data)

            choice = self.display.prompt_int(
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

            self.display.print('')

    def _handle_basic_actions(self, location_data):
        location_type = ((location_data.get('interactions') or {}).get('content') or {}).get('type', None)
        actions = list(ActionTypeEnum.LOCATION_ACTIONS_MAP.get(location_type, []))

        if (location_data.get('interactions') or {}).get('transition'):
            actions.append(ActionTypeEnum.TRANSITION)

        actions_map, actions_str = self.display.prepare_menu(actions)
        idx = self.display.prompt_int(
            'Basic actions:\n'
            f'{actions_str}\n'
            'Please type a number: '
        )
        if idx is None or idx not in actions_map:
            return

        current_action = actions_map[idx]
        method = self.main_menu_map.get(current_action)
        if method is None:
            self.display.print('This is not a valid action!')
        else:
            try:
                method()
            except Exception as error:
                self.display.print(f'Something went wrong. Error: {error}. Please try again.')

    def _handle_advanced_actions(self):
        actions_map, actions_str = self.display.prepare_menu(ActionTypeEnum.ADVANCED_ACTIONS)
        idx = self.display.prompt_int(
            'Advanced actions:\n'
            f'{actions_str}\n'
            'Please type a number: '
        )
        if idx is None or idx not in actions_map:
            return

        current_action = actions_map[idx]
        method = self.main_menu_map.get(current_action)
        if method is None:
            self.display.print('This is not a valid action!')
        else:
            try:
                method()
            except Exception as error:
                self.display.print(f'Something went wrong. Error: {error}. Please try again.')

    def _handle_character_actions(self):
        actions_map, actions_str = self.display.prepare_menu(ActionTypeEnum.CHARACTER_ACTIONS)
        idx = self.display.prompt_int(
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
        self.display.show_stats(self.character)

    def _show_character_skills(self):
        self.display.show_skills(self.character)

    def _show_character_inventory(self):
        inventory = getattr(self.character, 'inventory', None) or []
        unique_codes = set(slot.get('code') for slot in inventory if slot.get('code'))
        self.display.print('Loading items data...', end='\r')
        item_names = {}
        for item_code in unique_codes:
            item = self.get_item(item_code)
            item_names[item_code] = (item or {}).get('name', item_code)
        self.display.show_inventory(self.character, item_names)

    def _show_character_equipment(self):
        effects_data = self.get_effects()
        effect_names = {effect['code']: effect['name'] for effect in effects_data if 'code' in effect}

        unique_codes = set()
        for slot_name in ('weapon', 'shield', 'helmet', 'body_armor', 'leg_armor', 'boots',
                          'ring1', 'ring2', 'amulet', 'artifact1', 'artifact2', 'artifact3',
                          'rune', 'utility1', 'utility2', 'bag'):
            item_code = getattr(self.character, f'{slot_name}_slot', None)
            if item_code:
                unique_codes.add(item_code)

        self.display.print('Loading items data...', end='\r')
        items_data = {}
        for code in unique_codes:
            items_data[code] = self.get_item(code)
        self.display.show_equipment(self.character, effect_names, items_data)

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
            self.display.print('You have no characters. Creating a new one...')
            created = self._prompt_and_create_character()
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
        self.display.print(f'Characters on account: {", ".join(characters_map.values())}')

        idx = self._prompt_int(
            'Which character do you want to choose?\n'
            f'{characters_map_str}\n'
            'Please type a number: '
        )

        if idx is None or idx not in characters_map:
            return None

        return self._build_character(characters_map[idx])

    def _build_character(self, name):
        character = Character(name, parent=self, display=self.display)
        self.display.print(f'Selected character {name}.')
        self.display.print(f'Level {character.level}, HP {character.hp}/{character.max_hp}, '
                           f'Gold {character.gold}, Cooldown {character.cooldown}s.')
        self.display.show_image(ImageCategoryEnum.CHARACTERS, character.skin)

        return character

    def show_current_season(self):
        """Show the current season info at startup. Also acts as a
        network availability check (exits if the server is unreachable)."""

        response = self._get()

        if response.status_code != 200:
            sys.exit('Can\'t reach the server. Please try again later.')

        data = response.json().get('data', {})
        self.display.print(f'Game version: {data.get("version", "?")}.')

        season = data.get('season') or {}
        name = season.get('name', '?')
        number = season.get('number', '?')
        start = season.get('start_date', '?')
        self.display.print(f'Current season: {name} (#{number}), started {start}.')

    def _get_with_reauth(self, url, data=None):
        """Run an authenticated GET, automatically offering a re-login if
        the token is rejected. Returns the response object."""

        self.display.show_loading()
        response = self._get(url=url, data=data)
        self.display.hide_loading()

        if self.is_invalid_token_error(response) and self.ensure_valid_token(probe_response=response):
            self._propagate_token_to_characters()
            self.display.show_loading()
            response = self._get(url=url, data=data)
            self.display.hide_loading()

        return response

    def _post_with_reauth(self, url, data=None):
        """Run an authenticated POST, automatically offering a re-login if
        the token is rejected. Returns the response object."""

        self.display.show_loading()
        response = self._post(url=url, data=data)
        self.display.hide_loading()

        if self.is_invalid_token_error(response) and self.ensure_valid_token(probe_response=response):
            self._propagate_token_to_characters()
            self.display.show_loading()
            response = self._post(url=url, data=data)
            self.display.hide_loading()

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

    def _print_error_silently(self, response):
        try:
            if error_block := response.json().get('error'):
                self.display.print(error_block.get('message', 'Unknown error.'))
        except ValueError:
            pass

    def create_character(self, name, sex):
        """Create a new character. Returns True on success."""
        self.display.print(f'Creating character {name}...')

        create_request = self._post_with_reauth(
            url='/characters/create',
            data={
                'name': name,
                'skin': random.choice(CharacterSexEnum.SEX_SKIN_MAP[sex]),
            },
        )

        if create_request.status_code == 200:
            self.display.print(f'Character {name} successfully created.')
            return True

        if error_block := create_request.json().get('error'):
            self.display.print(error_block.get('message', 'Unknown error.'))

        return False

    def _prompt_and_create_character(self):
        """Prompt for name/sex via display and create character (console path)."""
        name = self._display_prompt_character_name()
        if name is None:
            return False
        sex = self._display_prompt_character_sex()
        if sex is None:
            return False
        ok = self.create_character(name, sex)
        if ok:
            self.display.print('You can now select the new character from the menu.')
        return ok

    def _display_prompt_character_name(self):
        while True:
            name = self.display.prompt_str('New character name (3-12 chars, a-z, 0-9, _ -): ')
            if name is None:
                return None
            if re.match(r'^[a-zA-Z0-9_-]{3,12}$', name):
                return name
            self.display.print('Name must be 3-12 characters using only a-z, 0-9, _, -.')

    def _display_prompt_character_sex(self):
        while True:
            sex = self.display.prompt_str('Sex: male (m) / female (f) / random (r): ')
            if sex is None:
                return None
            sex = sex.strip().lower()
            if sex in ('m', 'f', 'r'):
                return sex
            self.display.print('Please enter m, f, or r.')

    def delete_character(self, name=''):
        """Delete a character."""

        if not name:
            name = input('What is the name of the character to delete?: ')

        confirm = self._prompt_yes_no(f'Are you sure you want to permanently delete {name}?')
        if not confirm:
            self.display.print('Deletion cancelled.')
            return False

        response = self._post_with_reauth(url='/characters/delete', data={'name': name})

        if response.status_code == 200:
            self.display.print(f'Character {name} successfully deleted.')
            return True

        if error_block := response.json().get('error'):
            self.display.print(error_block.get('message', 'Unknown error.'))

        return False

    def get_account_details(self):
        """Return account details dict, or None on failure."""

        response = self._get_with_reauth(url='/my/details')
        if response.status_code != 200:
            self.display.print('Failed to get account details.')
            return None

        data = response.json().get('data', {})
        return data

    def _show_account_details(self):
        """Display account details (console path from account menu)."""
        data = self.get_account_details()
        if data is not None:
            self.display.print('=== Account details ===')
            for key, value in data.items():
                self.display.print(f'  {key}: {value}')

    def change_password(self):
        """Change account password."""

        current = input('Enter current password: ')
        new = input('Enter new password: ')
        response = self._post_with_reauth(url='/my/change_password', data={
            'current_password': current,
            'new_password': new,
        })

        if response.status_code == 200:
            self.display.print('Password changed. Note: your token has been reset, update config.ini.')
            return

        if error_block := response.json().get('error'):
            self.display.print(error_block.get('message', 'Unknown error.'))

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
        return self.display.prepare_menu(iterable)

    def _prompt_int(self, prompt, min_val=None, max_val=None):
        return self.display.prompt_int(prompt, min_val, max_val)

    def _prompt_str(self, prompt, allow_empty=True):
        return self.display.prompt_str(prompt, allow_empty)


    def character_movement(self):
        layer = getattr(self.character, 'layer', MapLayerEnum.OVERWORLD)
        maps = self.get_maps_data(layer=layer)
        available_types_map, available_types_str = self._build_location_type_menu(maps)

        location_type_idx = self._prompt_int(
            'What type of location do you want to move to?\n'
            f'{available_types_str}\n'
            'Please type a number: '
        )

        if location_type_idx is None:
            return

        chosen_locations = self._select_destinations(maps, available_types_map, location_type_idx)
        if not chosen_locations:
            return

        self._prompt_and_move(chosen_locations)

    def _build_location_type_menu(self, maps):
        available_types = sorted(
            map_type
            for map_type in{((_map.get('interactions') or {}).get('content') or {}).get('type', '') for _map in maps}
            if map_type
        )
        return self._prepare_actions_menu_data(available_types)

    def _select_destinations(self, maps, available_types_map, location_type_idx):
        if location_type_idx == 0:
            return maps

        chosen_location_type = available_types_map[location_type_idx]
        return [
            _map
            for _map in maps
            if ((_map.get('interactions') or {}).get('content') or {}).get('type', '') == chosen_location_type
        ]

    def _prompt_and_move(self, chosen_locations):
        chosen_locations_map, chosen_locations_str = self._prepare_actions_menu_data(
            [
                f'{_map.get("interactions", {}).get("content", {}).get("code")} (Location {_map["x"]}, {_map["y"]})'
                for _map in chosen_locations
            ]
        )

        if len(chosen_locations_map) == 0:
            self.display.print('No destinations of the chosen type.')
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
        self.display.start_batch(count)
        for _ in range(count):
            self.character.fight(participants=participants or None)
        self.display.end_batch()

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
        self.display.start_batch(count)
        for _ in range(count):
            self.character.gathering()
        self.display.end_batch()

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
            self.display.print('You can\'t craft anything at this location.')
            return None

        workshop_type = content.get('code', '')
        items_list = self.get_items(
            craft_skill=workshop_type,
            max_level=getattr(self.character, f'{workshop_type}_level', 1),
        )

        if not items_list:
            self.display.print('No craftable items available for your level at this workshop.')
            return None

        return items_list

    def _resolve_craft_code(self, items_list, items_map, craft_idx):
        return next(
            (it['code'] for it in items_list if it['name'] == items_map[craft_idx]),
            '',
        )

    def character_recycling(self):
        if not self._at_workshop():
            self.display.print('You can\'t recycle anything at this location.')
            return

        inventory = self._non_empty_inventory()
        if not inventory:
            self.display.print('Your inventory is empty.')
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

        self._ensure_at_correct_workshop(item_code)
        self.character.recycling(item_code, quantity)

    def _ensure_at_correct_workshop(self, item_code):
        item = self.get_item(code=item_code)
        craft = item.get('craft') or {}
        skill = craft.get('skill', '')
        if skill:
            response = self._get_with_reauth(url='/maps', data={'content_code': skill, 'size': 1})
            if response.status_code == 200:
                data = response.json().get('data', [])
                if data:
                    loc = data[0]
                    self.character.move(loc['x'], loc['y'])

    def _at_workshop(self):
        location_data = self.get_location_data(self.character.layer, self.character.x, self.character.y)
        return location_data.get('interactions', {}).get('content', {}).get('type') == MapTypesEnum.WORKSHOP

    def _non_empty_inventory(self):
        return [slot for slot in self.character.inventory if slot.get('code')]

    def character_equip(self):
        inventory = self._non_empty_inventory()
        if not inventory:
            self.display.print('Your inventory is empty.')
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
            self.display.print('This item type is not equippable.')
            return

        if item_data.get('level', 0) > self.character.level:
            self.display.print(f"You need to be level {item_data['level']} to equip this item.")
            return

        matching_slots = [
            s for s in EquipmentSlotsEnum
            if s == item_data['type']
            or s.startswith(item_data['type'])
            or s == item_code
        ]

        if not matching_slots:
            self.display.print('Could not determine a slot for this item.')
            return

        if len(matching_slots) == 1:
            equip_slot = matching_slots[0]
        else:
            def _slot_label(s):
                return s.replace('_slot', '').replace('_', ' ').title()

            slot_options = [
                {
                    'code': s,
                    'name': f'{_slot_label(s)} (occupied)'
                            if getattr(self.character, f'{s}_slot', None)
                            else f'{_slot_label(s)} (empty)'
                }
                for s in matching_slots
            ]
            slots_map, slots_map_str = self._prepare_actions_menu_data(slot_options)
            chosen_idx = self._prompt_int(
                'Which slot do you want to equip to?\n'
                f'{slots_map_str}\n'
                'Please type a number: '
            )
            if chosen_idx is None:
                return
            equip_slot = slots_map[chosen_idx]['code']

        quantity = None
        if equip_slot in ('utility1', 'utility2'):
            inv_qty = next(
                (s.get('quantity', 1) for s in (self.character.inventory or [])
                 if s.get('code') == item_code),
                1,
            )
            qty = self._prompt_int(f'How many to equip (max {inv_qty})?: ', min_val=1)
            if qty is not None:
                quantity = qty

        self.character.equip(item_code, equip_slot, quantity)

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
            self.display.print('Your inventory is empty.')
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
            self.display.print('Your inventory is empty.')
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
            self.display.print('No pending items to claim.')
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
            self.display.print('Your inventory is empty.')
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
            self.display.print('Bank is empty.')
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
            self.display.print('You have no other characters.')
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
            self.display.print('You have no other characters.')
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
            self.display.print('Your inventory is empty.')
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
            self.display.print('No sell orders available to buy from.')
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
            self.display.print('No buy orders to fill.')
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
            self.display.print('You have no open GE orders.')
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
            self.display.print('Could not get bank details.')
            return

        self._print_bank(bank, bank_items)

    def _print_bank(self, bank, bank_items):
        self.display.print('=== Bank details ===')
        self.display.print(f'  Slots: {bank.get("slots")}')
        self.display.print(f'  Expansions: {bank.get("expansions")}')
        self.display.print(f'  Next expansion cost: {bank.get("next_expansion_cost")}g')
        self.display.print(f'  Gold: {bank.get("gold")}g')

        if bank_items:
            self.display.print('  Items:')
            for it in bank_items:
                self.display.print(f'    {it["code"]} x{it.get("quantity", 1)}')
        else:
            self.display.print('  Items: (empty)')

    def show_pending_items(self):
        items = self.get_my_pending_items()
        if not items:
            self.display.print('No pending items.')
            return

        self.display.print('=== Pending items ===')
        for it in items:
            self.display.print(f'  [{it.get("source", "?")}] {it.get("description", "")} '
                  f'(id={it.get("id")}, gold={it.get("gold", 0)})')
            for sub in it.get('items', []) or []:
                self.display.print(f'    -> {sub["code"]} x{sub.get("quantity", 1)}')

    def show_ge_orders(self):
        orders = self.get_my_ge_orders()
        if not orders:
            self.display.print('No open GE orders.')
            return

        self.display.print('=== My GE orders ===')
        for o in orders:
            self.display.print(f'  [{o["type"]}] {o["code"]} x{o["quantity"]} @ {o["price"]}g '
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
            [self._scenario_name(scenario) for scenario in category_scenarios]
        )

        if not scenarios_map:
            self.display.print('No scenarios available in this category yet.')
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
            if self._scenario_name(scenario) == scenarios_map[scenario_idx]
        )
        params = self._collect_scenario_params(selected_scenario)
        repeats = self._scenario_repeats(params)
        self._invoke_scenario(selected_scenario, params, repeats, self.display)

    def _collect_scenario_params(self, scenario):
        import inspect
        sig = inspect.signature(scenario)
        params = {}
        for name, param in sig.parameters.items():
            if param.default is inspect.Parameter.empty:
                val = self._prompt_int(f'Enter value for "{name}": ', min_val=1)
                if val is not None:
                    params[name] = val
            else:
                hint = f' (default: {param.default})'
                val = self._prompt_int(f'Enter value for "{name}"{hint}: ', min_val=1)
                if val is not None:
                    params[name] = val
        return params

    def _scenario_repeats(self, params):
        return params.pop('quantity', params.pop('count', 1))

    def _scenario_name(self, scenario):
        return scenario.func.__name__.replace('_', ' ').title()

    def _invoke_scenario(self, scenario, params, repeats, display=None):
        if display and repeats > 1:
            display.start_batch(repeats)
        for _ in range(max(1, repeats)):
            scenario(**params)
        if display and repeats > 1:
            display.end_batch()

    def get_location_data(self, layer='overworld', x=0, y=0):
        location_data = self._get_with_reauth(url=f'/maps/{layer}/{x}/{y}')
        if location_data.status_code == 200:
            return location_data.json().get('data', {})

        if error_block := location_data.json().get('error'):
            self.display.print(error_block.get('message', 'Unknown error.'))

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
                    self.display.print(error_block.get('message', 'Unknown error.'))
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
            self.display.print(f'Event {code} spawned.')
            return

        if error_block := response.json().get('error'):
            self.display.print(error_block.get('message', 'Unknown error.'))

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
            self.display.print(error_block.get('message', 'Unknown error.'))

    def _prompt_iterations(self):
        val = self.display.prompt_int('Iterations (default 1000): ')
        return val if val else 1000

    def _prompt_simulation_characters(self):
        chars_raw = self.display.prompt_str(
            'Character config as JSON (list of dicts, see docs). Press Enter to use defaults: '
        )
        if not chars_raw or not chars_raw.strip():
            return []

        try:
            import json as _json
            return _json.loads(chars_raw)
        except ValueError as err:
            self.display.print(f'Invalid JSON: {err}')
            return None

    def _print_simulation_result(self, response, iterations):
        data = response.json().get('data', {})
        self.display.print('=== Simulation result ===')
        self.display.print(f'  Monster: {data.get("monster", {}).get("name", "?")} (lvl {data.get("monster", {}).get("level", "?")})')
        self.display.print(f'  Win rate: {data.get("win_rate", "?")}%')
        self.display.print(f'  Average turns: {data.get("average_turns", "?")}')
        self.display.print(f'  Total simulations: {iterations}')


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

    def __init__(self, name, parent=None, display=None) -> None:
        super().__init__()

        self.name = name
        self.parent = parent
        self.display = display or ConsoleDisplay()
        self.base_character_action_url = f'/my/{self.name}/action'
        self.refresh()

    def _get_with_reauth(self, url, data=None):
        """Run an authenticated GET, automatically offering a re-login if
        the token is rejected. Mirrors GameClient's wrapper but also
        propagates the new token to the parent client so account-level
        calls don't have to re-auth again."""

        self.display.show_loading()
        response = self._get(url=url, data=data)
        self.display.hide_loading()

        if self.is_invalid_token_error(response) and self.ensure_valid_token(probe_response=response):
            self._propagate_token_to_parent()
            self.display.show_loading()
            response = self._get(url=url, data=data)
            self.display.hide_loading()

        return response

    def _post_with_reauth(self, url, data=None):
        """Run an authenticated POST with the same re-login behaviour as
        _get_with_reauth."""

        self.display.show_loading()
        response = self._post(url=url, data=data)
        self.display.hide_loading()

        if self.is_invalid_token_error(response) and self.ensure_valid_token(probe_response=response):
            self._propagate_token_to_parent()
            self.display.show_loading()
            response = self._post(url=url, data=data)
            self.display.hide_loading()

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
                self.display.print(error_block.get('message', 'Unknown error.'))
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
                log = logs[0]
                self.display.show_action_log(log.get('description', ''))
                self.display.show_action_details(log)
            else:
                self.display.print('No recent actions.')
        elif error_block := last_action_data.json().get('error'):
            self.display.print(f'Can\'t get last action. {error_block.get("message", "Unknown error.")}.')

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
            self.display.show_action_in_progress(reason, total_seconds)

            for i in range(total_seconds, 0, -1):
                self.display.show_action_countdown(i)
                sleep(1)

            self.display.clear_action_countdown()
            self.display.show_action_details(data)
            self._get_last_action()
            result = data
        elif error_block := action_request.json().get('error'):
            self.display.show_action_error(error_block.get("message", "Unknown error."))

        return result

    def move(self, x=0, y=0, map_id=None):
        if map_id is None and self.x == x and self.y == y:
            return True
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
        if self.hp < self.max_hp / 2:
            self.display.print(f'HP too low ({self.hp}/{self.max_hp}). Resting...')
            self.rest()

        self._deposit_non_equip_if_full()

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
            self.display.print(f'Equipping {best_code} (+{best_value} {skill_code})...')
            self.equip(best_code, 'weapon')

    def gathering(self):
        skill_code = self._get_gathering_skill_at_location()
        if skill_code:
            self._equip_best_gathering_weapon(skill_code)

        self._deposit_non_equip_if_full()
        return self._do_action('gathering')

    def _deposit_non_equip_if_full(self):
        inventory = getattr(self, 'inventory', None) or []
        max_items = getattr(self, 'inventory_max_items', 100)
        total_quantity = sum(s.get('quantity', 0) for s in inventory if s.get('code'))
        fill_ratio = total_quantity / max_items if max_items else 0

        if fill_ratio > 0.9:
            unique_codes = set()
            for entry in inventory:
                code = entry.get('code')
                if code:
                    unique_codes.add(code)

            equip_types = set(ItemTypesEnum.EQUIP_TYPES)
            codes_to_deposit = []

            for code in unique_codes:
                response = self._get(url=f'/items/{code}')
                if response.status_code == 200:
                    item_type = response.json().get('data', {}).get('type')
                    if item_type not in equip_types:
                        codes_to_deposit.append(code)

            if codes_to_deposit:
                origin_x, origin_y = self.x, self.y
                at_bank = False

                location = self._get(url=f'/maps/{self.layer}/{self.x}/{self.y}')
                if location.status_code == 200:
                    content_type = (location.json().get('data', {}).get('content') or {}).get('type')
                    at_bank = content_type == 'bank'

                if not at_bank:
                    banks = self._get(url='/maps', data={'content_type': 'bank', 'layer': self.layer, 'size': 100})
                    if banks.status_code == 200:
                        bank_list = banks.json().get('data', [])
                        if bank_list:
                            bank = bank_list[0]
                            self.display.print(f'Moving to bank ({bank["x"]}, {bank["y"]}) to deposit...')
                            self.move(bank['x'], bank['y'])

                inv_by_code = {}
                for entry in (getattr(self, 'inventory', None) or []):
                    c = entry.get('code')
                    if c:
                        inv_by_code[c] = inv_by_code.get(c, 0) + entry.get('quantity', 0)

                self.display.print(f'Inventory {total_quantity}/{max_items} (>90%). Depositing...')
                deposit_list = [(code, inv_by_code.get(code, 0)) for code in codes_to_deposit if inv_by_code.get(code, 0) > 0]
                if deposit_list:
                    self.deposit_items(deposit_list)

                if not at_bank and (self.x != origin_x or self.y != origin_y):
                    self.display.print('Moving back to original location...')
                    self.move(origin_x, origin_y)

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
        return self._do_action('bank/deposit/item', [{'code': code, 'quantity': quantity}])

    def deposit_items(self, items):
        max_batch = 20
        for index in range(0, len(items), max_batch):
            batch = items[index:index + max_batch]
            payload = [{'code': code, 'quantity': quantity} for code, quantity in batch]
            self._do_action('bank/deposit/item', payload)

    def deposit_gold(self, quantity=0):
        return self._do_action('bank/deposit/gold', {'quantity': quantity})

    def withdraw_item(self, code='', quantity=1):
        return self._do_action('bank/withdraw/item', [{'code': code, 'quantity': quantity}])

    def withdraw_items(self, items):
        max_batch = 20
        for index in range(0, len(items), max_batch):
            batch = items[index:index + max_batch]
            payload = [{'code': code, 'quantity': quantity} for code, quantity in batch]
            self._do_action('bank/withdraw/item', payload)

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
