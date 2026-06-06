# Console client for Artifacts MMO

## About

A simple console client for interacting with the [Artifacts MMO](https://artifactsmmo.com/) game APIs.
Interaction with the user is realized by selecting from the offered options by entering the digits of the menu items.

The client targets the current public API (v7.x) and supports every character action and most of the account/world endpoints.

## Installation

1. Clone the repository:

```shell
git clone https://github.com/philarete173/artifactsmmo-client.git
```

2. Go to project folder, create virtual environment and activate it:
```shell
cd .\artifactsmmo-client
python -m venv .venv
source .venv/bin/activate  # for Windows use .venv\Scripts\activate
```

3. Install requirements (the list of used libraries can be found in the requirements.txt file):
```shell
pip install -r requirements.txt
```

## Usage

Before starting the client, you must specify your token in the config.ini configuration file (an example can be found in config.ini.example):

```ini
[General]
TOKEN = ACCOUNT_TOKEN
```

Your token can be found on the https://artifactsmmo.com/account page.

Now the client can be run through the main.py file:

```shell
python main.py
```

At startup, the client checks for server availability and shows the current game version and season, then prompts for the account token.
If there are no characters on the account, you will be prompted to create one.

```
Game version: 1.0.0.
Current season: Frozen Vows (#5), started 2025-12-01T00:00:00Z.
```

Further interaction is realized by selecting the required menu item and transferring the necessary data for sending requests.
The list of available actions depends on the type of location the character is currently in.

## Supported actions

The available action set depends on the current map `content.type`:

| Location type | Available actions |
|---|---|
| any | move, transition, equip, unequip, use item, rest, change skin, show bank, show pending items, show ge orders, claim pending item, give gold, give item, use scenario |
| `monster` | + fight |
| `resource` | + gathering |
| `workshop` | + crafting, recycling |
| `bank` | + deposit item/gold, withdraw item/gold, buy bank expansion |
| `grand_exchange` | + buy ge item, cancel/create/fill ge orders |
| `tasks_master` | + new/complete/cancel task, exchange task coins, trade task |
| `npc` | + buy/sell npc item |

If you want to run a specific set of actions, you can add them as scenarios to the storage.
Examples of scenarios are in the scripts.py file.
They will then be available in the action menu item "use scenario".

## Scripting

The `ScenariosStorage` class in `scripts.py` exposes:

- **Gather resources** — gather raw materials from resources or monsters
- **Craft resources** — refine raw materials into ingots/planks
- **Craft equipment** — full recipe chains for weapons/armor/jewelry
- **Craft consumables** — cooking recipes
- **Recycling** — salvage unequipped gear
- **Other** — automated tasks master quests, bank deposits

All scenarios look up the relevant workshop/map dynamically via the `/maps?content_code=...` endpoint, so they don't depend on hardcoded coordinates.

## Public API coverage

The client is a thin wrapper over the public Artifacts MMO REST API. Every endpoint reachable to a logged-in account is exposed as a method on `GameClient` or `Character`.

### Account (`/my/...`)
- server details (version, current season), account details, change password
- bank (details, items, expansion), pending items
- grand exchange (orders, history)
- characters list, logs

### Characters
- create/delete character, get character, list active characters
- list characters of any account
- every `action/*` endpoint: move (x/y or map_id), transition, fight, gathering, crafting, recycling, equip, unequip, use, delete, rest, change skin, claim pending item, give gold/item, npc buy/sell, all task actions, all bank actions, all grand exchange actions, buy bank expansion

### World data
- maps (by id, by layer, by position, filtered by content type/code, hiding blocked maps)
- items, monsters, resources, NPCs and NPC items
- tasks list / rewards
- achievements and badges
- effects, events (list, active, spawn)
- leaderboard (accounts, characters)
- fight simulation
