"""Workaround for a broken import in ragas 0.4.x.

ragas/llms/base.py unconditionally imports
`langchain_community.chat_models.vertexai.ChatVertexAI`, but that submodule
was removed from langchain-community (it's being sunset in favor of the
standalone langchain-google-vertexai package). We don't use VertexAI at all,
so this stubs out just enough of the module for ragas to import cleanly.

Must be imported before anything else in this package imports `ragas`.
"""

import sys
import types

if "langchain_community.chat_models.vertexai" not in sys.modules:
    from langchain_community.llms import VertexAI

    _shim = types.ModuleType("langchain_community.chat_models.vertexai")
    _shim.ChatVertexAI = VertexAI
    sys.modules["langchain_community.chat_models.vertexai"] = _shim
