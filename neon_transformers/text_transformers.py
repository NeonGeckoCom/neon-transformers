# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2025 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from typing import List, Optional, Tuple
from ovos_plugin_manager.text_transformers import find_utterance_transformer_plugins, load_utterance_transformer_plugin
from ovos_config.config import Configuration
from ovos_utils.json_helper import merge_dict
from ovos_utils.log import LOG
from ovos_bus_client.util import get_mycroft_bus
from neon_transformers.tasks import UtteranceTask


class UtteranceTransformer:
    task = UtteranceTask.OTHER

    def __init__(self, name, priority=50, config=None):
        self.name = name
        self.bus = None
        self.priority = priority
        if not config:
            config_core = dict(Configuration())
            config = config_core.get("utterance_transformers", {}).get(self.name)
        self.config = config or {}

    def bind(self, bus=None):
        """ attach messagebus """
        self.bus = bus or get_mycroft_bus()

    def initialize(self):
        """ perform any initialization actions """
        pass

    def transform(self, utterances: List[str],
                  context: dict = None) -> Tuple[list, dict]:
        """
        Optionally transform passed utterances and/or return additional context
        :param utterances: List of str utterances to parse
        :param context: existing Message context associated with utterances
        :returns: tuple of (possibly modified utterances, additional context)
        """
        return utterances, {}

    def default_shutdown(self):
        """ perform any shutdown actions """
        pass


class UtteranceTransformersService:

    def __init__(self, bus, config=None):
        self.config_core = config or Configuration()
        self.loaded_modules = {}
        self.has_loaded = False
        self.bus = bus
        self.config = self.config_core.get("utterance_transformers") or dict()
        self.load_plugins()

    def load_plugins(self):
        for plug_name, plug in find_utterance_transformer_plugins().items():
            if plug_name in self.config:
                # if disabled skip it
                if not self.config[plug_name].get("active", True):
                    continue
                try:
                    self.loaded_modules[plug_name] = plug()
                    LOG.info(f"loaded utterance transformer plugin: {plug_name}")
                except Exception as e:
                    LOG.error(e)
                    LOG.exception(f"Failed to load utterance transformer plugin: {plug_name}")

    @property
    def modules(self):
        """
        Return loaded transformers in priority order, such that modules with a
        higher `priority` rank are called first and changes from lower ranked
        transformers are applied last

        A plugin of `priority` 1 will override any existing context keys and
        will be the last to modify utterances`
        """
        return sorted(self.loaded_modules.values(),
                      key=lambda k: k.priority, reverse=True)

    def shutdown(self):
        for module in self.modules:
            try:
                module.shutdown()
            except:
                pass

    def transform(self, utterances: List[str], context: Optional[dict] = None):
        context = context or {}

        for module in self.modules:
            try:
                utterances, data = module.transform(utterances, context)
                LOG.debug(f"{module.name}: {data}")
                context = merge_dict(context, data)
            except Exception as e:
                LOG.warning(f"{module.name} transform exception: {e}")
        return utterances, context
