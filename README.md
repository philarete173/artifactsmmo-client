# Console client for Artifacts MMO

## About

A simple console client for interacting with the Artifacts MMO game APIs. 
Interaction with the user is realized by selecting from the offered options by entering the digits of the menu items.

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

3. Install requirements (The list of used libraries can be found in the requirements.txt file):
```shell
pip install -r requirements.txt
```

## Usage

Before starting the client, you must specify your token in the config.ini configuration file (an example can be found in config.ini.example):

```ini
[General]
TOKEN = ACCOUNT_TOKEN
```

Your token can be found on the https://artifactsmmo.com/account

Now the client can be run through the main.py file:

```shell
python main.py
```

At startup, the client checks for server availability and requests a list of characters on the account. 
If there are no characters, you will be prompted to create one.

```
Server status is "online".
Welcome to Artifacts Alpha 1. The server is up.
```

Further interaction is realized by selecting the required menu item and transferring the necessary data for sending requests

```
What do you want to do?
1 - move
2 - fight
3 - gathering
4 - crafting
5 - equip
6 - unequip
7 - new task
8 - complete task
9 - buy item
10 - sell item
11 - use scenario
Please type a number: 
```

If you want to run a specific set of actions, you can add them as scripts to the storage. 
Examples of scripts are in the scripts.py file. 
They will then be available in the action menu item "use scenario"