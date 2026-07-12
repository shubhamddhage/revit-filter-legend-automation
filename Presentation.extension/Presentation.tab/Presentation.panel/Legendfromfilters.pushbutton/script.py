# -*- coding: utf-8 -*-
import clr

clr.AddReference("System")
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")

from System.Collections.Generic import List
from pyrevit import revit, forms
from Autodesk.Revit.DB import (
    BuiltInCategory,
    BuiltInParameter,
    Color as RevitColor,
    CurveLoop,
    ElementId,
    FillPatternElement,
    FilledRegion,
    FilledRegionType,
    FilteredElementCollector,
    Line,
    OverrideGraphicSettings,
    TextNote,
    TextNoteType,
    TextNoteOptions,
    HorizontalTextAlignment,
    View,
    ViewDuplicateOption,
    ViewType,
    XYZ,
)

doc = revit.doc


def get_all_candidate_views():
    views = []
    for v in FilteredElementCollector(doc).OfClass(View).ToElements():
        try:
            if v.IsTemplate:
                continue
            if v.ViewType in [
                ViewType.FloorPlan,
                ViewType.CeilingPlan,
                ViewType.EngineeringPlan,
                ViewType.AreaPlan,
                ViewType.Section,
                ViewType.Elevation,
                ViewType.Detail,
                ViewType.ThreeD,
                ViewType.DraftingView,
            ]:
                views.append(v)
        except:
            pass
    return sorted(views, key=lambda x: x.Name)


def get_all_legends():
    legends = []
    for v in FilteredElementCollector(doc).OfClass(View).ToElements():
        try:
            if v.ViewType == ViewType.Legend:
                legends.append(v)
        except:
            pass
    return sorted(legends, key=lambda x: x.Name)


def ensure_legend_exists():
    legends = get_all_legends()
    if not legends:
        forms.alert("No legend exists in this project.\nCreate at least one legend manually first.", exitscript=True)
    return legends


def get_first_filled_region_type_id():
    frt = FilteredElementCollector(doc).OfClass(FilledRegionType).FirstElement()
    if frt:
        return frt.Id
    return ElementId.InvalidElementId


def get_solid_fill_pattern_id():
    patterns = FilteredElementCollector(doc).OfClass(FillPatternElement).ToElements()
    for pat in patterns:
        try:
            fp = pat.GetFillPattern()
            if fp and fp.IsSolidFill:
                return pat.Id
        except:
            pass
    return ElementId.InvalidElementId


def get_text_type_id_by_size(target_size_feet, tolerance=1e-6):
    text_types = FilteredElementCollector(doc).OfClass(TextNoteType).ToElements()
    for t in text_types:
        try:
            p = t.get_Parameter(BuiltInParameter.TEXT_SIZE)
            if not p:
                continue
            size_val = p.AsDouble()
            if abs(size_val - target_size_feet) <= tolerance:
                return t.Id
        except:
            pass
    return ElementId.InvalidElementId


def make_curve_loop(x, y, w, h):
    p1 = XYZ(x, y, 0)
    p2 = XYZ(x + w, y, 0)
    p3 = XYZ(x + w, y + h, 0)
    p4 = XYZ(x, y + h, 0)

    loop = CurveLoop()
    loop.Append(Line.CreateBound(p1, p2))
    loop.Append(Line.CreateBound(p2, p3))
    loop.Append(Line.CreateBound(p3, p4))
    loop.Append(Line.CreateBound(p4, p1))

    loops = List[CurveLoop]()
    loops.Add(loop)
    return loops


def duplicate_legend(base_legend, new_name):
    if not base_legend.CanViewBeDuplicated(ViewDuplicateOption.Duplicate):
        forms.alert("Selected legend can not be duplicated.", exitscript=True)

    new_view_id = base_legend.Duplicate(ViewDuplicateOption.Duplicate)
    new_legend = doc.GetElement(new_view_id)
    new_legend.Name = new_name
    return new_legend


def clear_view_detail_items(view_id):
    collector = FilteredElementCollector(doc, view_id).WhereElementIsNotElementType()
    to_delete = List[ElementId]()

    for el in collector:
        try:
            if el.Category:
                cat_id = el.Category.Id.IntegerValue
                if cat_id in [
                    int(BuiltInCategory.OST_TextNotes),
                    int(BuiltInCategory.OST_DetailComponents),
                    int(BuiltInCategory.OST_DetailLines),
                    int(BuiltInCategory.OST_FilledRegion),
                    int(BuiltInCategory.OST_Lines),
                    int(BuiltInCategory.OST_GenericAnnotation),
                ]:
                    to_delete.Add(el.Id)
        except:
            pass

    if to_delete.Count > 0:
        doc.Delete(to_delete)


def get_filter_display_data(view):
    rows = []
    try:
        filter_ids = list(view.GetFilters())
    except:
        filter_ids = []

    for fid in filter_ids:
        try:
            visible = view.GetFilterVisibility(fid)
        except:
            visible = True

        if not visible:
            continue

        f = doc.GetElement(fid)
        if not f:
            continue

        try:
            ogs = view.GetFilterOverrides(fid)
        except:
            ogs = None

        color = None
        if ogs:
            try:
                c = ogs.SurfaceForegroundPatternColor
                if c and (c.Red != 0 or c.Green != 0 or c.Blue != 0):
                    color = c
            except:
                pass
            if color is None:
                try:
                    c = ogs.CutForegroundPatternColor
                    if c and (c.Red != 0 or c.Green != 0 or c.Blue != 0):
                        color = c
                except:
                    pass
            if color is None:
                try:
                    c = ogs.ProjectionLineColor
                    if c and (c.Red != 0 or c.Green != 0 or c.Blue != 0):
                        color = c
                except:
                    pass

        if color is None:
            color = RevitColor(0, 0, 0)

        rows.append({
            "filter_id": fid,
            "filter_name": f.Name,
            "color": color
        })

    return sorted(rows, key=lambda x: x["filter_name"].lower())


def set_region_color_override(region, color, solid_fill_id):
    try:
        ogs = OverrideGraphicSettings()
        ogs.SetSurfaceForegroundPatternId(solid_fill_id)
        ogs.SetSurfaceForegroundPatternColor(color)
        ogs.SetCutForegroundPatternId(solid_fill_id)
        ogs.SetCutForegroundPatternColor(color)
        owner_view = doc.GetElement(region.OwnerViewId)
        owner_view.SetElementOverrides(region.Id, ogs)
    except:
        pass


candidate_views = get_all_candidate_views()
if not candidate_views:
    forms.alert("No eligible views found in project.", exitscript=True)

view_name_map = {v.Name: v for v in candidate_views}
selected_view_name = forms.SelectFromList.show(
    sorted(view_name_map.keys()),
    title="Select Source View",
    button_name="Use View",
    multiselect=False
)

if not selected_view_name:
    forms.alert("No source view selected.", exitscript=True)

source_view = view_name_map[selected_view_name]

filter_rows = get_filter_display_data(source_view)
if not filter_rows:
    forms.alert("Selected view has no visible applied filters.", exitscript=True)

filter_map = {row["filter_name"]: row for row in filter_rows}

selected_filter_names = forms.SelectFromList.show(
    sorted(filter_map.keys()),
    title="Select Filters For Legend",
    button_name="Create Legend",
    multiselect=True
)

if not selected_filter_names:
    forms.alert("No filters selected.", exitscript=True)

filter_rows = [filter_map[name] for name in selected_filter_names]

legends = ensure_legend_exists()
legend_name_map = {v.Name: v for v in legends}

selected_legend_name = forms.SelectFromList.show(
    sorted(legend_name_map.keys()),
    title="Select Base Legend To Duplicate",
    button_name="Use Legend",
    multiselect=False
)

if not selected_legend_name:
    forms.alert("No base legend selected.", exitscript=True)

base_legend = legend_name_map[selected_legend_name]

default_legend_name = "LEGEND - {}".format(source_view.Name)
new_legend_name = forms.ask_for_string(
    default=default_legend_name,
    prompt="Enter new legend name:",
    title="Legend Name"
)

if not new_legend_name:
    forms.alert("No legend name entered.", exitscript=True)

text_size_1_16 = (1.0 / 16.0) / 12.0
text_type_id = get_text_type_id_by_size(text_size_1_16)
region_type_id = get_first_filled_region_type_id()
solid_fill_id = get_solid_fill_pattern_id()

if text_type_id == ElementId.InvalidElementId:
    forms.alert('No TextNoteType with size 1/16" found in project.', exitscript=True)

if region_type_id == ElementId.InvalidElementId:
    forms.alert("No FilledRegionType found in project.", exitscript=True)

if solid_fill_id == ElementId.InvalidElementId:
    forms.alert("No Solid Fill pattern found in project.", exitscript=True)

with revit.Transaction("Create Filter Legend"):
    new_legend = duplicate_legend(base_legend, new_legend_name)
    clear_view_detail_items(new_legend.Id)

    swatch_size = (1.0 / 8.0) / 12.0
    start_x = 0.0
    start_y = 0.0
    text_offset_x = 0.018
    row_gap = 0.030

    text_options = TextNoteOptions(text_type_id)
    text_options.HorizontalAlignment = HorizontalTextAlignment.Left

    for i, row in enumerate(filter_rows):
        y = start_y - (i * row_gap)

        loops = make_curve_loop(start_x, y, swatch_size, swatch_size)
        region = FilledRegion.Create(doc, region_type_id, new_legend.Id, loops)
        set_region_color_override(region, row["color"], solid_fill_id)

        text_pt = XYZ(
            start_x + swatch_size + text_offset_x,
            y + swatch_size - 0.0015,
            0
        )

        TextNote.Create(
            doc,
            new_legend.Id,
            text_pt,
            row["filter_name"],
            text_options
        )

forms.alert(
    "Legend created successfully.\n\nSource View: {}\nLegend Name: {}\nRows Created: {}".format(
        source_view.Name,
        new_legend_name,
        len(filter_rows)
    ),
    title="Legend From Filters"
)