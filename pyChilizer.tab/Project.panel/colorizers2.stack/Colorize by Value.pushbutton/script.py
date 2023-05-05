import sys

from pyrevit import revit, DB, forms
from pyrevit import script
import random
from pychilizer import database
from pychilizer import colorize
from pyrevit.framework import List
import colorizebyvalueconfig
from collections import defaultdict
from pyrevit.revit.db import query

logger = script.get_logger()
BIC = DB.BuiltInCategory
doc = revit.doc
view = revit.active_view

overrides_option = colorizebyvalueconfig.get_config()


# colour gradients solution by https://bsouthga.dev/posts/color-gradients-with-python

# [ ] test in R2022
# [x] test in R2023
# [ ] find and exclude irrelevant builtin params
# [-] PROJECT PARAMETERS NOT SUPPORTED DUE TO HIGH NR OF REPETITIONS


class ParameterOption(forms.TemplateListItem):
    """Wrapper for selecting parameters from a list"""

    def __init__(self, param, param_dict):
        super(ParameterOption, self).__init__(param)
        self.param_dict = param_dict

    @property
    def name(self):
        return str(self.param_dict[self.item])


category_opt_dict = {
    "Windows": BIC.OST_Windows,
    "Doors": BIC.OST_Doors,
    "Floors": BIC.OST_Floors,
    "Walls": BIC.OST_Walls,
    "Generic Model": BIC.OST_GenericModel,
    "Casework": BIC.OST_Casework,
    "Furniture": BIC.OST_Furniture,
    "Furniture Systems": BIC.OST_FurnitureSystems,
    "Plumbing Fixtures": BIC.OST_PlumbingFixtures,
    "Roofs": BIC.OST_Roofs,
    "Electrical Equipment": BIC.OST_ElectricalEquipment,
    "Electrical Fixtures": BIC.OST_ElectricalFixtures,
    "Parking": BIC.OST_Parking,
    "Site": BIC.OST_Site,
    "Entourage": BIC.OST_Entourage,
    "Ceilings": BIC.OST_Ceilings,
    "Curtain Wall Panels": BIC.OST_CurtainWallPanels,
    "Curtain Wall Mullions": BIC.OST_CurtainWallMullions,
    "Topography":BIC.OST_Topography,
    "Structural Columns":BIC.OST_StructuralColumns,
    "Structural Framing":BIC.OST_StructuralFraming,
    "Stairs":BIC.OST_Stairs,
    "Ramps":BIC.OST_Ramps,
}

if forms.check_modelview(revit.active_view):
    selected_cat = forms.CommandSwitchWindow.show(sorted(category_opt_dict), message="Select Category to Colorize",
                                                  width=400)
if selected_cat == None:
    script.exit()
# format the category dictionary
chosen_bic = category_opt_dict[selected_cat]

# get all element categories and return a list of all categories except chosen BIC
all_cats = doc.Settings.Categories
chosen_category = all_cats.get_Item(chosen_bic)
hide_categories_except = [c for c in all_cats if c.Id != chosen_category.Id]

get_view_elements = DB.FilteredElementCollector(doc) \
    .OfCategory(chosen_bic) \
    .WhereElementIsNotElementType() \
    .ToElements()

inst_param_dict = {}
type_param_dict = {}


def param_is_bip(param):
    # check if parameter if a BIP
    return param.Definition.BuiltInParameter != DB.BuiltInParameter.INVALID


for e in get_view_elements:
    element_parameter_set = e.Parameters
    for ip in element_parameter_set:
        # if the parameter is shared - store as Id
        if ip.IsShared and ip.Definition.Id not in inst_param_dict:
            pretty_param_name = "".join([str(ip.Definition.Name), " [Shared Parameter]"])
            inst_param_dict[ip.Definition.Id] = pretty_param_name
        # if the param is BIP - store as BIP
        elif param_is_bip(ip) and ip.Definition.Name not in inst_param_dict:
            inst_param_dict[ip.Definition.BuiltInParameter] = str(ip.Definition.Name)
        # another case - Project Parameters - NOT SUPPORTED due to possible duplicates with Family Parameters
        # elif not (ip.IsShared) and not(param_is_bip(ip)) and ip.Definition.Id not in inst_param_dict:
        #     pretty_param_name = "".join([str(ip.Definition.Name), " [Project Parameter]"])
        #     inst_param_dict[ip.Definition.Id] = pretty_param_name


    type_parameter_set = doc.GetElement(e.GetTypeId()).Parameters
    for tp in type_parameter_set:
        if tp.IsShared and tp.Definition.Id not in type_param_dict:
            pretty_param_name = "".join([str(tp.Definition.Name), " [Shared Parameter]"])
            type_param_dict[tp.Definition.Id] = pretty_param_name
        elif param_is_bip(tp) and tp.Definition.Name not in type_param_dict:
            type_param_dict[tp.Definition.BuiltInParameter] = str(tp.Definition.Name)
        # elif not (tp.IsShared) and not(param_is_bip(tp)) and tp.Definition.Id not in inst_param_dict:
        #     pretty_param_name = "".join([str(tp.Definition.Name), " [Project Parameter]"])
        #     inst_param_dict[tp.Definition.Id] = pretty_param_name

# show UI form to pick parameters
# todo: clean this
instance_p_class = [ParameterOption(x, inst_param_dict) for x in inst_param_dict.keys()]
type_p_class = [ParameterOption(x, type_param_dict) for x in type_param_dict.keys()]
i_p_ops = sorted(instance_p_class, key=lambda x: x.name)
t_p_ops = sorted(type_p_class, key=lambda x: x.name)
ops = {"Type Parameters": t_p_ops, "Instance Parameters": i_p_ops}

# note: the selection will not actually be a parameter but either an Element Id or a BIP
selected_parameter = forms.SelectFromList.show(ops,
                                               button_name="Select Parameters",
                                               multiselect=False)

forms.alert_ifnot(selected_parameter, "No Parameters Selected", exitscript=True)

# get elements in current view
first_el = get_view_elements[0]

# {value of parameter : element id}
# need a nested dictionary
values_dict = defaultdict(list)

for el in get_view_elements:
    if selected_parameter in inst_param_dict.keys():
        el_parameter = el.get_Parameter(selected_parameter)
        if el_parameter:
            param_value = database.get_param_value_as_string(el_parameter)
            # values_dict[param_value] = []
            values_dict[param_value].append(el.Id)
    else:
        el_type = query.get_type(el)
        element_type_parameter = el_type.get_Parameter(selected_parameter)
        if element_type_parameter:
            param_value = database.get_param_value_as_string(element_type_parameter)
            values_dict[param_value].append(el.Id)

# colour dictionary
n = len(values_dict.keys())

if n < 14:
    colours = colorize.basic_colours()
else:
    colours = colorize.rainbow()
col_dict = colorize.polylinear_gradient(colours, n)
chop_col_list = col_dict["hex"][0:n]
# gradient method
revit_colours = [colorize.revit_colour(h) for h in chop_col_list]

for x in range(10):
    random.shuffle(revit_colours)

override_filters = 0

with revit.Transaction("Colorize by Value", doc):
    for param_value, c in zip(values_dict.keys(), revit_colours):

        override = DB.OverrideGraphicSettings()
        if "Projection Line Colour" in overrides_option:
            override.SetProjectionLineColor(c)
        if "Cut Line Colour" in overrides_option:
            override.SetCutLineColor(c)
        if "Projection Surface Colour" in overrides_option:
            override.SetSurfaceForegroundPatternColor(c)
            override.SetSurfaceForegroundPatternId(database.get_solid_fill_pat().Id)
        if "Cut Pattern Colour" in overrides_option:
            override.SetCutForegroundPatternColor(c)
            override.SetCutForegroundPatternId(database.get_solid_fill_pat().Id)
        for el_id in values_dict[param_value]:
            view.SetElementOverrides(el_id, override)
