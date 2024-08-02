from api import Character


def craft_wooden_staff(character: Character, quantity=1):
    character.move(6, 1)
    for _ in range(18*quantity):
        character.gathering()

    character.move(-2, -3)
    character.crafting('ash_plank', 3*quantity)

    character.move(6, 1)
    for _ in range(4*quantity):
        character.gathering()

    character.move(2, 1)
    character.crafting('wooden_stick', quantity)
    character.crafting('wooden_staff', quantity)


def craft_copper_dagger(character: Character, quantity=1):
    character.move(2, 0)
    for _ in range(18*quantity):
        character.gathering()

    character.move(1, 5)
    character.crafting('copper', 3*quantity)

    character.move(2, 1)
    character.crafting('copper_dagger', quantity)
