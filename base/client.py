import random

from base.base import BaseGameClient
from base.character import Character
from base.enums import ActionTypeEnum, CharacterSexEnum


class GameClient(BaseGameClient):
    """Shared API client for ArtifactsMMO.

    Provides all API data-fetching methods, account management, and the
    action routing maps used by both console and GUI front-ends.
    """

    def __init__(self, display=None):
        super().__init__()

        self.display = display
        self.character = None
        self.characters = []
        self.scenarios_storage = None

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

    # ── Auth wrappers ───────────────────────────────────────────

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

    def _propagate_token_to_characters(self):
        """Copy the current auth token to all active Character instances."""

        for char in self.characters:
            if hasattr(char, 'base_headers'):
                char.base_headers['Authorization'] = self.base_headers.get('Authorization', '')

    # ── Character lifecycle ─────────────────────────────────────

    def _build_character(self, name):
        """Create a Character object. Override in subclasses for UI-specific output."""
        character = Character(name, parent=self, display=self.display)
        return character

    def _choose_character(self):
        """Select a character and set up scenarios storage."""
        self.select_character()
        if self.character is not None:
            from scripts import ScenariosStorage
            self.scenarios_storage = ScenariosStorage(self.character)

    def select_character(self):
        """Fetch account characters, auto-create if needed, let user choose."""
        ...

    # ── Account management ──────────────────────────────────────

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

    def get_account_details(self):
        """Return account details dict, or None on failure."""

        response = self._get_with_reauth(url='/my/details')
        if response.status_code != 200:
            self.display.print('Failed to get account details.')
            return None

        data = response.json().get('data', {})
        return data

    def login_with_password(self):
        """Force a fresh login (replace the current token with one obtained
        from username/password). Useful when the saved token is expired or
        has been reset."""

        if self.request_new_token():
            self._propagate_token_to_characters()

    # ── Season / server info ────────────────────────────────────

    def show_current_season(self):
        """Show the current season info at startup. Also acts as a
        network availability check (exits if the server is unreachable)."""

        response = self._get()

        if response.status_code != 200:
            if self.display:
                self.display.print('Can\'t reach the server. Please try again later.')
            return

        data = response.json().get('data', {})
        if self.display:
            self.display.print(f'Game version: {data.get("version", "?")}.')

    # ── Menu dispatch stubs (overridden by subclasses) ──────────

    def character_movement(self):
        ...

    def character_transition(self):
        ...

    def character_fight(self):
        ...

    def character_gathering(self):
        ...

    def character_crafting(self):
        ...

    def character_recycling(self):
        ...

    def character_equip(self):
        ...

    def character_unequip(self):
        ...

    def character_use_item(self):
        ...

    def character_delete_item(self):
        ...

    def character_rest(self):
        ...

    def character_change_skin(self):
        ...

    def character_get_new_task(self):
        ...

    def character_complete_task(self):
        ...

    def character_cancel_task(self):
        ...

    def character_exchange_task_coins(self):
        ...

    def character_trade_task(self):
        ...

    def character_claim_pending_item(self):
        ...

    def character_npc_buy_item(self):
        ...

    def character_npc_sell_item(self):
        ...

    def character_buy_bank_expansion(self):
        ...

    def character_deposit_item_to_bank(self):
        ...

    def character_deposit_gold_to_bank(self):
        ...

    def character_withdraw_item_from_bank(self):
        ...

    def character_withdraw_gold_from_bank(self):
        ...

    def character_give_gold(self):
        ...

    def character_give_item(self):
        ...

    def character_ge_buy_item(self):
        ...

    def character_ge_cancel_order(self):
        ...

    def character_ge_create_buy_order(self):
        ...

    def character_ge_create_sell_order(self):
        ...

    def character_ge_fill_order(self):
        ...

    def show_bank(self):
        ...

    def show_pending_items(self):
        ...

    def show_ge_orders(self):
        ...

    def use_scenario(self):
        ...

    def _show_account_details(self):
        ...

    def change_password(self):
        ...

    def _prompt_and_create_character(self):
        ...

    # ── API data fetchers ───────────────────────────────────────

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
