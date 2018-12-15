# Elite Four Bot

The Elite Four Bot is an AI bot which uses the minimax algorithm to win games on Pokemon Showdown. This bot was written by a team of students as a [final project](https://github.com/fhenrywells/elitefourbot) for CS 221. Special thanks to [Henry Weller](https://github.com/fhenrywells) and [Nicholas Allen](https://github.com/nickanallen) for their contributions.


## Starting a Pokemon-Showdown Server

Go to the [Pokemon-Showdown](./Pokemon-Showdown) directory in your terminal and enter `node pokemon-showdown`

This will start Pokemon-Showdown, using your computer as a local server. Detailed instructions on this process can be found in the Pokemon-Showdown [README](./Pokemon-Showdown/README.md) file. This functionality was forked from Zarel's [Pokemon Showdown](https://github.com/Zarel/Pokemon-Showdown).


## Playing an AI Bot

Go to [Pokemon-Showdown-Bot](./Pokemon-Showdown/Pokemon-Showdown-Bot) and enter `node bot` in your terminal.

This will start the AI bot. By default, the bot will look for the localhost:8000. You can change this in the Pokemon-Showdown-Bot [config.js](./Pokemon-Showdown/Pokemon-Showdown-Bot/config.js) file. The main server is `sim.smogon.com`. Instructions on running the server above. 

The bot calls on a Flask endpoint to get the best decision after each turn. To get the flask server running, go to the [sim](./Pokemon-Showdown/sim) directory and run enter `python minimaxserver.py`. This will start the minimax server and expose the flask endpoint.


Detailed instructions on bot features and configurations can be found in the Pokemon-Showdown-Bot [README](./Pokemon-Showdown/Pokemon-Showdown-Bot/README.md) file. Functionality for internet connectivity was forked from [Pokemon-Showdown-Node-Bot](https://github.com/Ecuacion/Pokemon-Showdown-Node-Bot). Special thanks to [Ecuacion](https://github.com/Ecuacion) for his work, which has allowed our AI bot to play against others users online.
