from pyrevit import script, DB, forms
from rpw.ui.forms import FlexForm, Label, CheckBox, Button, ComboBox
import sys

custom_config = script.get_config("Override Options")

override_options = ["Projection Line Colour", "Projection Surface Colour", "Cut Line Colour", "Cut Pattern Colour"]
default_options = ["Projection Surface Colour", "Cut Pattern Colour"]


class ChosenItem(forms.TemplateListItem):
    """Wrapper class for chosen item"""
    pass


def get_config():
    prev_choice = custom_config.get_option("overrides", [])
    return prev_choice


def save_config(chosen, config):
    """Save given list of overrides"""
    config.overrides = chosen
    script.save_config()


def load_configs(config):
    """Load list of frequently selected items from configs or defaults"""
    ovrds = config.get_option("overrides", [])
    ovrd_items = [x for x in (ovrds or default_options)]
    return filter(None, ovrd_items)


def config_overrides(config):
    """Ask for users choice of overrides"""
    prev_ovrds = load_configs(config)
    opts = [ChosenItem(x, checked=x in prev_ovrds) for x in override_options]
    overrides = forms.SelectFromList.show(
        opts,
        title="Choose Overrides Styles",
        button_name="Remember",
        multiselect=True
    )
    if overrides:
        save_config([x for x in overrides if x], config)


if __name__ == "__main__":
    config_overrides(custom_config)
