# JWPlaceholderAPI

**JWPlaceholderAPI** is a unified placeholder framework for Endstone Minecraft servers, completely rewritten in Python! 

### What does it do?
It provides a standardized way for different plugins to share and parse variables (placeholders). Instead of every plugin implementing its own variable system (like replacing `%player%` or `{name}` in config files), JWPlaceholderAPI provides a single, central API that parses strings like `%player_name%` and `%server_online%` dynamically.

### Why is it useful?
- **For Server Owners:** You can use placeholders from one plugin (e.g., JWEconomy's `%jweco_balance%`) inside another plugin's configuration (e.g., JWBossScore's scoreboard lines). This makes your server deeply interconnected and customizable.
- **For Developers:** You no longer need to write custom logic to fetch another plugin's data. You just hook into JWPlaceholderAPI, and instantly your plugin can support hundreds of placeholders from other plugins. You can also expose your own plugin's data to the rest of the server easily.

### How to use it?
Simply install the plugin on your server! It works automatically in the background. 
- **Server Owners:** Look for plugins that mention "PlaceholderAPI support". You can then use any registered placeholders in their config files. You can check available placeholders using `/papi list` in-game.
- **Developers:** Read the Developer API section below to learn how to parse placeholders in your strings or how to register your own custom placeholders.

- 🌐 Website: https://jw-placeholder-api-page.vercel.app/

## 🚀 Features
- **Built-in Placeholders:** Comes with `%player_...%` and `%server_...%` placeholders out of the box.
- **Developer API:** Easily create and register your own placeholders within your own Endstone Python plugins.
- **High Performance:** Async-friendly and optimized string replacement logic.

## 💻 Commands & Permissions
| Command | Permission | Description |
|---|---|---|
| `/papi list` | `jwplaceholderapi.admin` | List all registered expansions. |
| `/papi info <id>` | `jwplaceholderapi.admin` | View details about a specific expansion. |
| `/papi parse <player> <text>` | `jwplaceholderapi.admin` | Test placeholders in-game (e.g., `/papi parse Steve %player_name% is cool`). |

## 🛠️ Developer API: Creating Your Own Expansion

If you are a plugin developer, you can hook into JWPlaceholderAPI to provide your own placeholders!

### 1. Add `jwplaceholderapi` as a dependency
In your plugin's `main.py`, add `jwplaceholderapi` as a `depend` or `soft_depend`.

### 2. Create an Expansion Class
Create a class that inherits from `PlaceholderExpansion`. You can safely fallback to `object` if you only use JWPlaceholderAPI as a soft-dependency.

```python
from typing import Optional
from endstone import Player

try:
    from jwplaceholderapi.expansion import PlaceholderExpansion
except ImportError:
    PlaceholderExpansion = object # Fallback if PAPI is not installed

class MyCustomExpansion(PlaceholderExpansion):
    def __init__(self, plugin):
        self.plugin = plugin
        super().__init__()

    # The prefix of your placeholder (e.g., %myplugin_...%)
    def get_identifier(self) -> str:
        return "myplugin"

    def get_author(self) -> str:
        return "YourName"

    def get_version(self) -> str:
        return "1.0.0"

    # This method is called whenever a placeholder matching your identifier is found
    def on_request(self, player: Optional[Player], params: str) -> Optional[str]:
        # player might be None if the placeholder is requested by the console
        if not player:
            return None

        # Handle %myplugin_kills%
        if params == "kills":
            return str(self.plugin.get_player_kills(player))
        
        # Handle %myplugin_rank%
        if params == "rank":
            return self.plugin.get_player_rank(player)

        # Return None if the parameter is unknown. PAPI will leave the text unparsed.
        return None
```

### 3. Register your Expansion
Register your expansion when your plugin enables:

```python
from endstone.plugin import Plugin
from .my_expansion import MyCustomExpansion

class MyPlugin(Plugin):
    api_version = "0.11"
    name = "MyPlugin"
    version = "1.0.0"
    soft_depend = ["jwplaceholderapi"]

    def on_enable(self) -> None:
        papi = self.server.plugin_manager.get_plugin("jwplaceholderapi")
        if papi:
            try:
                # Register the expansion
                papi.register_expansion(MyCustomExpansion(self))
                self.logger.info("Successfully hooked into JWPlaceholderAPI!")
            except Exception as e:
                self.logger.warning(f"Failed to hook into JWPlaceholderAPI: {e}")
```

## 📝 Parsing Placeholders in Your Plugin
If you want your plugin to support placeholders (like in chat formats, scoreboards, or MOTDs), you can use PAPI to parse them!

```python
papi = self.server.plugin_manager.get_plugin("jwplaceholderapi")
if papi:
    raw_text = "Welcome back, %player_name%! Your rank is %myplugin_rank%."
    
    # Parse standard %placeholders%
    parsed_text = papi.set_placeholders(player, raw_text)
    
    # Parse bracket {placeholders}
    parsed_bracket_text = papi.set_bracket_placeholders(player, raw_text)
```
