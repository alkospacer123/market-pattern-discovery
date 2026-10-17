"""GUI input contract: mock Tk on any host, no actual token, network or display."""
import sys
import types
import unittest
from unittest.mock import patch

from IntradayLab.m15_robot.step15_broker_probe import (
    M15RiskAuthorityError, _gui_credentials,
)


class FakeTk:
    def __init__(self, values, button="READONLY check"):
        self.values = values
        self.button = button
        self.entries = []
        self.password_shows = []
        self.commands = {}
        self.labels = []
        self.destroyed = False

    def title(self, *args): pass
    def geometry(self, *args): pass
    def resizable(self, *args): pass
    def protocol(self, *args): pass
    def bind(self, *args): pass
    def lift(self): pass
    def quit(self): pass
    def destroy(self): self.destroyed = True
    def mainloop(self): self.commands[self.button]()


class FakeElement:
    def __init__(self, root, kind, **kwargs):
        self.root = root
        self.kind = kind
        self.kwargs = kwargs
        if kind == "entry":
            self.position = len(root.entries)
            root.entries.append(self)
            root.password_shows.append(kwargs.get("show"))
        if kind == "button":
            root.commands[kwargs["text"]] = kwargs["command"]

    def pack(self, *args, **kwargs): pass
    def focus_set(self): pass
    def config(self, **kwargs): self.kwargs.update(kwargs)
    def get(self):
        return self.root.values[self.position]


def fake_tk(root):
    return types.SimpleNamespace(
        Tk=lambda: root,
        Label=lambda parent, **kwargs: FakeElement(root, "label", **kwargs),
        Entry=lambda parent, **kwargs: FakeElement(root, "entry", **kwargs),
        Frame=lambda parent, **kwargs: FakeElement(root, "frame", **kwargs),
        Button=lambda parent, **kwargs: FakeElement(root, "button", **kwargs),
    )


class M15GUICredentials(unittest.TestCase):
    def test_local_paste_gui_return_values_and_mask_token(self):
        root = FakeTk(("m15-demo", "h1-demo", "masked-synthetic-token"))
        with patch.dict(sys.modules, {"tkinter": fake_tk(root)}):
            values = _gui_credentials()
        self.assertEqual(values, ("m15-demo", "h1-demo", "masked-synthetic-token"))
        self.assertEqual(root.password_shows, ["", "", "*"])
        self.assertTrue(root.destroyed)

    def test_cancel_exits_before_network(self):
        root = FakeTk(("", "", ""), button="Cancel")
        with patch.dict(sys.modules, {"tkinter": fake_tk(root)}):
            with self.assertRaisesRegex(M15RiskAuthorityError, "GUI_CANCELLED"):
                _gui_credentials()
        self.assertTrue(root.destroyed)

    def test_missing_fields_fail_closed(self):
        root = FakeTk(("m15-demo", "h1-demo", ""))
        with patch.dict(sys.modules, {"tkinter": fake_tk(root)}):
            with self.assertRaisesRegex(M15RiskAuthorityError, "GUI_CANCELLED"):
                _gui_credentials()

    def test_equal_account_ids_fail_closed(self):
        root = FakeTk(("same-account", "same-account", "synthetic-token"))
        with patch.dict(sys.modules, {"tkinter": fake_tk(root)}):
            with self.assertRaisesRegex(M15RiskAuthorityError, "GUI_CANCELLED"):
                _gui_credentials()

    def test_no_tk_installed_fails_closed(self):
        with patch.dict(sys.modules, {"tkinter": None}):
            with self.assertRaisesRegex(M15RiskAuthorityError, "GUI_NOT_AVAILABLE"):
                _gui_credentials()


if __name__ == "__main__":
    unittest.main()
