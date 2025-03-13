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

import os
import sys
import unittest

from mock.mock import Mock
from copy import deepcopy
from ovos_utils.messagebus import FakeBus

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from neon_transformers import UtteranceTransformer
from neon_transformers.tasks import UtteranceTask


class MockTransformer(UtteranceTransformer):
    task = UtteranceTask.TRANSFORM

    def __init__(self):
        super().__init__("mock_transformer")

    def transform(self, utterances, context=None):
        return utterances + ["transformer"], {}


class MockContextAdder(UtteranceTransformer):
    task = UtteranceTask.ADD_CONTEXT

    def __init__(self):
        super().__init__("mock_context_adder")

    def transform(self, utterances, context=None):
        return utterances, {"old_context": False,
                            "new_context": True,
                            "new_key": "test"}


class TextTransformersTests(unittest.TestCase):
    def test_utterance_transformer_service_load(self):
        from neon_transformers.text_transformers import UtteranceTransformersService
        bus = FakeBus()
        service = UtteranceTransformersService(bus)
        self.assertIsInstance(service.config, dict)
        self.assertEqual(service.bus, bus)
        self.assertFalse(service.has_loaded)
        self.assertIsInstance(service.loaded_modules, dict)
        for plugin in service.loaded_modules:
            self.assertIsInstance(service.loaded_modules[plugin],
                                  UtteranceTransformer)
        self.assertIsInstance(service.modules, list)
        self.assertEqual(len(service.loaded_modules), len(service.modules))
        service.shutdown()

    def test_utterance_transformer_service_transform(self):
        from neon_transformers.text_transformers import UtteranceTransformersService
        bus = FakeBus()
        service = UtteranceTransformersService(bus)
        service.loaded_modules = {"mock_transformer": MockTransformer()}
        utterances = ["test", "utterance"]
        context = {"old_context": True,
                   "new_context": False}
        utterances, context = service.transform(utterances, context)
        self.assertEqual(" ".join(utterances), "test utterance transformer")
        self.assertEqual(context, {"old_context": True,
                                   "new_context": False})

        service.loaded_modules["mock_context_adder"] = MockContextAdder()
        utterances, context = service.transform(utterances, context)
        self.assertEqual(utterances, ["test", "utterance",
                                      "transformer", "transformer"])
        self.assertEqual(context, {"old_context": False,
                                   "new_context": True,
                                   "new_key": "test"})
        service.shutdown()

    def test_utterance_transformer_service_priority(self):
        from neon_transformers.text_transformers import UtteranceTransformersService

        utterances = ["test 1", "test one"]
        lang = "en-us"

        def mod_1_parse(utterances, lang):
            utterances.append("mod 1 parsed")
            return utterances, {"parser_context": "mod_1"}

        def mod_2_parse(utterances, lang):
            utterances.append("mod 2 parsed")
            return utterances, {"parser_context": "mod_2"}

        bus = FakeBus()
        service = UtteranceTransformersService(bus)

        mod_1 = Mock()
        mod_1.priority = 2
        mod_1.transform = mod_1_parse
        mod_2 = Mock()
        mod_2.priority = 1
        mod_2.transform = mod_2_parse

        service.loaded_modules = \
            {"test_mod_1": mod_1,
             "test_mod_2": mod_2}

        on_text_context = Mock()
        bus.once('neon.text_transformers.context', on_text_context)
        # Check transformers adding utterances
        new_utterances, context = service.transform(deepcopy(utterances),
                                                    {'lang': lang})
        self.assertEqual(context["parser_context"], "mod_2")
        self.assertNotEqual(new_utterances, utterances)
        self.assertEqual(len(new_utterances),
                         len(utterances) + 2)

        # Check context change on priority swap
        mod_2.priority = 100
        _, context = service.transform(deepcopy(utterances),
                                       {'lang': lang})
        self.assertEqual(context["parser_context"], "mod_1")

        # Check emitted context
        on_text_context.assert_called_once()
        msg = on_text_context.call_args[0][0]
        self.assertEqual(msg.msg_type, 'neon.text_transformers.context')
        self.assertEqual(msg.context, {'lang': lang,
                                       "parser_context": "mod_2"})
        self.assertEqual(msg.data, {"parser_context": "mod_2"})


if __name__ == "__main__":
    unittest.main()
