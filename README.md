# JWPlaceholderAPI (Python)

A unified placeholder framework for Endstone servers, completely rewritten in Python! This plugin allows server owners to use dynamic placeholders across different plugins, and provides a simple API for developers to register their own custom placeholders.

## 🚀 Features
- **Built-in Placeholders:** Comes with `%player_...%` and `%server_...%` placeholders out of the box.
- **Developer API:** Easily create and register your own placeholders within your own Endstone Python plugins.
- **High Performance:** Async-friendly and optimized string replacement logic.

## 💻 Commands & Permissions
| Command | Permission | Description |
|---|---|---|
| `/papi list` | `papi.admin` | List all registered expansions. |
| `/papi info <id>` | `papi.admin` | View details about a specific expansion. |
| `/papi parse <player> <text>` | `papi.admin` | Test placeholders in-game (e.g., `/papi parse Steve %player_name% is cool`). |

## 🛠️ Developer API: Creating Your Own Expansion

If you are a plugin developer, you can hook into JWPlaceholderAPI to provide your own placeholders!

### 1. Add `jwplaceholderapi` as a dependency
In your plugin's `pyproject.toml` or `plugin.yml`, add `jwplaceholderapi` as a `depend` or `soft_depend`.

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