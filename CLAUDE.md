# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

This is a Vue.js 3 application with Vite as the build tool and development server.

### Development Commands
- `npm run dev` - Start development server on http://localhost:3000
- `npm run build` - Build for production
- `npm run preview` - Preview production build

### Dependencies
- Vue 3.4.0
- Vue Router 4.2.0  
- Element Plus 2.4.0
- Element Plus Icons 2.3.0
- Vite 5.0.0 (build tool)
- Konva.js 9.2.0 (2D canvas library)
- vue-konva 3.0.2 (Vue wrapper for Konva.js)

### Project Structure
```
/
├── index.html              # Root HTML file
├── package.json            # Dependencies and scripts
├── vite.config.js          # Vite build configuration
├── src/
│   ├── app/
│   │   ├── index.html      # Legacy HTML (now unused)
│   │   ├── index.js        # Vue app entry point
│   │   └── app.vue         # Root component
│   ├── assets/style/       # CSS files
│   ├── components/         # Reusable components
│   ├── router/             # Vue Router configuration
│   └── views/              # Page components
├── Layouts/                # SVG analysis and conversion tools
│   ├── object.py           # Python SVG parser (legacy)
│   ├── *.svg               # Floor plan SVG files
│   ├── *_konva.json        # Converted JSON files for import
│   └── *.xlsx              # Generated reports
├── svg_to_konva.py         # SVG to Konva.js converter script
└── CLAUDE.md               # This file

## Application Architecture

### Data Storage
- Uses localStorage for data persistence
- No backend database - all data is stored in browser localStorage
- Data entities: regions, sites, floors, and floorPlans

### Core Components Structure

**Main App Structure:**
- `src/app/app.vue` - Root component with navigation header
- `src/app/index.js` - Application entry point, Vue 3 with Element Plus
- `src/router/index.js` - Vue Router configuration with hash history

**Views:**
- `src/views/dashboard/index.vue` - Statistics dashboard showing counts from localStorage
- `src/views/regions/index.vue` - Region management (CRUD operations)
- `src/views/sites/index.vue` - Data center sites management
- `src/views/floors/index.vue` - Floors/shelters management with grid system
- `src/views/floor-plan/index.vue` - Visual floor plan designer (complex drawing tool)

### Data Hierarchy
1. **Regions** - Top-level geographical groupings
2. **Sites** - Data centers within regions (Building, Shelter, or Building + Shelters)
3. **Floors** - Individual floors or shelters within sites
4. **Floor Plans** - Visual layouts with equipment placement

### Floor Plan Designer Features
The floor plan designer (`src/views/floor-plan/index.vue`) includes:
- **JSON Import System**: Import pre-converted floor plan data from SVG files
- **Konva.js Canvas**: High-performance 2D rendering with zoom, pan, and selection
- **Layer Management**: Toggle visibility of different element types
- **Interactive Elements**: Click, drag, and transform floor plan objects
- **Element Types**: Floor shape, structural elements, server racks, cooling units, cooling tiles, PDUs/PPCs
- **Accurate Rendering**: Preserves original SVG geometry including complex paths
- **Real-time Selection**: Transform handles for resize and rotation
- **Visual Hierarchy**: Proper layering with background floor shape and equipment overlays

## Key Technical Details

### Setup Instructions
1. **Install dependencies:** `npm install`
2. **Start development server:** `npm run dev`
3. **Build for production:** `npm run build`
4. **Preview production build:** `npm run preview`

### Floor Plan Workflow
1. **Convert SVG to JSON**: Use `svg_to_konva.py` to convert SVG files
2. **Import JSON**: Load converted files directly into the floor plan designer
3. **Interactive Editing**: Use Konva.js canvas for viewing and manipulating elements
4. **Layer Management**: Toggle visibility of different element types
5. **Save/Export**: Store modified floor plans in localStorage

### Build Configuration
- Uses Vite as build tool and dev server
- Vue SFC (Single File Component) support
- Hot module replacement in development
- Production builds to `/dist` directory
- Development server runs on port 3000 with auto-open

### Vue.js Features Used
- Vue 3 Composition API and Options API
- Vue Router with hash history mode
- Element Plus UI components and icons
- Scoped CSS in Vue components
- localStorage for data persistence
- vue-konva integration for 2D canvas rendering
- Reactive layer management and element properties

### Data Structure
- Grid dimensions calculated from column letters (AA, AB, AC...) and row numbers
- Power capacity tracking (DC and AC) in kilowatts
- Floor dimensions stored in centimeters with grid-based coordinate system

### SVG to JSON Conversion System

#### Primary Converter: `svg_to_konva.py`
A comprehensive Python script that converts SVG floor plans to Konva.js compatible JSON format:

**Features:**
- **100% Accurate Conversion**: Preserves exact geometry, transforms, and styling
- **Element Detection**: Automatically identifies and categorizes floor plan elements
- **Layer Organization**: Separates elements into logical layers for easy management
- **Complex Path Support**: Handles curved and irregular shapes (floor outlines, equipment)
- **Metadata Preservation**: Stores original SVG attributes and geometry data
- **Transform Handling**: Accurately processes SVG transforms (matrix, translate, scale, rotate)

**Detected Element Types:**
- **Floor Shape**: Building outline and boundaries (background layer)
- **Structural Elements**: Walls, columns, building framework
- **Server Racks**: Red and gray server equipment with rack identification
- **Cooling Units**: Wall/ceiling-mounted cooling equipment
- **Cooling Tiles**: Floor-mounted perforated tiles
- **PDUs/PPCs**: Power distribution units and power panel controllers
- **Individual Elements**: Standalone SVG elements not in groups

**Usage:**
```bash
python3 svg_to_konva.py "path/to/floor_plan.svg"
```

**Output:**
- Creates `*_konva.json` file with structured layer data
- Detailed conversion statistics and element counts
- Preserves visual fidelity and interactive functionality

#### Legacy Tool: `object.py`
Original SVG analysis tool for pattern recognition and Excel reporting:
- Identifies cooling tiles, server racks, cooling units, columns, PDUs, walls, doors
- Exports to SVG and Excel formats for pattern analysis
- Used for understanding SVG structure and developing conversion algorithms

### SVG Structure Analysis (MLQ2 G.F - Power.svg)

The SVG file represents a data center floor plan with the following structure:

#### Overall Structure
- **Generated by:** Schneider Electric with Batik SVG Generator
- **Dimensions:** 3660 x 1417 pixels
- **Base transform:** All elements use `transform="matrix(1,0,0,1,98,-84)"` for consistent positioning

#### Grid System
- **Column Labels:** AA, AB, AC, AD... through DR (double-letter format)
- **Row Labels:** 01, 02, 03... through 34 (zero-padded numbers)
- **Grid Spacing:** Approximately 36 pixels between grid lines
- **Coordinate System:** Bottom-left origin with row numbers increasing upward

#### Element Types and Patterns

**1. Customer Zones/Cages (Blue highlighted areas)**
- **Color:** `rgb(0,120,215)` with 0.0784 opacity
- **Pattern:** Rectangular `<path>` elements defining cage boundaries
- **Labels:** Company names (BME, MUFG, NBE, Bloomberg, TAHAKUM, etc.)
- **Specifications:** Power consumption in kW and area in m²

**2. Structural Elements (Silver dashed lines)**
- **Color:** Silver with `stroke-dasharray="18,9"` and `stroke-width="2"`
- **Purpose:** Defines structural walls, boundaries, and separations
- **Pattern:** Complex path definitions outlining building structure

**3. Columns/Structural Support (Beige/tan colored)**
- **Color:** `rgb(224,224,215)` with 0.4 opacity
- **Pattern:** Vertical rectangular elements representing building columns
- **Labels:** Column identifiers (Row, AH, etc.)

**4. Equipment Objects (Colored rectangles with borders)**
- **Pattern:** Rectangular elements with colored fills and stroke outlines
- **Colors:** 
  - Pink/Red: `rgb(255,196,196)` - Likely cooling or mechanical equipment
  - Blue: `rgb(171,211,241)` - Power distribution units or electrical equipment
  - Red: `rgb(244,145,145)` - Emergency or fire safety equipment
- **Borders:** 3px width strokes in gray (`rgb(110,110,110)`) or specific colors

**5. Rotated Elements**
- **Pattern:** Uses `transform="translate(x,y) rotate(angle) translate(-x,-y)"` for rotated equipment
- **Common rotations:** 90°, 270° for equipment orientation

#### Text Elements
- **Font families:** Tahoma (main labels), Segoe UI (equipment text)
- **Font sizes:** 15px (general), 20px (grid labels), 23px (large labels)
- **Grid labels:** Positioned at consistent intervals for navigation
- **Equipment labels:** Include power ratings (kW) and area measurements (m²)

#### Key Observations for Application Development
- Customer zones are defined by blue-filled rectangular paths
- Equipment is represented by colored rectangles with consistent stroke patterns
- Grid system provides spatial reference for all elements
- Power and space data is embedded in text elements adjacent to zones
- Transform matrices provide consistent coordinate system
- Equipment orientation is handled through rotation transforms

#### Modern Approach: Automated Conversion

The `svg_to_konva.py` script automates all SVG parsing and object detection:

**Python-based Detection (Recommended)**
```python
# Element detection functions
def is_server_rack(element) -> Optional[str]:  # Returns 'red' or 'gray'
def is_cooling_unit(element) -> bool:
def is_cooling_tile(element) -> bool:
def is_pdu_or_ppc(element) -> bool:
def is_structural_element(element) -> bool:
def is_floor_shape(element) -> bool:

# Automatic conversion with 100% accuracy
result = parse_svg_to_konva("floor_plan.svg")
```

**Element Identification Patterns:**
- **Server Racks**: Groups with red (`rgb(230,0,0)`) or gray (`rgb(110,110,110)`) fills containing line and path elements
- **Cooling Units**: Blue groups (`rgb(62,153,223)`, `rgb(171,211,241)`) with specific geometric patterns
- **Cooling Tiles**: Path elements with 30-50 curve commands indicating circular dot patterns
- **Floor Shape**: Large silver-filled groups with complex paths (>200 chars, coordinates >1000)
- **Structural Elements**: Silver elements with base transform `matrix(1,0,0,1,98,-84)`
- **PDUs/PPCs**: Green groups (`rgb(103,203,51)`, `rgb(189,232,167)`) with line and path children

**Transform Handling:**
```python
# Comprehensive transform parsing
def extract_all_transforms(transform_str):
    # Handles matrix, translate, scale, rotate
    # Returns normalized transform object

def apply_transform_to_point(x, y, transforms):
    # Applies transform chain to coordinates
    # Maintains positioning accuracy
```

**Geometry Preservation:**
```python
# Complete shape data extraction
def get_svg_element_geometry(element):
    # Extracts all child shapes (paths, lines, rects, circles, text)
    # Preserves original SVG data for complex rendering
    # Returns structured geometry metadata
```

#### Legacy JavaScript Approach (Deprecated)

The original client-side parsing approach has been replaced by the Python converter for better accuracy and performance. The JavaScript patterns above are preserved for reference but are no longer recommended for production use.

## Development Notes

### Working with localStorage
All data persistence uses localStorage with these keys:
- `regions` - Array of region objects
- `sites` - Array of site objects  
- `floors` - Array of floor objects
- `floorPlans` - Object with floor IDs as keys containing Konva.js stage data

### Floor Plan Data Structure
Floor plans are stored in localStorage as Konva.js stage JSON:
```javascript
// Example floorPlans entry
{
  "floor_123": {
    "konvaData": "{...}",  // Konva stage JSON
    "lastModified": "2024-01-15T10:30:00.000Z",
    "elementCount": 150,
    "layers": {
      "floor_shape": true,
      "structural": true,
      "server_racks": true,
      "cooling_units": true,
      "cooling_tiles": false,
      "pdu_ppc": true
    }
  }
}
```

### Grid System
- Default grid size: 60cm
- Column format: AA, AB, AC, AD... (double letters only)
- Row format: 01, 02, 03... (zero-padded numbers)
- Dimensions calculated as: columns × grid_size and rows × grid_size

### Navigation
- Hash-based routing (createWebHashHistory)
- Main nav: Dashboard, Regions, Data Centers, Floors/Shelters
- Floor plan accessible via "Floor Plan" button in floors table

## Common Development Tasks

### Running the Application
```bash
# First time setup
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Working with Floor Plans

#### Converting SVG Files
```bash
# Convert a single SVG file
python3 svg_to_konva.py "Layouts/floor_plan.svg"

# Output will be: Layouts/floor_plan_konva.json
```

#### Importing Floor Plans
1. Convert SVG using the Python script
2. Open the floor plan designer in the application
3. Click "Import JSON" and select the generated `*_konva.json` file
4. Use layer controls to show/hide different element types
5. Interact with elements using mouse (click, drag, transform)

#### Understanding the JSON Structure
```json
{
  "version": "1.0",
  "source_file": "floor_plan.svg",
  "layers": {
    "floor_shape": { /* Single background shape */ },
    "structural": [ /* Building elements */ ],
    "server_racks": [ /* Server equipment */ ],
    "cooling_units": [ /* Cooling equipment */ ],
    "cooling_tiles": [ /* Floor tiles */ ],
    "pdu_ppc": [ /* Power equipment */ ],
    "other": [ /* Miscellaneous elements */ ]
  },
  "metadata": {
    "total_elements": 150,
    "conversion_accuracy": "100%",
    /* SVG attributes and geometry data */
  }
}
```

### Adding New Features
1. Create new Vue components in `src/components/` or `src/views/`
2. Update router configuration in `src/router/index.js` for new pages
3. Use Element Plus components for consistent UI
4. Store data in localStorage following existing patterns
5. For floor plan features, extend Konva.js elements and layer management
6. Update SVG converter for new element types if needed

### Troubleshooting
- **Import errors:** Ensure all imports use `.vue` extension for Vue components
- **Build errors:** Check that all dependencies are installed with `npm install`
- **Routing issues:** Verify routes are properly configured in `src/router/index.js`
- **Missing icons:** Import icons from `@element-plus/icons-vue` in `src/app/index.js`
- **Konva.js issues:** Check that vue-konva is properly imported and stage/layer refs are valid
- **JSON import errors:** Verify JSON file structure matches expected format from `svg_to_konva.py`
- **Canvas performance:** For large floor plans, consider using Konva's `perfectDrawEnabled: false`
- **Python conversion errors:** Ensure Python script has access to SVG file and write permissions for output

### Floor Plan Specific Issues
- **Elements not visible:** Check layer visibility toggles and opacity settings
- **Incorrect positioning:** Verify SVG transform parsing in Python converter
- **Missing complex shapes:** Ensure path data is preserved in geometry metadata
- **Poor performance:** Consider limiting visible layers or using Konva's optimization features
- **Selection not working:** Check that elements have `listening: true` and proper event handlers