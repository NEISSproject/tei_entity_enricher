from abc import abstractmethod

from tei_entity_enricher.util.SessionState import _SessionState


class MenuBase(object):
    def __init__(self, state: _SessionState, show_menu: bool = True, name: str = ""):
        self.name: str = name
        self.state = state
        self.show_menu: bool = show_menu

    @abstractmethod
    def show(self, **kwargs):
        """all visible streamlit components are created here"""
        raise NotImplementedError

    @abstractmethod
    def check(self, **kwargs):
        """return True if class has an expected state, False otherwise."""
        raise NotImplementedError
