"""
Citadel C2 Framework
"""

from .protocol import C2Protocol
from .agent.phantom import PhantomAgent
from .server.citadel import CitadelServer

__all__ = ['C2Protocol', 'PhantomAgent', 'CitadelServer']
__version__ = "0.0.0"
