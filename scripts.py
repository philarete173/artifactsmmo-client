from base import BaseClient


class ScenariosStorage(BaseClient):
    """Class for storing scenarios for character automation."""

    GATHER_RESOURCES_CATEGORY = 'Gather resources'
    CRAFT_RESOURCES_CATEGORY = 'Craft resources'
    CRAFT_ITEMS_CATEGORY = 'Craft items'

    def __init__(self, character):
        super().__init__()

        self.character = character

        self.scenarios_category_map = {
            self.GATHER_RESOURCES_CATEGORY: [
                self.gather_copper_ore,
                self.gather_iron_ore,
                self.gather_coal,
                self.gather_gold_ore,
                self.gather_ash_wood,
                self.gather_spruce_wood,
                self.gather_birch_wood,
                self.gather_resource_from_monsters,
            ],
            self.CRAFT_RESOURCES_CATEGORY: [
                self.craft_copper,
                self.craft_iron,
                self.craft_steel,
                self.craft_gold,
                self.craft_ash_planks,
                self.craft_spruce_planks,
                self.craft_hardwood_planks,
            ],
            self.CRAFT_ITEMS_CATEGORY: [
                self.craft_wooden_staff,
                self.craft_wooden_shield,
                self.craft_copper_dagger,
                self.craft_copper_helmet,
                self.craft_copper_boots,
                self.craft_copper_ring,
                self.craft_life_amulet,
                self.craft_copper_armor,
                self.craft_copper_legs_armor,
                self.craft_iron_ring,
            ],
        }

    def _sell_item(self, item_name='', quantity=1):
        self.character.move(5, 1)
        self.character.sell_item(item_name, quantity)

    def _craft_weapon(self, item_code='', quantity=1):
        self.character.move(2, 1)
        self.character.crafting(item_code, quantity)

    def _craft_gear(self, item_code='', quantity=1):
        self.character.move(3, 1)
        self.character.crafting(item_code, quantity)

    def _craft_jewelry(self, item_code='', quantity=1):
        self.character.move(1, 3)
        self.character.crafting(item_code, quantity)

    def _craft_metal(self, item_code='', quantity=1):
        self.character.move(1, 5)
        self.character.crafting(item_code, quantity)

    def _craft_planks(self, item_code='', quantity=1):
        self.character.move(-2, -3)
        self.character.crafting(item_code, quantity)

    def gather_copper_ore(self, quantity=1):
        self.character.move(2, 0)
        for _ in range(quantity):
            self.character.gathering()

    def gather_iron_ore(self, quantity=1):
        self.character.move(1, 7)
        for _ in range(quantity):
            self.character.gathering()

    def gather_coal(self, quantity=1):
        self.character.move(1, 6)
        for _ in range(quantity):
            self.character.gathering()

    def gather_gold_ore(self, quantity=1):
        self.character.move(10, -4)
        for _ in range(quantity):
            self.character.gathering()

    def gather_ash_wood(self, quantity=1):
        self.character.move(6, 1)
        for _ in range(quantity):
            self.character.gathering()

    def gather_spruce_wood(self, quantity=1):
        self.character.move(2, 6)
        for _ in range(quantity):
            self.character.gathering()

    def gather_birch_wood(self, quantity=1):
        self.character.move(2, 6)
        for _ in range(quantity):
            self.character.gathering()

    def gather_resource_from_monsters(self, item_code='', quantity=1):
        monster_data = self._get(
            url='/monsters',
            data={
                'drop': item_code,
                'size': 1,
            }
        )

        if monster_data.status_code == 200:
            monster_code = monster_data.json()['data'][0]['code']

            location_data = self._get(
                url='/maps',
                data={
                    'content_code': monster_code,
                    'size': 1,
                }
            )

            if location_data.status_code == 200:
                location = location_data.json()['data'][0]

                self.character.move(location['x'], location['y'])

                while next(
                        filter(
                            lambda item: item['code'] == item_code,
                            self.character.inventory),
                        {},
                ).get('quantity', 0) < quantity:
                    self.character.fight()

            elif error_block := location_data.json().get('error'):
                print(f'Can\'t get location data. {error_block["message"]}.')

        elif error_block := monster_data.json().get('error'):
            print(f'Can\'t get monster data. {error_block["message"]}.')

    def craft_copper(self, quantity=1):
        self.gather_copper_ore(6 * quantity)

        self._craft_metal('copper', quantity)

    def craft_iron(self, quantity=1):
        self.gather_iron_ore(6 * quantity)

        self._craft_metal('iron', quantity)

    def craft_steel(self, quantity=1):
        self.gather_iron_ore(2 * quantity)
        self.gather_coal(4 * quantity)

        self._craft_metal('steel', quantity)

    def craft_gold(self, quantity=1):
        self.gather_gold_ore(6 * quantity)

        self._craft_metal('gold', quantity)

    def craft_ash_planks(self, quantity=1):
        self.gather_ash_wood(6 * quantity)

        self._craft_planks('ash_plank', quantity)

    def craft_spruce_planks(self, quantity=1):
        self.gather_spruce_wood(6 * quantity)

        self._craft_planks('spruce_plank', quantity)

    def craft_hardwood_planks(self, quantity=1):
        self.gather_ash_wood(2 * quantity)
        self.gather_birch_wood(4 * quantity)

        self._craft_planks('hardwood_plank', quantity)

    def craft_wooden_staff(self, quantity=1, sell=False):
        self.craft_ash_planks(3 * quantity)

        self.gather_ash_wood(4 * quantity)

        self._craft_weapon('wooden_stick', quantity)
        self._craft_weapon('wooden_staff', quantity)

        if sell:
            self._sell_item('wooden_staff', quantity)

    def craft_wooden_shield(self, quantity=1, sell=False):
        self.craft_ash_planks(3 * quantity)

        self._craft_gear('wooden_shield', quantity)

        if sell:
            self._sell_item('wooden_shield', quantity)

    def craft_copper_dagger(self, quantity=1, sell=False):
        self.craft_copper(3 * quantity)

        self._craft_weapon('copper_dagger', quantity)

        if sell:
            self._sell_item('copper_dagger', quantity)

    def craft_copper_helmet(self, quantity=1, sell=False):
        self.craft_copper(3 * quantity)

        self._craft_gear('copper_helmet', quantity)

        if sell:
            self._sell_item('copper_helmet', quantity)

    def craft_copper_boots(self, quantity=1, sell=False):
        self.craft_copper(3 * quantity)

        self._craft_gear('copper_boots', quantity)

        if sell:
            self._sell_item('copper_boots', quantity)

    def craft_copper_ring(self, quantity=1, sell=False):
        self.craft_copper(4 * quantity)

        self._craft_jewelry('copper_ring', quantity)

        if sell:
            self._sell_item('copper_ring', quantity)

    def craft_copper_armor(self, quantity=1, sell=False):
        self.craft_copper(5 * quantity)

        self._craft_gear('copper_armor', quantity)

        if sell:
            self._sell_item('copper_armor', quantity)

    def craft_copper_legs_armor(self, quantity=1, sell=False):
        self.craft_copper(4 * quantity)

        self._craft_gear('copper_legs_armor', quantity)

        if sell:
            self._sell_item('copper_legs_armor', quantity)

    def craft_life_amulet(self, quantity=1, sell=False):
        self.gather_resource_from_monsters('blue_slimeball', quantity)
        self.gather_resource_from_monsters('red_slimeball', quantity)
        self.gather_resource_from_monsters('cowhide', 2 * quantity)

        self._craft_jewelry('life_amulet', quantity)

        if sell:
            self._sell_item('life_amulet', quantity)

    def craft_iron_dagger(self, quantity=1, sell=False):
        self.craft_copper(2 * quantity)
        self.craft_iron(6 * quantity)

        self._craft_weapon('iron_dagger', quantity)

        if sell:
            self._sell_item('iron_dagger', quantity)

    def craft_iron_sword(self, quantity=1, sell=False):
        self.craft_iron(8 * quantity)

        self._craft_weapon('iron_sword', quantity)

        if sell:
            self._sell_item('iron_sword', quantity)

    def craft_greater_wooden_staff(self, quantity=1, sell=False):
        self.craft_ash_planks(3 * quantity)
        self.craft_spruce_planks(4 * quantity)

        self._craft_weapon('greater_wooden_staff', quantity)

        if sell:
            self._sell_item('greater_wooden_staff', quantity)

    def craft_iron_boots(self, quantity=1, sell=False):
        self.craft_iron(6 * quantity)

        self._craft_gear('iron_boots', quantity)

        if sell:
            self._sell_item('iron_boots', quantity)

    def craft_iron_ring(self, quantity=1, sell=False):
        self.craft_iron(6 * quantity)

        self._craft_jewelry('iron_ring', quantity)

        if sell:
            self._sell_item('iron_ring', quantity)

