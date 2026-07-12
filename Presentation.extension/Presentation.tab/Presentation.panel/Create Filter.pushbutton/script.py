# -*- coding: utf-8 -*-
import clr

clr.AddReference("System")
clr.AddReference("PresentationFramework")
clr.AddReference("PresentationCore")
clr.AddReference("WindowsBase")
clr.AddReference("RevitAPI")

from System.Collections.Generic import List
from System.Windows import MessageBox

from pyrevit import forms, revit, script
from Autodesk.Revit.DB import (
    BuiltInCategory,
    BuiltInParameter,
    Color as RevitColor,
    ElementId,
    ElementParameterFilter,
    FamilySymbol,
    FillPatternElement,
    FilteredElementCollector,
    FloorType,
    OverrideGraphicSettings,
    ParameterFilterElement,
    ParameterFilterRuleFactory,
    WallFoundationType,
    WallType,
)

doc = revit.doc
active_view = doc.ActiveView



CATEGORY_MAP = {
    "Structural Foundations": BuiltInCategory.OST_StructuralFoundation,
    "Structural Columns": BuiltInCategory.OST_StructuralColumns,
    "Structural Framing": BuiltInCategory.OST_StructuralFraming,
    "Walls": BuiltInCategory.OST_Walls,
}


def get_solid_fill_pattern_id(document):
    for pat in FilteredElementCollector(document).OfClass(FillPatternElement):
        fp = pat.GetFillPattern()
        if fp and fp.IsSolidFill:
            return pat.Id
    return ElementId.InvalidElementId


def hsv_to_rgb(h, s, v):
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    i = i % 6

    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    else:
        r, g, b = v, p, q

    return int(r * 255), int(g * 255), int(b * 255)


def generate_distinct_colors(count):
    result = []
    if count <= 0:
        return result

    for i in range(count):
        h = float(i) / float(count)
        r, g, b = hsv_to_rgb(h, 0.70, 0.90)
        result.append(RevitColor(r, g, b))

    return result


def get_existing_filter_names():
    return set(
        x.Name for x in FilteredElementCollector(doc).OfClass(ParameterFilterElement)
    )


def apply_filter_graphics(view, filter_id, color, solid_fill_id):
    ogs = OverrideGraphicSettings()

    try:
        ogs.SetProjectionLineColor(color)
    except:
        pass

    try:
        ogs.SetCutLineColor(color)
    except:
        pass

    try:
        ogs.SetSurfaceForegroundPatternColor(color)
        ogs.SetSurfaceForegroundPatternId(solid_fill_id)
    except:
        pass

    try:
        ogs.SetCutForegroundPatternColor(color)
        ogs.SetCutForegroundPatternId(solid_fill_id)
    except:
        pass

    existing_filters = list(view.GetFilters())
    if filter_id not in existing_filters:
        view.AddFilter(filter_id)

    view.SetFilterOverrides(filter_id, ogs)
    view.SetFilterVisibility(filter_id, True)


def get_type_name(elem_type):
    try:
        p = elem_type.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
        if p:
            s = p.AsString()
            if s:
                return s.strip()
    except:
        pass

    try:
        if elem_type.Name:
            return elem_type.Name.strip()
    except:
        pass

    return None


def get_family_name(sym):
    try:
        if sym.Family and sym.Family.Name:
            return sym.Family.Name.strip()
    except:
        pass
    return ""


def build_item(display_name, type_name):
    return {
        "display": display_name,
        "type_name": type_name
    }


def get_foundation_items():
    items = {}

    family_symbols = list(
        FilteredElementCollector(doc)
        .OfClass(FamilySymbol)
        .OfCategory(BuiltInCategory.OST_StructuralFoundation)
        .WhereElementIsElementType()
        .ToElements()
    )

    for sym in family_symbols:
        type_name = get_type_name(sym)
        family_name = get_family_name(sym)

        if type_name:
            display_name = "{} : {}".format(family_name, type_name) if family_name else type_name
            items[display_name] = build_item(display_name, type_name)

    floor_types = list(
        FilteredElementCollector(doc)
        .OfClass(FloorType)
        .WhereElementIsElementType()
        .ToElements()
    )

    for ft in floor_types:
        try:
            if ft.Category and ft.Category.Id.IntegerValue == int(BuiltInCategory.OST_StructuralFoundation):
                if ft.IsFoundationSlab:
                    type_name = get_type_name(ft)
                    if type_name:
                        display_name = "Foundation Slab : {}".format(type_name)
                        items[display_name] = build_item(display_name, type_name)
        except:
            pass

    wall_foundation_types = list(
        FilteredElementCollector(doc)
        .OfClass(WallFoundationType)
        .WhereElementIsElementType()
        .ToElements()
    )

    for wft in wall_foundation_types:
        try:
            if wft.Category and wft.Category.Id.IntegerValue == int(BuiltInCategory.OST_StructuralFoundation):
                type_name = get_type_name(wft)
                if type_name:
                    display_name = "Wall Foundation : {}".format(type_name)
                    items[display_name] = build_item(display_name, type_name)
        except:
            pass

    return [items[k] for k in sorted(items.keys())]


def get_column_items():
    items = {}

    column_symbols = list(
        FilteredElementCollector(doc)
        .OfClass(FamilySymbol)
        .OfCategory(BuiltInCategory.OST_StructuralColumns)
        .WhereElementIsElementType()
        .ToElements()
    )

    for sym in column_symbols:
        type_name = get_type_name(sym)
        family_name = get_family_name(sym)

        if type_name:
            display_name = "{} : {}".format(family_name, type_name) if family_name else type_name
            items[display_name] = build_item(display_name, type_name)

    return [items[k] for k in sorted(items.keys())]


def get_framing_items():
    items = {}

    framing_symbols = list(
        FilteredElementCollector(doc)
        .OfClass(FamilySymbol)
        .OfCategory(BuiltInCategory.OST_StructuralFraming)
        .WhereElementIsElementType()
        .ToElements()
    )

    for sym in framing_symbols:
        type_name = get_type_name(sym)
        family_name = get_family_name(sym)

        if type_name:
            display_name = "{} : {}".format(family_name, type_name) if family_name else type_name
            items[display_name] = build_item(display_name, type_name)

    return [items[k] for k in sorted(items.keys())]


def get_wall_items():
    items = {}

    wall_types = list(
        FilteredElementCollector(doc)
        .OfClass(WallType)
        .WhereElementIsElementType()
        .ToElements()
    )

    for wt in wall_types:
        try:
            if wt.Category and wt.Category.Id.IntegerValue == int(BuiltInCategory.OST_Walls):
                type_name = get_type_name(wt)
                if type_name:
                    display_name = "Wall : {}".format(type_name)
                    items[display_name] = build_item(display_name, type_name)
        except:
            pass

    return [items[k] for k in sorted(items.keys())]


def get_items_for_category(category_name):
    if category_name == "Structural Foundations":
        return get_foundation_items()
    elif category_name == "Structural Columns":
        return get_column_items()
    elif category_name == "Structural Framing":
        return get_framing_items()
    elif category_name == "Walls":
        return get_wall_items()
    return []


class FilterWindow(forms.WPFWindow):
    def __init__(self):
        forms.WPFWindow.__init__(self, script.get_bundle_file("ui.xaml"))
        self.items = []
        self.populate_categories()
        self.ParameterCombo.Items.Clear()
        self.ParameterCombo.Items.Add("Type Name")
        self.ParameterCombo.SelectedIndex = 0
        self.ParameterCombo.IsEnabled = False
        self.StatusText.Text = "Select category. All type names from that category will be listed."
        self.show_dialog()

    def populate_categories(self):
        self.CategoryCombo.Items.Clear()
        for name in sorted(CATEGORY_MAP.keys()):
            self.CategoryCombo.Items.Add(name)
        self.CategoryCombo.SelectedIndex = 0

    def category_changed(self, sender, args):
        self.load_names()

    def parameter_changed(self, sender, args):
        pass

    def close_window(self, sender, args):
        self.Close()

    def load_names(self):
        self.ValueList.Items.Clear()

        cname = self.CategoryCombo.SelectedItem
        self.items = get_items_for_category(cname)

        for item in self.items:
            self.ValueList.Items.Add(item["display"])

        self.StatusText.Text = "{} type names found in category.".format(len(self.items))


    def generate_filters(self, sender, args):
        cname = self.CategoryCombo.SelectedItem
        if not cname:
            MessageBox.Show("Please select a category.", "Generate Filters")
            return

        if not self.items:
            self.items = get_items_for_category(cname)

        if not self.items:
            MessageBox.Show("No type names found for selected category.", "Generate Filters")
            return

        display_map = {item["display"]: item for item in self.items}

        selected_displays = forms.SelectFromList.show(
            sorted(display_map.keys()),
            title="Select types for {}".format(cname),
            button_name="Create Filters",
            multiselect=True
        )

        if not selected_displays:
            MessageBox.Show("No types selected.", "Generate Filters")
            return

        selected_items = [display_map[x] for x in selected_displays]
        bic = CATEGORY_MAP[cname]

        existing_names = get_existing_filter_names()
        used_names_this_run = set()

        created_items = []
        skipped_duplicates = []
        failed = []

        for item in selected_items:
            filter_name = item["type_name"]

            if filter_name in existing_names or filter_name in used_names_this_run:
                skipped_duplicates.append(
                    "{} --> skipped because filter name already exists".format(filter_name)
                )
                continue

            created_items.append(item)
            used_names_this_run.add(filter_name)

        colors = generate_distinct_colors(len(created_items))
        solid_fill_id = get_solid_fill_pattern_id(doc)

        cat_ids = List[ElementId]()
        cat_ids.Add(ElementId(int(bic)))

        type_name_param_id = ElementId(BuiltInParameter.ALL_MODEL_TYPE_NAME)

        created = 0

        with revit.Transaction("Generate {} Filters".format(cname)):
            for i, item in enumerate(created_items):
                try:
                    rule = ParameterFilterRuleFactory.CreateEqualsRule(
                        type_name_param_id,
                        item["type_name"]
                    )
                    elem_filter = ElementParameterFilter(rule)

                    pf = ParameterFilterElement.Create(
                        doc,
                        item["type_name"],
                        cat_ids,
                        elem_filter
                    )

                    apply_filter_graphics(active_view, pf.Id, colors[i], solid_fill_id)
                    created += 1

                except Exception as ex:
                    failed.append("{} --> {}".format(item["display"], str(ex)))

        msg = "{} filters created.\n{} skipped duplicate names.\n{} failed.".format(
            created, len(skipped_duplicates), len(failed)
        )
        self.StatusText.Text = msg
        MessageBox.Show(msg, "Generate Filters")


FilterWindow()