from ovos_plugin_manager.utils import load_plugin, find_plugins, PluginTypes
from ovos_utils.configuration import read_mycroft_config
from ovos_utils.messagebus import get_mycroft_bus


def find_text_transformer_plugins():
    return find_plugins(PluginTypes.TEXT_TRANSFORM)


def load_text_transformer_plugin(module_name):
    """Wrapper function for loading text_transformer plugin.

    Arguments:
        (str) Mycroft text_transformer module name from config
    Returns:
        class: found text_transformer plugin class
    """
    return load_plugin(module_name, PluginTypes.TEXT_TRANSFORM)


class TextTransformer:
    def __init__(self, name, priority=50, config=None):
        self.name = name
        self.bus = None
        self.priority = priority
        if not config:
            config_core = read_mycroft_config()
            config = config_core.get("text_transformers", {}).get(self.name)
        self.config = config or {}

    def bind(self, bus=None):
        """ attach messagebus """
        self.bus = bus or get_mycroft_bus()

    def initialize(self):
        """ perform any initialization actions """
        pass

    def transform(self, utterances, lang="en-us"):
        """ parse utterances
        return modified utterances + metadata to be merged into message context """
        return utterances, {}

    def default_shutdown(self):
        """ perform any shutdown actions """
        pass

