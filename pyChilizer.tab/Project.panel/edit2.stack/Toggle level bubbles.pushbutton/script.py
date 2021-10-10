"""Toggle level bubbles in View."""

__title__ = 'Toggle\nLevels'

#import libraries and reference the RevitAPI and RevitAPIUI

from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Architecture import *
from Autodesk.Revit.DB.Analysis import *
from Autodesk.Revit.UI import *

from pyrevit import revit, DB, UI
from pyrevit import forms

#set the active Revit application and document
app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
active_view = doc.ActiveView

sel = revit.get_selection()

try:
    while True:
        level = doc.GetElement(revit.uidoc.Selection.PickObject(UI.Selection.ObjectType.Element, 'Pick a Level'))

        end_0 = level.IsBubbleVisibleInView(DB.DatumEnds.End0, active_view)
        end_1 = level.IsBubbleVisibleInView(DB.DatumEnds.End1, active_view)

        with revit.Transaction('Toggle grid'):
            if end_0 and end_1:
                level.HideBubbleInView(DB.DatumEnds.End1, active_view)
            elif end_0 and not end_1:
                level.HideBubbleInView(DB.DatumEnds.End0, active_view)
            elif not end_0 and not end_1:
                level.ShowBubbleInView(DB.DatumEnds.End1, active_view)
            else:
                level.ShowBubbleInView(DB.DatumEnds.End0, active_view)


except Exception as e:
    pass

