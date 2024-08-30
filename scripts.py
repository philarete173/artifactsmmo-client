from base import BaseClient
from enums import MapTypesEnum, TaskTypeEnum


class ScenariosStorage(BaseClient):
    """Class for storing scenarios for character automation."""

    GATHER_RESOURCES_CATEGORY = 'Gather resources'
    CRAFT_RESOURCES_CATEGORY = 'Craft resources'
    CRAFT_EQUIPMENT_CATEGORY = 'Craft equipment'
    CRAFT_CONSUMABLES = 'Craft consumables'
    OTHER_CATEGORY = 'Other scenarios'

    def __init__(self, character):
        super().__init__()

        self.character = character

        self.scenarios_category_map = {
            self.GATHER_RESOURCES_CATEGORY: self._get_gather_resources_category_scenarios,
            self.CRAFT_RESOURCES_CATEGORY: self._get_craft_resources_category_scenarios,
            self.CRAFT_EQUIPMENT_CATEGORY: self._get_craft_equipment_category_scenarios,
            self.CRAFT_CONSUMABLES: self._get_craft_consumables_scenarios,
            self.OTHER_CATEGORY: self._get_other_scenarios,
        }

    def _get_gather_resources_category_scenarios(self):
        scenarios_list = [
            self.gather_copper_ore,
            self.gather_ash_wood,
        ]

        if self.character.mining_level >= 10:
            scenarios_list.append(self.gather_iron_ore)

        if self.character.mining_level >= 20:
            scenarios_list.extend([
                self.gather_iron_ore,
                self.gather_coal,
            ])

        if self.character.mining_level >= 30:
            scenarios_list.append(self.gather_gold_ore)

        if self.character.woodcutting_level >= 10:
            scenarios_list.append(self.gather_spruce_wood)

        if self.character.woodcutting_level >= 20:
            scenarios_list.append(self.gather_birch_wood)

        if self.character.woodcutting_level >= 30:
            scenarios_list.append(self.gather_dead_wood)

        scenarios_list.extend([
            self.gather_resource_from_location,
            self.gather_resource_from_monsters,
        ])

        return scenarios_list

    def _get_craft_resources_category_scenarios(self):
        scenarios_list = [
            self.craft_copper,
            self.craft_ash_planks,
        ]

        if self.character.mining_level >= 10:
            scenarios_list.append(self.craft_iron)

        if self.character.mining_level >= 20:
            scenarios_list.append(self.craft_steel)

        if self.character.mining_level >= 30:
            scenarios_list.append(self.craft_gold)

        if self.character.woodcutting_level >= 10:
            scenarios_list.append(self.craft_spruce_planks)

        if self.character.woodcutting_level >= 20:
            scenarios_list.append(self.craft_hardwood_planks)

        if self.character.woodcutting_level >= 30:
            scenarios_list.append(self.craft_dead_wood_planks)

        return scenarios_list

    def _get_craft_equipment_category_scenarios(self):
        scenarios_list = [
            self.craft_wooden_staff,
            self.craft_wooden_shield,
            self.craft_copper_dagger,
            self.craft_copper_helmet,
            self.craft_copper_boots,
            self.craft_copper_ring,
        ]

        if self.character.weaponcrafting_level >= 5:
            scenarios_list.extend([

            ])

        if self.character.weaponcrafting_level >= 10:
            scenarios_list.extend([
                self.craft_iron_dagger,
                self.craft_iron_sword,
                self.craft_greater_wooden_staff,
                self.craft_fire_bow,
            ])

        if self.character.weaponcrafting_level >= 15:
            scenarios_list.extend([
                self.craft_multislimes_sword,
                self.craft_mushstaff,
                self.craft_mushmush_bow,
            ])

        if self.character.weaponcrafting_level >= 20:
            scenarios_list.extend([

            ])

        if self.character.weaponcrafting_level >= 25:
            scenarios_list.extend([

            ])

        if self.character.weaponcrafting_level >= 30:
            scenarios_list.extend([

            ])

        if self.character.gearcrafting_level >= 5:
            scenarios_list.extend([
                self.craft_copper_armor,
                self.craft_copper_legs_armor,
                self.craft_feather_coat,
            ])

        if self.character.gearcrafting_level >= 10:
            scenarios_list.extend([
                self.craft_iron_boots,
                self.craft_adventurer_helmet,
                self.craft_adventurer_pants,
                self.craft_adventurer_vest,
                self.craft_slime_shield,
            ])

        if self.character.gearcrafting_level >= 15:
            scenarios_list.extend([
                self.craft_adventurer_boots,
            ])

        if self.character.gearcrafting_level >= 20:
            scenarios_list.extend([

            ])

        if self.character.gearcrafting_level >= 25:
            scenarios_list.extend([

            ])

        if self.character.gearcrafting_level >= 30:
            scenarios_list.extend([

            ])

        if self.character.jewelrycrafting_level >= 5:
            scenarios_list.extend([
                self.craft_life_amulet,
            ])

        if self.character.jewelrycrafting_level >= 10:
            scenarios_list.extend([
                self.craft_iron_ring,
                self.craft_fire_and_earth_amulet,
                self.craft_air_and_water_amulet,
            ])

        if self.character.jewelrycrafting_level >= 15:
            scenarios_list.extend([
                self.craft_air_ring,
                self.craft_earth_ring,
                self.craft_fire_ring,
                self.craft_water_ring,
                self.craft_life_ring,
            ])

        if self.character.jewelrycrafting_level >= 20:
            scenarios_list.extend([

            ])

        if self.character.jewelrycrafting_level >= 25:
            scenarios_list.extend([

            ])

        if self.character.jewelrycrafting_level >= 30:
            scenarios_list.extend([

            ])

        return scenarios_list

    def _get_craft_consumables_scenarios(self):
        scenarios_list = [
            self.craft_cooked_gudgeon,
            self.craft_cooked_chicken,
        ]

        if self.character.cooking_level >= 5:
            scenarios_list.extend([
                self.craft_cooked_beef,
            ])

        if self.character.cooking_level >= 10:
            scenarios_list.extend([
                self.craft_cheese,
                self.craft_fried_eggs,
                self.craft_mushroom_soup,
                self.craft_beef_stew,
            ])

            if self.character.fishing_level >= 10:
                scenarios_list.extend([
                    self.craft_cooked_shrimp,
                ])

        if self.character.cooking_level >= 15:
            scenarios_list.extend([
                self.craft_cooked_wolf_meat,
            ])

        if self.character.cooking_level >= 20 and self.character.fishing_level >= 20:
            scenarios_list.extend([
                self.craft_cooked_trout,
            ])

        if self.character.cooking_level >= 30 and self.character.fishing_level >= 30:
            scenarios_list.extend([
                self.craft_cooked_bass,
            ])

        return scenarios_list

    def _get_other_scenarios(self):
        return [
            self.do_quest_from_tasks_master,
        ]

    def _get_location_for_content(self, content_code=''):
        location_data = self._get(
            url='/maps',
            data={
                'content_code': content_code,
                'size': 1,
            }
        )

        if location_data.status_code == 200:
            location = location_data.json()['data'][0]

            return location['x'], location['y']

        elif error_block := location_data.json().get('error'):
            print(f'Can\'t get location data. {error_block["message"]}.')

    def _gather_resource(self, type_from='', item_code='', quantity=1):
        item_data = self._get(
            url=f'/{type_from}',
            data={
                'drop': item_code,
                'size': 1,
            }
        )

        if item_data.status_code == 200:
            content_code = item_data.json()['data'][0]['code']

            if location := self._get_location_for_content(content_code):

                self.character.move(*location)

                while next(
                    filter(
                        lambda item: item['code'] == item_code,
                        self.character.inventory),
                    {},
                ).get('quantity', 0) < quantity:
                    if type_from == 'resources':
                        self.character.gathering()
                    elif type_from == 'monsters':
                        if (self.character.x, self.character.y) != location:
                            self.character.move(*location)

                        self.character.fight()

        elif error_block := item_data.json().get('error'):
            print(f'Can\'t get item data. {error_block["message"]}.')

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

    def _craft_food(self, item_code='', quantity=1):
        self.character.move(1, 1)
        self.character.crafting(item_code, quantity)

    def gather_resource_from_location(self, item_code='', quantity=1):
        self._gather_resource(type_from='resources', item_code=item_code, quantity=quantity)

    def gather_resource_from_monsters(self, item_code='', quantity=1):
        self._gather_resource(type_from='monsters', item_code=item_code, quantity=quantity)

    def do_quest_from_tasks_master(self, quantity=1):
        tasks_master_location_data = self._get(
            url='/maps',
            data={
                'content_type': MapTypesEnum.TASKS_MASTER.value,
                'size': 1,
            }
        )

        if tasks_master_location_data.status_code == 200:
            tasks_master_location = tasks_master_location_data.json()['data'][0]

            for _ in range(quantity):
                if not self.character.task:
                    self.character.move(tasks_master_location['x'], tasks_master_location['y'])
                    self.character.get_task()

                if self.character.task_type == TaskTypeEnum.MONSTERS.value:
                    if monster_location := self._get_location_for_content(self.character.task):
                        while self.character.task_progress < self.character.task_total:
                            if (self.character.x, self.character.y) != monster_location:
                                self.character.move(*monster_location)

                            self.character.fight()

                        self.character.move(tasks_master_location['x'], tasks_master_location['y'])
                        self.character.complete_task()

                else:
                    print('Can\'t process this type of task.')
                    break

        else:
            print('Can\'t locate Tasks Master.')

    def gather_copper_ore(self, quantity=1):
        self.gather_resource_from_location('copper_ore', quantity)

    def gather_iron_ore(self, quantity=1):
        self.gather_resource_from_location('iron_ore', quantity)

    def gather_coal(self, quantity=1):
        self.gather_resource_from_location('coal', quantity)

    def gather_gold_ore(self, quantity=1):
        self.gather_resource_from_location('gold_ore', quantity)

    def gather_ash_wood(self, quantity=1):
        self.gather_resource_from_location('ash_wood', quantity)

    def gather_spruce_wood(self, quantity=1):
        self.gather_resource_from_location('spruce_wood', quantity)

    def gather_birch_wood(self, quantity=1):
        self.gather_resource_from_location('birch_wood', quantity)

    def gather_dead_wood(self, quantity=1):
        self.gather_resource_from_location('dead_wood', quantity)

    def craft_copper(self, quantity=1):
        self.gather_copper_ore(8 * quantity)

        self._craft_metal('copper', quantity)

    def craft_iron(self, quantity=1):
        self.gather_iron_ore(8 * quantity)

        self._craft_metal('iron', quantity)

    def craft_steel(self, quantity=1):
        self.gather_iron_ore(3 * quantity)
        self.gather_coal(5 * quantity)

        self._craft_metal('steel', quantity)

    def craft_gold(self, quantity=1):
        self.gather_gold_ore(8 * quantity)

        self._craft_metal('gold', quantity)

    def craft_ash_planks(self, quantity=1):
        self.gather_ash_wood(8 * quantity)

        self._craft_planks('ash_plank', quantity)

    def craft_spruce_planks(self, quantity=1):
        self.gather_spruce_wood(8 * quantity)

        self._craft_planks('spruce_plank', quantity)

    def craft_hardwood_planks(self, quantity=1):
        self.gather_ash_wood(3 * quantity)
        self.gather_birch_wood(5 * quantity)

        self._craft_planks('hardwood_plank', quantity)

    def craft_dead_wood_planks(self, quantity=1):
        self.gather_dead_wood(8 * quantity)

        self._craft_planks('dead_wood_plank', quantity)

    def craft_wooden_staff(self, quantity=1, sell=False):
        self.craft_ash_planks(3 * quantity)

        self.gather_ash_wood(4 * quantity)

        self._craft_weapon('wooden_stick', quantity)
        self._craft_weapon('wooden_staff', quantity)

        if sell:
            self._sell_item('wooden_staff', quantity)

    def craft_wooden_shield(self, quantity=1, sell=False):
        self.craft_ash_planks(6 * quantity)

        self._craft_gear('wooden_shield', quantity)

        if sell:
            self._sell_item('wooden_shield', quantity)

    def craft_copper_dagger(self, quantity=1, sell=False):
        self.craft_copper(6 * quantity)

        self._craft_weapon('copper_dagger', quantity)

        if sell:
            self._sell_item('copper_dagger', quantity)

    def craft_copper_helmet(self, quantity=1, sell=False):
        self.craft_copper(6 * quantity)

        self._craft_gear('copper_helmet', quantity)

        if sell:
            self._sell_item('copper_helmet', quantity)

    def craft_copper_boots(self, quantity=1, sell=False):
        self.craft_copper(8 * quantity)

        self._craft_gear('copper_boots', quantity)

        if sell:
            self._sell_item('copper_boots', quantity)

    def craft_copper_ring(self, quantity=1, sell=False):
        self.craft_copper(6 * quantity)

        self._craft_jewelry('copper_ring', quantity)

        if sell:
            self._sell_item('copper_ring', quantity)

    def craft_copper_armor(self, quantity=1, sell=False):
        self.craft_copper(5 * quantity)
        self.gather_resource_from_monsters('feather', 2 * quantity)

        self._craft_gear('copper_armor', quantity)

        if sell:
            self._sell_item('copper_armor', quantity)

    def craft_copper_legs_armor(self, quantity=1, sell=False):
        self.craft_copper(6 * quantity)

        self._craft_gear('copper_legs_armor', quantity)

        if sell:
            self._sell_item('copper_legs_armor', quantity)

    def craft_feather_coat(self, quantity=1, sell=False):
        self.gather_resource_from_monsters('feather', 6 * quantity)

        self._craft_gear('feather_coat', quantity)

        if sell:
            self._sell_item('feather_coat', quantity)

    def craft_life_amulet(self, quantity=1, sell=False):
        self.gather_resource_from_monsters('blue_slimeball', 2 * quantity)
        self.gather_resource_from_monsters('red_slimeball', 2 * quantity)
        self.gather_resource_from_monsters('feather', 4 * quantity)

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

    def craft_fire_bow(self, quantity=1, sell=False):
        self.craft_spruce_planks(4 * quantity)
        self.gather_resource_from_monsters('red_slimeball', 2 * quantity)

        self._craft_weapon('fire_bow', quantity)

        if sell:
            self._sell_item('fire_bow', quantity)

    def craft_iron_boots(self, quantity=1, sell=False):
        self.craft_iron(5 * quantity)
        self.gather_resource_from_monsters('feather', 3 * quantity)

        self._craft_gear('iron_boots', quantity)

        if sell:
            self._sell_item('iron_boots', quantity)

    def craft_iron_ring(self, quantity=1, sell=False):
        self.craft_iron(6 * quantity)

        self._craft_jewelry('iron_ring', quantity)

        if sell:
            self._sell_item('iron_ring', quantity)

    def craft_fire_and_earth_amulet(self, quantity=1, sell=False):
        self.craft_copper(3 * quantity)
        self.craft_iron(4 * quantity)
        self.gather_resource_from_monsters('red_slimeball', 3 * quantity)
        self.gather_resource_from_monsters('yellow_slimeball', 3 * quantity)

        self._craft_jewelry('fire_and_earth_amulet', quantity)

        if sell:
            self._sell_item('fire_and_earth_amulet', quantity)

    def craft_air_and_water_amulet(self, quantity=1, sell=False):
        self.craft_copper(2 * quantity)
        self.craft_iron(6 * quantity)
        self.gather_resource_from_monsters('green_slimeball', 3 * quantity)
        self.gather_resource_from_monsters('blue_slimeball', 3 * quantity)

        self._craft_jewelry('air_and_water_amulet', quantity)

        if sell:
            self._sell_item('air_and_water_amulet', quantity)

    def craft_slime_shield(self, quantity=1, sell=False):
        self.craft_spruce_planks(6 * quantity)
        self.gather_resource_from_monsters('green_slimeball', 3 * quantity)
        self.gather_resource_from_monsters('blue_slimeball', 3 * quantity)
        self.gather_resource_from_monsters('red_slimeball', 3 * quantity)
        self.gather_resource_from_monsters('yellow_slimeball', 3 * quantity)

        self._craft_gear('slime_shield', quantity)

        if sell:
            self._sell_item('slime_shield', quantity)

    def craft_adventurer_helmet(self, quantity=1, sell=False):
        self.craft_spruce_planks(3 * quantity)
        self.gather_resource_from_monsters('feather', 4 * quantity)
        self.gather_resource_from_monsters('cowhide', 3 * quantity)
        self.gather_resource_from_monsters('mushroom', 4 * quantity)

        self._craft_gear('adventurer_helmet', quantity)

        if sell:
            self._sell_item('adventurer_helmet', quantity)

    def craft_adventurer_pants(self, quantity=1, sell=False):
        self.craft_iron(2 * quantity)
        self.gather_resource_from_monsters('cowhide', 8 * quantity)
        self.gather_resource_from_monsters('mushroom', 2 * quantity)

        self._craft_gear('adventurer_pants', quantity)

        if sell:
            self._sell_item('adventurer_pants', quantity)

    def craft_adventurer_vest(self, quantity=1, sell=False):
        self.craft_spruce_planks(4 * quantity)
        self.gather_resource_from_monsters('feather', 2 * quantity)
        self.gather_resource_from_monsters('cowhide', 6 * quantity)
        self.gather_resource_from_monsters('yellow_slimeball', 4 * quantity)

        self._craft_gear('adventurer_vest', quantity)

        if sell:
            self._sell_item('adventurer_vest', quantity)

    def craft_adventurer_boots(self, quantity=1, sell=False):
        self.craft_spruce_planks(2 * quantity)
        self.gather_resource_from_monsters('cowhide', 6 * quantity)
        self.gather_resource_from_monsters('wolf_hair', 4 * quantity)
        self.gather_resource_from_monsters('mushroom', 3 * quantity)
        self.craft_spruce_planks(2 * quantity)

        self._craft_gear('adventurer_boots', quantity)

        if sell:
            self._sell_item('adventurer_boots', quantity)

    def craft_multislimes_sword(self, quantity=1, sell=False):
        self.craft_iron_sword(quantity)
        self.gather_resource_from_monsters('red_slimeball', 3 * quantity)
        self.gather_resource_from_monsters('green_slimeball', 3 * quantity)
        self.gather_resource_from_monsters('blue_slimeball', 3 * quantity)
        self.gather_resource_from_monsters('yellow_slimeball', 3 * quantity)

        self._craft_weapon('multislimes_sword', quantity)

        if sell:
            self._sell_item('multislimes_sword', quantity)

    def craft_mushstaff(self, quantity=1, sell=False):
        self.craft_spruce_planks(5 * quantity)
        self.craft_iron(quantity)
        self.gather_resource_from_monsters('mushroom', 5 * quantity)
        self.gather_resource_from_monsters('flying_wing', 2 * quantity)

        self._craft_weapon('mushstaff', quantity)

        if sell:
            self._sell_item('mushstaff', quantity)

    def craft_mushmush_bow(self, quantity=1, sell=False):
        self.craft_spruce_planks(6 * quantity)
        self.gather_resource_from_monsters('wolf_hair', 3 * quantity)
        self.gather_resource_from_monsters('mushroom', 4 * quantity)

        self._craft_weapon('mushmush_bow', quantity)

        if sell:
            self._sell_item('mushmush_bow', quantity)

    def craft_air_ring(self, quantity=1, sell=False):
        self.craft_iron_ring(quantity)
        self.gather_resource_from_monsters('green_slimeball', 4 * quantity)
        self.gather_resource_from_monsters('flying_wing', 2 * quantity)

        self._craft_jewelry('air_ring', quantity)

        if sell:
            self._sell_item('air_ring', quantity)

    def craft_earth_ring(self, quantity=1, sell=False):
        self.craft_iron_ring(quantity)
        self.gather_resource_from_monsters('yellow_slimeball', 4 * quantity)
        self.gather_resource_from_monsters('mushroom', 2 * quantity)

        self._craft_jewelry('earth_ring', quantity)

        if sell:
            self._sell_item('earth_ring', quantity)

    def craft_fire_ring(self, quantity=1, sell=False):
        self.craft_iron_ring(quantity)
        self.gather_resource_from_monsters('red_slimeball', 4 * quantity)
        self.gather_resource_from_monsters('mushroom', 2 * quantity)

        self._craft_jewelry('fire_ring', quantity)

        if sell:
            self._sell_item('fire_ring', quantity)

    def craft_water_ring(self, quantity=1, sell=False):
        self.craft_iron_ring(quantity)
        self.gather_resource_from_monsters('blue_slimeball', 4 * quantity)
        self.gather_resource_from_monsters('flying_wing', 2 * quantity)

        self._craft_jewelry('water_ring', quantity)

        if sell:
            self._sell_item('water_ring', quantity)

    def craft_life_ring(self, quantity=1, sell=False):
        self.craft_iron_ring(quantity)
        self.gather_resource_from_monsters('feather', 2 * quantity)
        self.gather_resource_from_monsters('mushroom', 2 * quantity)

        self._craft_jewelry('life_ring', quantity)

        if sell:
            self._sell_item('life_ring', quantity)

    def craft_cooked_gudgeon(self, quantity=1, sell=False):
        self.gather_resource_from_location('gudgeon', quantity)

        self._craft_food('cooked_gudgeon', quantity)

        if sell:
            self._sell_item('cooked_gudgeon', quantity)

    def craft_cooked_chicken(self, quantity=1, sell=False):
        self.gather_resource_from_monsters('raw_chicken', quantity)

        self._craft_food('cooked_chicken', quantity)

        if sell:
            self._sell_item('cooked_chicken', quantity)

    def craft_cooked_beef(self, quantity=1, sell=False):
        self.gather_resource_from_monsters('raw_beef', quantity)

        self._craft_food('cooked_beef', quantity)

        if sell:
            self._sell_item('cooked_beef', quantity)

    def craft_cooked_shrimp(self, quantity=1, sell=False):
        self.gather_resource_from_location('shrimp', quantity)

        self._craft_food('cooked_shrimp', quantity)

        if sell:
            self._sell_item('cooked_shrimp', quantity)

    def craft_cheese(self, quantity=1, sell=False):
        self.gather_resource_from_monsters('milk_bucket', 3 * quantity)

        self._craft_food('cheese', quantity)

        if sell:
            self._sell_item('cheese', quantity)

    def craft_fried_eggs(self, quantity=1, sell=False):
        self.gather_resource_from_monsters('egg', 5 * quantity)

        self._craft_food('fried_eggs', quantity)

        if sell:
            self._sell_item('fried_eggs', quantity)

    def craft_mushroom_soup(self, quantity=1, sell=False):
        self.craft_ash_planks(quantity)
        self.gather_resource_from_monsters('milk_bucket', quantity)
        self.gather_resource_from_monsters('mushroom', quantity)

        self._craft_food('mushroom_soup', quantity)

        if sell:
            self._sell_item('mushroom_soup', quantity)

    def craft_beef_stew(self, quantity=1, sell=False):
        self.craft_ash_planks(quantity)
        self.gather_resource_from_monsters('raw_beef', 3 * quantity)

        self._craft_food('beef_stew', quantity)

        if sell:
            self._sell_item('beef_stew', quantity)

    def craft_cooked_wolf_meat(self, quantity=1, sell=False):
        self.gather_resource_from_monsters('raw_wolf_meat', quantity)

        self._craft_food('cooked_wolf_meat', quantity)

        if sell:
            self._sell_item('cooked_wolf_meat', quantity)

    def craft_cooked_trout(self, quantity=1, sell=False):
        self.gather_resource_from_location('trout', quantity)

        self._craft_food('cooked_trout', quantity)

        if sell:
            self._sell_item('cooked_trout', quantity)

    def craft_cooked_bass(self, quantity=1, sell=False):
        self.gather_resource_from_location('bass', quantity)

        self._craft_food('cooked_bass', quantity)

        if sell:
            self._sell_item('cooked_bass', quantity)

