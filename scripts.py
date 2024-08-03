class ScenariosStorage:
    """Class for storing scenarios for character automation."""

    def __init__(self, character):
        self.character = character

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

    def craft_copper(self, quantity=1):
        self.gather_copper_ore(6 * quantity)

        self.character.move(1, 5)
        self.character.crafting('copper', quantity)

    def craft_iron(self, quantity=1):
        self.gather_iron_ore(6 * quantity)

        self.character.move(1, 5)
        self.character.crafting('iron', quantity)

    def craft_steel(self, quantity=1):
        self.gather_iron_ore(2 * quantity)
        self.gather_coal(4 * quantity)

        self.character.move(1, 5)
        self.character.crafting('steel', quantity)

    def craft_gold(self, quantity=1):
        self.gather_gold_ore(6 * quantity)

        self.character.move(1, 5)
        self.character.crafting('gold', quantity)

    def craft_ash_planks(self, quantity=1):
        self.gather_ash_wood(6 * quantity)

        self.character.move(-2, -3)
        self.character.crafting('ash_plank', quantity)

    def craft_spruce_planks(self, quantity=1):
        self.gather_spruce_wood(6 * quantity)

        self.character.move(-2, -3)
        self.character.crafting('spruce_plank', quantity)

    def craft_hardwood_planks(self, quantity=1):
        self.gather_ash_wood(2 * quantity)
        self.gather_birch_wood(4 * quantity)

        self.character.move(-2, -3)
        self.character.crafting('hardwood_plank', quantity)

    def sell_item(self, item_name='', quantity=1):
        self.character.move(5, 1)
        self.character.sell_item(item_name, quantity)

    def craft_wooden_staff(self, quantity=1, sell=False):
        self.craft_ash_planks(3 * quantity)

        self.gather_ash_wood(4 * quantity)

        self.character.move(2, 1)
        self.character.crafting('wooden_stick', quantity)
        self.character.crafting('wooden_staff', quantity)

        if sell:
            self.sell_item('wooden_staff', quantity)

    def craft_wooden_shield(self, quantity=1, sell=False):
        self.craft_ash_planks(3 * quantity)

        self.character.move(3, 1)
        self.character.crafting('wooden_shield', quantity)

        if sell:
            self.sell_item('wooden_shield', quantity)

    def craft_copper_dagger(self, quantity=1, sell=False):
        self.craft_copper(3 * quantity)

        self.character.move(2, 1)
        self.character.crafting('copper_dagger', quantity)

        if sell:
            self.sell_item('copper_dagger', quantity)

    def craft_copper_helmet(self, quantity=1, sell=False):
        self.craft_copper(3 * quantity)

        self.character.move(3, 1)
        self.character.crafting('copper_helmet', quantity)

        if sell:
            self.sell_item('copper_helmet', quantity)

    def craft_copper_boots(self, quantity=1, sell=False):
        self.craft_copper(3 * quantity)

        self.character.move(3, 1)
        self.character.crafting('copper_boots', quantity)

        if sell:
            self.sell_item('copper_boots', quantity)

    def craft_copper_ring(self, quantity=1, sell=False):
        self.craft_copper(4 * quantity)

        self.character.move(1, 3)
        self.character.crafting('copper_ring', quantity)

        if sell:
            self.sell_item('copper_ring', quantity)

    def craft_copper_armor(self, quantity=1, sell=False):
        self.craft_copper(5 * quantity)

        self.character.move(3, 1)
        self.character.crafting('copper_armor', quantity)

        if sell:
            self.sell_item('copper_armor', quantity)

    def craft_copper_legs_armor(self, quantity=1, sell=False):
        self.craft_copper(4 * quantity)

        self.character.move(3, 1)
        self.character.crafting('copper_legs_armor', quantity)

        if sell:
            self.sell_item('copper_legs_armor', quantity)
