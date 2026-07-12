# revit-filter-legend-automation
Revit plugin to batch-create filters and auto-generate legends for structural elements
# Revit Filter & Legend Toolkit

A pyRevit extension that automates color-coded presentation drawings — batch-create view filters with color overrides, then auto-generate a matching legend, in seconds instead of hours.

## Preview

![Color-coded foundation plan sample](assets/sample_foundation_plan_color_legend.svg)

*Sample illustrative output — actual results depend on your model's element types and view.*

## Overview

Manually building presentation drawings in Revit means creating a separate filter for every element type, overriding colors one by one, and then hand-placing legend swatches to match. It's repetitive, error-prone, and has to be redone every time a type changes.

This toolkit replaces that entire manual workflow with two one-click tools.

## Tools

### 🎨 Create Filter
Batch-creates view filters and applies color overrides for every element type in the active view — foundations, columns, walls — using a fixed color palette so results stay consistent across sheets.

### 🏷️ Legend from Filters
Builds a matching legend directly from the filters created above, using `FilledRegion` and `TextNote` elements placed in a dedicated Legend view. Uses a clear-and-rebuild pattern, so re-running it keeps the legend in sync as filters or types change.

## Why this exists

- **Hours → minutes** — no more creating filters one type at a time
- **Consistency** — every sheet gets the same colors, every time
- **Fewer errors** — mismatched or missing types stand out instantly instead of hiding in a schedule
- **Faster reviews** — clients, GCs, and reviewers read a colored drawing in seconds
- **Scales with the model** — works the same at 20 elements or 2,000

## Requirements

- Autodesk Revit (2021+ recommended)
- [pyRevit](https://www.pyrevitlabs.io/) installed
- Python (bundled with pyRevit — no separate install needed)

## Installation

1. Clone or download this repository:
   ```bash
   git clone https://github.com/shubhamddhage/revit-filter-legend-automation.git
   ```
2. Open pyRevit's extension manager (**pyRevit tab → Extensions**), or manually copy the `.extension` folder into your pyRevit extensions directory.
3. Reload pyRevit (**pyRevit tab → Reload**, or restart Revit).
4. The **Presentation** panel will appear on the ribbon with both tools.

## Usage

1. Open the view you want to color-code (e.g., a foundation plan).
2. Click **Create Filter** — filters and color overrides are applied automatically based on element type.
3. Click **Legend from Filters** — a legend matching your filters is built in the project's Legend view.
4. Place the legend on your sheet as usual.

## Project Structure

```
Presentation.extension/
├── Presentation.tab/
│   └── Presentation.panel/
│       ├── Create Filter.pushbutton/
│       │   ├── script.py
│       │   ├── ui.xaml
│       │   ├── bundle.yaml
│       │   └─  icon.png
│       └── Legendfromfilters.pushbutton/
│           ├── script.py
│           ├──bundle.yaml
│           └── icon.png
├── assets/
│   └── sample_foundation_plan_color_legend.svg
├── README.md
└── .gitignore
```

## Roadmap

- [ ] Configurable color palette (currently fixed)
- [ ] Support for additional categories beyond foundations/columns/walls
- [ ] Batch mode across multiple views/sheets

## License

MIT License — free to use, modify, and share.

## Author

Built by **Shubham** — BIM Engineer specializing in structural Revit workflows and Revit API automation.
