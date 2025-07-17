# White Space Management - DCIM Floor Plan System

A modern Data Center Infrastructure Management (DCIM) floor plan visualization and management system built with Vue.js and Konva.js.

## Features

- 🏢 **Interactive Floor Plan Designer** - Visual floor plan management with drag-and-drop functionality
- 🎨 **SVG to Konva.js Conversion** - Import existing floor plans from SVG files
- 📊 **Layer-based Visualization** - Toggle visibility of different equipment types
- 🖥️ **Equipment Management** - Track server racks, cooling units, PDUs, and more
- 💾 **Local Storage Persistence** - No backend required, all data stored locally
- 🔍 **Zoom & Pan Controls** - Navigate large floor plans with ease
- 📐 **Grid-based Coordinate System** - Precise equipment placement

## Tech Stack

- **Frontend Framework**: Vue.js 3.4.0
- **Build Tool**: Vite 5.0.0
- **UI Components**: Element Plus 2.4.0
- **Canvas Rendering**: Konva.js 9.2.0 (via vue-konva 3.0.2)
- **Routing**: Vue Router 4.2.0
- **SVG Conversion**: Python script with XML parsing

## Project Structure

```
white-space-management/
├── src/
│   ├── app/           # Vue application entry point
│   ├── assets/        # CSS and static assets
│   ├── components/    # Reusable Vue components
│   ├── router/        # Vue Router configuration
│   └── views/         # Page components
├── Layouts/           # SVG floor plans and conversion tools
├── svg_to_konva.py    # SVG to JSON converter
├── package.json       # NPM dependencies
├── vite.config.js     # Vite configuration
└── CLAUDE.md          # Development documentation
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/anauwal2/white-space-management.git
cd white-space-management
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Usage

### Converting SVG Floor Plans

1. Place your SVG floor plan in the `Layouts/` directory
2. Run the conversion script:
```bash
python3 svg_to_konva.py "Layouts/your-floor-plan.svg"
```
3. This creates a `*_konva.json` file ready for import

### Using the Floor Plan Designer

1. Navigate to a floor in the application
2. Click "Floor Plan" to open the designer
3. Use "Import JSON" to load a converted floor plan
4. Toggle layers to show/hide different equipment types:
   - Floor Shape (background)
   - Server Racks (red and gray)
   - Cooling Units (blue)
   - Cooling Tiles (perforated floor tiles)
   - PDUs/PPCs (green power units)

### Data Hierarchy

```
Regions
  └── Sites (Data Centers)
       └── Floors/Shelters
            └── Floor Plans (Visual Layouts)
```

## Equipment Types

- **Server Racks**: IT equipment racks (red = active, gray = passive)
- **Cooling Units**: Wall/ceiling-mounted cooling equipment
- **Cooling Tiles**: Perforated floor tiles for airflow
- **PDUs/PPCs**: Power Distribution Units and Power Panel Controllers

## Development

### Build for Production
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

### Adding New Features

1. Vue components go in `src/components/` or `src/views/`
2. Update router in `src/router/index.js` for new pages
3. Use Element Plus components for consistent UI
4. Follow existing localStorage patterns for data persistence

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is proprietary software. All rights reserved.

## Acknowledgments

- Built with Vue.js and Element Plus
- Canvas rendering powered by Konva.js
- SVG parsing capabilities for floor plan import