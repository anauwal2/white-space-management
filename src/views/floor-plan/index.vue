<template>
  <div class="floor-plan-page">
    <div class="page-header">
      <h2>{{ siteName }} - {{ floorName }}</h2>
      <div class="header-actions">
        <el-button @click="$router.back()">
          <el-icon><Back /></el-icon>
          Back
        </el-button>
        <el-button type="primary" @click="triggerSVGInput">
          <el-icon><DocumentAdd /></el-icon>
          Import SVG
        </el-button>
        <el-button type="success" @click="saveFloorPlan">
          <el-icon><Check /></el-icon>
          Save Plan
        </el-button>
      </div>
    </div>

    <div class="designer-container">
      <div class="canvas-container">
        <div 
          ref="svgContainer" 
          class="svg-canvas"
          @wheel="handleWheel"
        ></div>
      </div>
      
      <div class="controls-panel">
        <el-card class="controls-card">
          <template #header>
            <span>Import Controls</span>
          </template>
          
          <div class="control-group">
            <el-button @click="triggerSVGInput" type="primary">
              <el-icon><DocumentAdd /></el-icon>
              Select SVG File
            </el-button>
            <input 
              ref="svgFileInput" 
              type="file" 
              accept=".svg" 
              @change="handleSVGImport" 
              style="display: none"
            />
          </div>

          <div class="control-group">
            <el-button @click="clearCanvas" type="danger">
              <el-icon><Delete /></el-icon>
              Clear Canvas
            </el-button>
          </div>

          <div class="control-group">
            <el-checkbox v-model="dragEnabled" @change="toggleDragMode">
              Enable Drag Mode
            </el-checkbox>
            <el-text tag="small" v-if="!dragEnabled">
              Drag mode disabled - elements cannot be moved
            </el-text>
            <el-text tag="small" v-else>
              Drag mode enabled - click and drag elements to move them
            </el-text>
          </div>

          <div class="control-group">
            <label>Layer Controls:</label>
            <div class="layer-controls">
              <el-checkbox v-model="layerVisibility['floor-shape']" @change="toggleLayer('floor-shape')">
                Floor Shape
              </el-checkbox>
              <el-checkbox v-model="layerVisibility['customer-zones']" @change="toggleLayer('customer-zones')">
                Customer Zones
              </el-checkbox>
              <el-checkbox v-model="layerVisibility['server-racks']" @change="toggleLayer('server-racks')">
                Server Racks
              </el-checkbox>
              <el-checkbox v-model="layerVisibility['cooling-units']" @change="toggleLayer('cooling-units')">
                Cooling Units
              </el-checkbox>
              <el-checkbox v-model="layerVisibility['cooling-tiles']" @change="toggleLayer('cooling-tiles')">
                Cooling Tiles
              </el-checkbox>
              <el-checkbox v-model="layerVisibility['pdu-ppc']" @change="toggleLayer('pdu-ppc')">
                PDUs/PPCs
              </el-checkbox>
              <el-checkbox v-model="layerVisibility['other']" @change="toggleLayer('other')">
                Other Elements
              </el-checkbox>
              <el-checkbox v-model="layerVisibility['grid']" @change="toggleLayer('grid')">
                Grid & Coordinates
              </el-checkbox>
            </div>
          </div>

          <div class="control-group">
            <el-text tag="small">
              Objects: {{ objectCount }}
            </el-text>
          </div>

          <div class="control-group">
            <el-text tag="small">
              Status: {{ importStatus }}
            </el-text>
          </div>

          <div class="control-group">
            <label>Zoom:</label>
            <el-button-group>
              <el-button size="small" @click="zoomIn">+</el-button>
              <el-button size="small" @click="zoomOut">-</el-button>
              <el-button size="small" @click="resetZoom">Reset</el-button>
              <el-button size="small" @click="fitToScreen">Fit</el-button>
            </el-button-group>
            <div class="zoom-info">{{ Math.round(zoomLevel * 100) }}%</div>
          </div>
        </el-card>

        <el-card class="controls-card">
          <template #header>
            <span>Object Properties</span>
          </template>
          
          <div v-if="selectedObject" class="object-properties">
            <div class="property-item">
              <label>Type:</label>
              <span>{{ selectedObject.type }}</span>
            </div>
            <div class="property-item">
              <label>ID:</label>
              <span>{{ selectedObject.id }}</span>
            </div>
            <div class="property-item">
              <label>Position:</label>
              <span>{{ selectedObject.x }}, {{ selectedObject.y }}</span>
            </div>
            <div class="property-item">
              <label>Size:</label>
              <span>{{ selectedObject.width }} × {{ selectedObject.height }}</span>
            </div>
            <div class="property-item" v-if="selectedObject.transform">
              <label>Transform:</label>
              <span>{{ selectedObject.transform }}</span>
            </div>
          </div>
          <div v-else class="no-selection">
            <el-text tag="small">No object selected</el-text>
            <el-text tag="small">Use mouse wheel to zoom</el-text>
            <el-text tag="small">Drag to pan</el-text>
            <el-text tag="small">Click elements to select</el-text>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { SVG } from '@svgdotjs/svg.js'
import '@svgdotjs/svg.panzoom.js'
import '@svgdotjs/svg.draggable.js'

const DEFAULT_VIEWBOX = { width: 3660, height: 1417 }
const ZOOM_CONFIG = {
  min: 0.1,
  max: 10,
  factor: 0.1,
  step: 1.2
}
const GRID_OFFSET = { x: 13, y: -14 }
const COORDINATE_TRANSFORM = { x: 0, y: 0 }

const LAYER_TYPES = {
  FLOOR_SHAPE: 'floor-shape',
  CUSTOMER_ZONES: 'customer-zones',
  SERVER_RACKS: 'server-racks',
  COOLING_UNITS: 'cooling-units',
  COOLING_TILES: 'cooling-tiles',
  PDU_PPC: 'pdu-ppc',
  OTHER: 'other',
  GRID: 'grid'
}

const ELEMENT_COLORS = {
  SILVER: 'silver',
  BLUE_ZONE: 'rgb(0,120,215)',
  GRAY_RACK: 'rgb(110,110,110)',
  RED_RACK: 'rgb(230,0,0)',
  BLUE_COOLING: 'rgb(62,153,223)',
  LIGHT_BLUE_COOLING: 'rgb(171,211,241)',
  GREEN_PDU: 'rgb(103,203,51)',
  LIGHT_GREEN_PDU: 'rgb(189,232,167)'
}

export default {
  name: 'FloorPlan',
  setup() {
    const route = useRoute()
    
    // Refs
    const svgContainer = ref(null)
    const svgFileInput = ref(null)
    const objectCount = ref(0)
    const selectedObject = ref(null)
    const siteName = ref('')
    const floorName = ref('')
    const importStatus = ref('Ready')
    const zoomLevel = ref(1)
    
    // Layer visibility state
    const layerVisibility = ref({
      [LAYER_TYPES.FLOOR_SHAPE]: true,
      [LAYER_TYPES.CUSTOMER_ZONES]: true,
      [LAYER_TYPES.SERVER_RACKS]: true,
      [LAYER_TYPES.COOLING_UNITS]: true,
      [LAYER_TYPES.COOLING_TILES]: true,
      [LAYER_TYPES.PDU_PPC]: true,
      [LAYER_TYPES.OTHER]: true,
      [LAYER_TYPES.GRID]: true
    })
    const dragEnabled = ref(true)
    
    // Internal state
    let svgDraw = null
    let originalSVGContent = null
    let layerGroups = {}
    let selectedElement = null
    let gridLayer = null
    let coordinateLabels = {
      top: [],
      bottom: [],
      left: [],
      right: []
    }
    let gridOffset = { x: 0, y: 0 }
    
    const initSVGCanvas = () => {
      nextTick(() => {
        if (svgContainer.value) {
          svgDraw = SVG().addTo(svgContainer.value).size('100%', '100%')
          svgDraw.viewbox(0, 0, DEFAULT_VIEWBOX.width, DEFAULT_VIEWBOX.height)
          
          svgDraw.panZoom({
            zoomMin: ZOOM_CONFIG.min,
            zoomMax: ZOOM_CONFIG.max,
            zoomFactor: ZOOM_CONFIG.factor
          })
        }
      })
    }

    const triggerSVGInput = () => {
      svgFileInput.value?.click()
    }

    const handleSVGImport = (event) => {
      const file = event.target.files[0]
      if (!isValidSVGFile(file)) {
        ElMessage.error('Please select a valid SVG file')
        return
      }

      importStatus.value = 'Reading SVG file...'
      
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          parseSVGContent(e.target.result)
        } catch (error) {
          console.error('Error parsing SVG:', error)
          ElMessage.error('Failed to parse SVG file')
          importStatus.value = 'Error'
        }
      }
      reader.onerror = () => {
        ElMessage.error('Failed to read SVG file')
        importStatus.value = 'Error'
      }
      reader.readAsText(file)
    }

    const isValidSVGFile = (file) => {
      return file && (file.type === 'image/svg+xml' || file.name.endsWith('.svg'))
    }

    const removeCoordinateLabels = (svgText) => {
      const patterns = [
        /<text[^>]*x="[^"]*"\s+y="164"[^>]*>[A-Z][A-Z]<\/text>/g,
        /<text[^>]*y="164"\s+x="[^"]*"[^>]*>[A-Z][A-Z]<\/text>/g,
        /<text[^>]*x="[^"]*"\s+y="(1[4-9][0-9][0-9]|[2-9][0-9][0-9][0-9])"[^>]*>[A-Z][A-Z]<\/text>/g,
        /<text[^>]*y="(1[4-9][0-9][0-9]|[2-9][0-9][0-9][0-9])"\s+x="[^"]*"[^>]*>[A-Z][A-Z]<\/text>/g,
        /<text[^>]*x="-?\d+"\s+y="[^"]*"[^>]*>\d{1,2}<\/text>/g,
        /<text[^>]*y="[^"]*"\s+x="-?\d+"[^>]*>\d{1,2}<\/text>/g,
        /<text[^>]*x="([-]?[0-9]{1,2}|3[4-9][0-9][0-9])"[^>]*>\d{1,2}<\/text>/g,
        /<text[^>]*x="([-]?[0-9]{1,2}|3[4-9][0-9][0-9])"[^>]*>[A-Z][A-Z]<\/text>/g
      ]
      
      return patterns.reduce((text, pattern) => text.replace(pattern, ''), svgText)
    }

    const parseSVGContent = (svgText, isLoadingFromSave = false) => {
      try {
        importStatus.value = 'Loading SVG...'
        
        if (!validateSVGCanvas()) return
        
        svgDraw.clear()
        
        const { width, height } = extractSVGDimensions(svgText)
        const cleanedSVGText = removeCoordinateLabels(svgText)
        
        if (!isLoadingFromSave) {
          originalSVGContent = cleanedSVGText
        }
        
        svgDraw.viewbox(0, 0, width, height)
        svgDraw.svg(cleanedSVGText)
        
        if (!isLoadingFromSave) {
          setupGridAndCoordinates(svgText)
        }
        
        organizeIntoLayers()
        setupInteractions()
        
        setTimeout(fitToScreen, 100)
        
        importStatus.value = 'Complete'
        ElMessage.success('SVG imported successfully')
        
      } catch (error) {
        handleSVGError(error)
      }
    }

    const validateSVGCanvas = () => {
      if (!svgDraw) {
        ElMessage.error('SVG canvas not initialized. Please try again.')
        importStatus.value = 'Error'
        return false
      }
      return true
    }

    const extractSVGDimensions = (svgText) => {
      const parser = new DOMParser()
      const svgDoc = parser.parseFromString(svgText, 'image/svg+xml')
      const svgRoot = svgDoc.documentElement
      
      return {
        width: parseFloat(svgRoot.getAttribute('width') || DEFAULT_VIEWBOX.width),
        height: parseFloat(svgRoot.getAttribute('height') || DEFAULT_VIEWBOX.height)
      }
    }

    const setupGridAndCoordinates = (svgText) => {
      detectCoordinateLabels(svgText)
      generateGrid()
      moveGrid(GRID_OFFSET.x, GRID_OFFSET.y)
      
      if (gridLayer) {
        gridLayer.back()
        gridLayer.addClass('non-draggable')
      }
    }

    const handleSVGError = (error) => {
      console.error('Error processing SVG:', error)
      ElMessage.error('Failed to process SVG: ' + error.message)
      importStatus.value = 'Error'
    }

    const detectCoordinateLabels = (originalSVGText) => {
      coordinateLabels = {
        top: [],
        bottom: [],
        left: [],
        right: []
      }
      
      extractColumnLabels(originalSVGText)
      extractRowLabels(originalSVGText)
      sortCoordinateLabels()
    }

    const extractColumnLabels = (svgText) => {
      const columnLabelRegex = /<text[^>]*x="([^"]*)"|[^>]*y="([^"]*)"|[^>]*>([A-Z][A-Z])<\/text>/g
      let match
      
      while ((match = columnLabelRegex.exec(svgText)) !== null) {
        const coord = transformCoordinate(
          parseFloat(match[1]),
          parseFloat(match[2]),
          match[3]
        )
        
        if (coord.y < 200) {
          coordinateLabels.top.push(coord)
        } else if (coord.y > 1300) {
          coordinateLabels.bottom.push(coord)
        }
      }
    }

    const extractRowLabels = (svgText) => {
      const rowLabelRegex = /<text[^>]*x="([^"]*)"|[^>]*y="([^"]*)"|[^>]*>(\d{1,2})<\/text>/g
      let match
      
      while ((match = rowLabelRegex.exec(svgText)) !== null) {
        const coord = transformCoordinate(
          parseFloat(match[1]),
          parseFloat(match[2]),
          match[3]
        )
        
        if (coord.x < 200) {
          coordinateLabels.left.push(coord)
        } else if (coord.x > 3400) {
          coordinateLabels.right.push(coord)
        }
      }
    }

    const transformCoordinate = (x, y, label) => ({
      label,
      x: x + COORDINATE_TRANSFORM.x,
      y: y + COORDINATE_TRANSFORM.y
    })

    const sortCoordinateLabels = () => {
      coordinateLabels.top.sort((a, b) => a.x - b.x)
      coordinateLabels.bottom.sort((a, b) => a.x - b.x)
      coordinateLabels.left.sort((a, b) => b.y - a.y)
      coordinateLabels.right.sort((a, b) => b.y - a.y)
    }

    const generateGrid = () => {
      if (!svgDraw) return
      
      if (gridLayer) {
        gridLayer.remove()
      }
      
      gridLayer = svgDraw.group().addClass('grid-layer')
      
      const boundaries = calculateGridBoundaries()
      
      generateVerticalGridLines(boundaries)
      generateHorizontalGridLines(boundaries)
      addCoordinateLabelsToGrid()
      addTileCoordinatesToCells()
    }

    const calculateGridBoundaries = () => {
      return {
        topY: coordinateLabels.top.length > 0 ? Math.min(...coordinateLabels.top.map(c => c.y)) - 20 : 80,
        bottomY: coordinateLabels.bottom.length > 0 ? Math.max(...coordinateLabels.bottom.map(c => c.y)) + 20 : 1420,
        leftX: coordinateLabels.left.length > 0 ? Math.min(...coordinateLabels.left.map(c => c.x)) - 20 : 60,
        rightX: coordinateLabels.right.length > 0 ? Math.max(...coordinateLabels.right.map(c => c.x)) + 20 : 3520
      }
    }

    const generateVerticalGridLines = ({ topY, bottomY }) => {
      if (coordinateLabels.top.length === 0 && coordinateLabels.bottom.length === 0) return
      
      const uniqueColumns = getUniqueColumns()
      drawColumnGridLines(uniqueColumns, topY, bottomY)
      drawColumnBoundaries(uniqueColumns, topY, bottomY)
    }

    const generateHorizontalGridLines = ({ leftX, rightX }) => {
      if (coordinateLabels.left.length === 0 && coordinateLabels.right.length === 0) return
      
      const uniqueRows = getUniqueRows()
      drawRowGridLines(uniqueRows, leftX, rightX)
      drawRowBoundaries(uniqueRows, leftX, rightX)
    }

    const getUniqueColumns = () => {
      const columnCoords = [...coordinateLabels.top, ...coordinateLabels.bottom]
      const uniqueColumns = []
      
      columnCoords.forEach(coord => {
        if (!uniqueColumns.find(c => Math.abs(c.x - coord.x) < 5)) {
          uniqueColumns.push(coord)
        }
      })
      
      return uniqueColumns.sort((a, b) => a.x - b.x)
    }

    const getUniqueRows = () => {
      const rowCoords = [...coordinateLabels.left, ...coordinateLabels.right]
      const uniqueRows = []
      
      rowCoords.forEach(coord => {
        if (!uniqueRows.find(r => Math.abs(r.y - coord.y) < 5)) {
          uniqueRows.push(coord)
        }
      })
      
      return uniqueRows.sort((a, b) => a.y - b.y)
    }

    const drawColumnGridLines = (uniqueColumns, topY, bottomY) => {
      for (let i = 0; i < uniqueColumns.length - 1; i++) {
        const gridLineX = uniqueColumns[i].x + (uniqueColumns[i + 1].x - uniqueColumns[i].x) / 2
        createGridLine(gridLineX, topY, gridLineX, bottomY, 'grid-line-vertical')
      }
    }

    const drawRowGridLines = (uniqueRows, leftX, rightX) => {
      for (let i = 0; i < uniqueRows.length - 1; i++) {
        const gridLineY = uniqueRows[i].y + (uniqueRows[i + 1].y - uniqueRows[i].y) / 2
        createGridLine(leftX, gridLineY, rightX, gridLineY, 'grid-line-horizontal')
      }
    }

    const drawColumnBoundaries = (uniqueColumns, topY, bottomY) => {
      if (uniqueColumns.length === 0) return
      
      const colSpacing = uniqueColumns.length > 1 ? uniqueColumns[1].x - uniqueColumns[0].x : 36
      const firstCol = uniqueColumns[0]
      const lastCol = uniqueColumns[uniqueColumns.length - 1]
      
      createGridLine(firstCol.x - colSpacing/2, topY, firstCol.x - colSpacing/2, bottomY, 'grid-line-vertical')
      createGridLine(lastCol.x + colSpacing/2, topY, lastCol.x + colSpacing/2, bottomY, 'grid-line-vertical')
    }

    const drawRowBoundaries = (uniqueRows, leftX, rightX) => {
      if (uniqueRows.length === 0) return
      
      const rowSpacing = uniqueRows.length > 1 ? uniqueRows[1].y - uniqueRows[0].y : 36
      const firstRow = uniqueRows[0]
      const lastRow = uniqueRows[uniqueRows.length - 1]
      
      createGridLine(leftX, firstRow.y - rowSpacing/2, rightX, firstRow.y - rowSpacing/2, 'grid-line-horizontal')
      createGridLine(leftX, lastRow.y + rowSpacing/2, rightX, lastRow.y + rowSpacing/2, 'grid-line-horizontal')
    }

    const createGridLine = (x1, y1, x2, y2, className) => {
      gridLayer.line(x1, y1, x2, y2)
        .stroke({ color: '#ddd', width: 1, dasharray: '2,2' })
        .addClass(className)
    }

    const addCoordinateLabelsToGrid = () => {
      if (!gridLayer) return
      
      const labelConfig = {
        font: { family: 'Tahoma', size: 16, weight: 'bold' },
        fill: '#666'
      }
      
      addLabels(coordinateLabels.top, { x: -10, y: -20 }, 'coordinate-label-top', labelConfig)
      addLabels(coordinateLabels.bottom, { x: -10, y: 5 }, 'coordinate-label-bottom', labelConfig)
      addLabels(coordinateLabels.left, { x: -20, y: -8 }, 'coordinate-label-left', labelConfig)
      addLabels(coordinateLabels.right, { x: 5, y: -8 }, 'coordinate-label-right', labelConfig)
    }

    const addLabels = (labels, offset, className, config) => {
      labels.forEach(coord => {
        gridLayer.text(coord.label)
          .move(coord.x + offset.x, coord.y + offset.y)
          .font(config.font)
          .fill(config.fill)
          .addClass(className)
      })
    }

    const addTileCoordinatesToCells = () => {
      if (!gridLayer) return
      
      const columns = coordinateLabels.top.length > 0 ? coordinateLabels.top : coordinateLabels.bottom
      const rows = coordinateLabels.left.length > 0 ? coordinateLabels.left : coordinateLabels.right
      
      if (columns.length === 0 || rows.length === 0) return
      
      const sortedColumns = [...columns].sort((a, b) => a.x - b.x)
      const sortedRows = [...rows].sort((a, b) => a.y - b.y)
      
      sortedColumns.forEach((col, colIndex) => {
        sortedRows.forEach((row, rowIndex) => {
          createClickableTile(col, row, colIndex, rowIndex, sortedColumns, sortedRows)
        })
      })
    }

    const createClickableTile = (col, row, colIndex, rowIndex, sortedColumns, sortedRows) => {
      const tileCoordinate = `${col.label}-${row.label.padStart(2, '0')}`
      
      // Calculate tile dimensions
      const tileWidth = colIndex < sortedColumns.length - 1 
        ? sortedColumns[colIndex + 1].x - col.x 
        : (colIndex > 0 ? col.x - sortedColumns[colIndex - 1].x : 36)
      
      const tileHeight = rowIndex < sortedRows.length - 1 
        ? sortedRows[rowIndex + 1].y - row.y 
        : (rowIndex > 0 ? row.y - sortedRows[rowIndex - 1].y : 36)
      
      // Create invisible clickable rectangle for the tile
      const tileRect = gridLayer.rect(Math.abs(tileWidth), Math.abs(tileHeight))
        .move(col.x - Math.abs(tileWidth)/2, row.y - Math.abs(tileHeight)/2)
        .fill('transparent')
        .stroke({ color: 'transparent', width: 1 })
        .addClass('tile-clickable')
        .css({ cursor: 'pointer' })
      
      // Add click event to the tile
      tileRect.on('click', (e) => {
        e.stopPropagation()
        handleTileClick({
          coordinate: tileCoordinate,
          position: { x: col.x, y: row.y },
          dimensions: { width: Math.abs(tileWidth), height: Math.abs(tileHeight) },
          bounds: {
            left: col.x - Math.abs(tileWidth)/2,
            right: col.x + Math.abs(tileWidth)/2,
            top: row.y - Math.abs(tileHeight)/2,
            bottom: row.y + Math.abs(tileHeight)/2
          },
          columnIndex: colIndex,
          rowIndex: rowIndex
        })
      })
      
      // Add hover effects
      tileRect.on('mouseenter', () => {
        tileRect.stroke({ color: '#007bff', width: 2, opacity: 0.5 })
      })
      
      tileRect.on('mouseleave', () => {
        tileRect.stroke({ color: 'transparent', width: 1 })
      })
      
      // Add the coordinate text label
      gridLayer.text(tileCoordinate)
        .move(col.x - 14, row.y - 13)
        .font({ family: 'Arial', size: 10, weight: 'normal' })
        .fill('#999')
        .addClass('tile-coordinate')
        .css({ 
          'pointer-events': 'none',
          'user-select': 'none'
        })
    }

    const handleTileClick = (tileData) => {
      console.log('=== TILE CLICKED ===')
      console.log('Coordinate:', tileData.coordinate)
      console.log('Center Position:', tileData.position)
      console.log('Dimensions:', tileData.dimensions)
      console.log('Bounds:', tileData.bounds)
      console.log('Grid Indices:', { column: tileData.columnIndex, row: tileData.rowIndex })
      console.log('====================')
      
      // Show visual feedback
      ElMessage.info(`Clicked tile: ${tileData.coordinate}`)
    }

    const moveGrid = (offsetX, offsetY) => {
      if (!gridLayer) return
      
      const currentTransform = gridLayer.transform()
      const newX = (currentTransform.translateX || 0) + offsetX
      const newY = (currentTransform.translateY || 0) + offsetY
      
      gridLayer.translate(newX, newY)
      
      gridOffset.x = newX
      gridOffset.y = newY
    }

    const organizeIntoLayers = () => {
      if (!svgDraw) return
      
      initializeLayerGroups()
      
      let totalElements = 0
      const groups = svgDraw.find('g')
      
      groups.forEach((group, index) => {
        const elementType = classifyElement(group)
        
        layerGroups[elementType].push(group)
        
        group.data('element-type', elementType)
        group.data('element-id', `${elementType}-${index}`)
        
        totalElements++
      })
      
      objectCount.value = totalElements
    }

    const initializeLayerGroups = () => {
      layerGroups = Object.values(LAYER_TYPES).reduce((acc, type) => {
        acc[type] = []
        return acc
      }, {})
      
      if (gridLayer) {
        layerGroups[LAYER_TYPES.GRID].push(gridLayer)
      }
    }

    const groupRelatedElements = (groups) => {
      const result = []
      const processed = new Set()
      
      groups.forEach((group, index) => {
        if (processed.has(index)) return
        
        const elementType = classifyElement(group)
        const transform = group.attr('transform') || ''
        
        if (shouldGroupByTransform(elementType)) {
          const relatedGroups = findGroupsWithSameTransform(groups, group, transform, processed, index)
          result.push({ type: elementType, groups: relatedGroups, transform })
        } else {
          processed.add(index)
          result.push({ type: elementType, groups: [group], transform })
        }
      })
      
      return result
    }

    const shouldGroupByTransform = (elementType) => {
      return [LAYER_TYPES.SERVER_RACKS, LAYER_TYPES.COOLING_UNITS, LAYER_TYPES.PDU_PPC].includes(elementType)
    }

    const findGroupsWithSameTransform = (groups, group, transform, processed, index) => {
      const relatedGroups = [group]
      processed.add(index)
      
      const transformMatch = transform.match(/translate\(([^)]+)\)/)
      if (!transformMatch) return relatedGroups
      
      const translatePattern = transformMatch[1]
      
      groups.forEach((otherGroup, otherIndex) => {
        if (processed.has(otherIndex) || index === otherIndex) return
        
        const otherTransform = otherGroup.attr('transform') || ''
        if (otherTransform.includes(`translate(${translatePattern})`)) {
          const otherType = classifyElement(otherGroup)
          if (canGroupTogether(otherType)) {
            relatedGroups.push(otherGroup)
            processed.add(otherIndex)
          }
        }
      })
      
      return relatedGroups
    }

    const canGroupTogether = (elementType) => {
      return [LAYER_TYPES.SERVER_RACKS, LAYER_TYPES.COOLING_UNITS, LAYER_TYPES.PDU_PPC, LAYER_TYPES.OTHER].includes(elementType)
    }

    const classifyElement = (element) => {
      const attributes = {
        fill: element.attr('fill') || '',
        stroke: element.attr('stroke') || '',
        transform: element.attr('transform') || '',
        fillOpacity: element.attr('fill-opacity')
      }
      
      if (isFloorShape(element, attributes)) return LAYER_TYPES.FLOOR_SHAPE
      if (isCustomerZone(attributes)) return LAYER_TYPES.CUSTOMER_ZONES
      if (isServerRack(attributes)) return LAYER_TYPES.SERVER_RACKS
      if (isCoolingUnit(attributes)) return LAYER_TYPES.COOLING_UNITS
      if (isCoolingTile(element)) return LAYER_TYPES.COOLING_TILES
      if (isPDU(attributes)) return LAYER_TYPES.PDU_PPC
      
      return LAYER_TYPES.OTHER
    }

    const isFloorShape = (element, { fill, transform }) => {
      if (!fill.includes(ELEMENT_COLORS.SILVER) || !transform.includes('matrix(1,0,0,1,98,-84)')) {
        return false
      }
      
      const paths = element.find('path')
      return paths.length > 0 && (paths[0].attr('d') || '').length > 200
    }

    const isCustomerZone = ({ fill, fillOpacity }) => {
      return fill.includes(ELEMENT_COLORS.BLUE_ZONE) && fillOpacity === '0.0784'
    }

    const isServerRack = ({ fill, transform }) => {
      const hasValidFill = fill.includes(ELEMENT_COLORS.GRAY_RACK) || fill.includes(ELEMENT_COLORS.RED_RACK)
      const hasTransform = transform.includes('translate') || transform.includes('rotate')
      return hasValidFill && hasTransform
    }

    const isCoolingUnit = ({ fill }) => {
      return fill.includes(ELEMENT_COLORS.BLUE_COOLING) || fill.includes(ELEMENT_COLORS.LIGHT_BLUE_COOLING)
    }

    const isCoolingTile = (element) => {
      const paths = element.find('path')
      for (let i = 0; i < paths.length; i++) {
        const pathData = paths[i].attr('d') || ''
        const cCount = (pathData.match(/C/g) || []).length
        if (cCount >= 30 && cCount <= 50) {
          return true
        }
      }
      return false
    }

    const isPDU = ({ fill }) => {
      return fill.includes(ELEMENT_COLORS.GREEN_PDU) || fill.includes(ELEMENT_COLORS.LIGHT_GREEN_PDU)
    }

    // Find the top-level group for an element
    const findTopLevelGroup = (element) => {
      if (!element) return null
      
      // If this is already a top-level group with our classification data, return it
      if (element.data('element-type')) {
        return element
      }
      
      // Traverse up the DOM tree to find the parent group with classification
      let current = element.parent()
      while (current && current !== svgDraw) {
        if (current.type === 'g' && current.data('element-type')) {
          return current
        }
        current = current.parent()
      }
      
      return null
    }

    // Set up element interactions
    const setupInteractions = () => {
      if (!svgDraw) return
      
      // Add click handlers to ALL elements (including children) for selection
      const allElements = svgDraw.find('*')
      
      allElements.forEach(element => {
        // Skip the root SVG element
        if (element === svgDraw) return
        
        element.on('click', (e) => {
          e.stopPropagation()
          
          // Find the top-level group this element belongs to
          const topGroup = findTopLevelGroup(element)
          if (topGroup) {
            selectElement(topGroup)
          }
        })
        
        element.on('mouseenter', (e) => {
          // Find the top-level group and highlight it
          const topGroup = findTopLevelGroup(element)
          if (topGroup && topGroup !== selectedElement) {
            topGroup.css({ opacity: 0.8 })
            
            // Change cursor based on drag mode and element type
            const elementType = topGroup.data('element-type')
            if (elementType === 'floor-shape') {
              element.css({ cursor: 'default' })
            } else if (dragEnabled.value) {
              element.css({ cursor: 'move' })
            } else {
              element.css({ cursor: 'pointer' })
            }
          }
        })
        
        element.on('mouseleave', (e) => {
          // Find the top-level group and remove highlight
          const topGroup = findTopLevelGroup(element)
          if (topGroup && topGroup !== selectedElement) {
            topGroup.css({ opacity: 1 })
          }
        })
      })
      
      // Set up drag functionality
      setupDrag()
      
      // Click on background to deselect (but not on tiles)
      svgDraw.on('click', (e) => {
        // Don't deselect if clicking on a tile
        if (!e.target.classList.contains('tile-clickable')) {
          deselectAll()
        }
      })
    }

    // Simple drag implementation
    const setupDrag = () => {
      // Get all groups with element types (excluding floor-shape and grid)
      const allGroups = svgDraw.find('g').filter(g => {
        const elementType = g.data('element-type')
        const isNonDraggable = g.hasClass('non-draggable')
        return elementType && elementType !== 'floor-shape' && elementType !== 'grid' && !isNonDraggable
      })
      
      allGroups.forEach(group => {
        if (dragEnabled.value) {
          group.draggable()
        }
        
        // Drag event handlers
        group.on('dragstart', (e) => {
          // Disable panning while dragging
          if (svgDraw.panZoom) {
            svgDraw.panZoom(false)
          }
          
          // Visual feedback
          group.css({ opacity: 0.7 })
          
          const elementType = group.data('element-type')
          console.log(`Started dragging ${elementType}`)
        })
        
        group.on('dragmove', (e) => {
          // Update selection properties in real-time
          if (selectedObject.value && group === selectedElement) {
            const bbox = group.bbox()
            selectedObject.value.x = Math.round(bbox.x)
            selectedObject.value.y = Math.round(bbox.y)
          }
        })
        
        group.on('dragend', (e) => {
          // Re-enable panning
          if (svgDraw.panZoom) {
            svgDraw.panZoom({
              zoomMin: 0.1,
              zoomMax: 10,
              zoomFactor: 0.1
            })
          }
          
          // Reset visual feedback
          group.css({ opacity: 1 })
          
          // Update selection properties
          if (selectedObject.value && group === selectedElement) {
            const bbox = group.bbox()
            selectedObject.value.x = Math.round(bbox.x)
            selectedObject.value.y = Math.round(bbox.y)
          }
          
          const elementType = group.data('element-type')
          console.log(`Finished dragging ${elementType}`)
          ElMessage.success(`Moved ${elementType}`)
        })
      })
    }

    // Select an element
    const selectElement = (element) => {
      // Remove previous selection
      deselectAll()
      
      // Set current selected element
      selectedElement = element
      
      // Highlight selected element
      element.css({ 
        outline: '2px solid red',
        outlineOffset: '2px',
        opacity: 1
      })
      
      // Update selected object info
      const bbox = element.bbox()
      selectedObject.value = {
        type: element.data('element-type') || 'unknown',
        id: element.data('element-id') || 'unknown',
        x: Math.round(bbox.x),
        y: Math.round(bbox.y),
        width: Math.round(bbox.width),
        height: Math.round(bbox.height),
        transform: element.attr('transform') || 'none'
      }
      
      console.log('Selected:', selectedObject.value)
      ElMessage.info(`Selected ${selectedObject.value.type}: ${selectedObject.value.id}`)
    }

    // Deselect all elements
    const deselectAll = () => {
      if (svgDraw) {
        const groups = svgDraw.find('g')
        groups.forEach(group => {
          group.css({ 
            outline: 'none',
            opacity: 1
          })
        })
      }
      selectedElement = null
      selectedObject.value = null
    }

    const toggleLayer = (layerType) => {
      if (!layerGroups[layerType]) return
      
      const isVisible = layerVisibility.value[layerType]
      
      layerGroups[layerType].forEach(group => {
        group.css({ display: isVisible ? 'block' : 'none' })
      })
    }

    const zoomIn = () => {
      if (!svgDraw) return
      const currentZoom = svgDraw.zoom()
      svgDraw.zoom(currentZoom * ZOOM_CONFIG.step)
      zoomLevel.value = svgDraw.zoom()
    }

    const zoomOut = () => {
      if (!svgDraw) return
      const currentZoom = svgDraw.zoom()
      svgDraw.zoom(currentZoom / ZOOM_CONFIG.step)
      zoomLevel.value = svgDraw.zoom()
    }

    const resetZoom = () => {
      if (!svgDraw) return
      svgDraw.zoom(1)
      svgDraw.viewbox(0, 0, DEFAULT_VIEWBOX.width, DEFAULT_VIEWBOX.height)
      zoomLevel.value = 1
    }

    const fitToScreen = () => {
      if (svgDraw) {
        // Get container size
        const container = svgContainer.value
        const containerWidth = container.clientWidth
        const containerHeight = container.clientHeight
        
        // Get SVG content bounds
        const bbox = svgDraw.bbox()
        
        // Calculate scale to fit
        const scaleX = containerWidth / bbox.width
        const scaleY = containerHeight / bbox.height
        const scale = Math.min(scaleX, scaleY, 1.0) * 0.9 // 90% to add padding
        
        svgDraw.zoom(scale)
        // Reset to center instead of using panTo
        svgDraw.viewbox(0, 0, 3660, 1417)
        zoomLevel.value = scale
        
        console.log('Fit to screen - scale:', scale)
      }
    }

    const clearCanvas = () => {
      if (!svgDraw) return
      
      svgDraw.clear()
      resetCanvasState()
    }

    const resetCanvasState = () => {
      layerGroups = {}
      gridLayer = null
      coordinateLabels = { top: [], bottom: [], left: [], right: [] }
      gridOffset = { x: 0, y: 0 }
      originalSVGContent = null
      objectCount.value = 0
      selectedObject.value = null
      importStatus.value = 'Ready'
    }

    const handleWheel = (e) => {
      e.preventDefault()
      if (!svgDraw) return
      
      const delta = e.deltaY > 0 ? 1 / ZOOM_CONFIG.step : ZOOM_CONFIG.step
      const currentZoom = svgDraw.zoom()
      svgDraw.zoom(currentZoom * delta)
      zoomLevel.value = svgDraw.zoom()
    }

    const toggleDragMode = () => {
      if (!svgDraw) return
      
      const draggableGroups = getDraggableGroups()
      
      draggableGroups.forEach(group => {
        group.draggable(dragEnabled.value)
      })
      
      ElMessage.info(`Drag mode ${dragEnabled.value ? 'enabled' : 'disabled'}`)
    }

    const getDraggableGroups = () => {
      return svgDraw.find('g').filter(g => {
        const elementType = g.data('element-type')
        const isNonDraggable = g.hasClass('non-draggable')
        return elementType && 
               elementType !== LAYER_TYPES.FLOOR_SHAPE && 
               elementType !== LAYER_TYPES.GRID && 
               !isNonDraggable
      })
    }

    const saveFloorPlan = () => {
      if (!svgDraw || !originalSVGContent) {
        ElMessage.warning('No floor plan to save. Please import an SVG first.')
        return
      }

      try {
        const floorPlanData = createFloorPlanData()
        const floorPlans = JSON.parse(localStorage.getItem('floorPlans') || '{}')
        
        floorPlans[route.params.id] = floorPlanData
        localStorage.setItem('floorPlans', JSON.stringify(floorPlans))
        
        ElMessage.success('Floor plan saved successfully')
      } catch (error) {
        console.error('Error saving floor plan:', error)
        ElMessage.error('Failed to save floor plan')
      }
    }

    const createFloorPlanData = () => {
      return {
        originalSVG: originalSVGContent,
        elementStates: getElementStates(),
        coordinateLabels,
        gridOffset,
        layerVisibility: layerVisibility.value,
        lastModified: new Date().toISOString(),
        objectCount: objectCount.value
      }
    }

    const getElementStates = () => {
      const elementStates = []
      const groups = svgDraw.find('g')
      
      groups.forEach(group => {
        const elementType = group.data('element-type')
        if (elementType && elementType !== LAYER_TYPES.GRID) {
          const transform = group.transform()
          elementStates.push({
            id: group.data('element-id'),
            type: elementType,
            transform: {
              translateX: transform.translateX || 0,
              translateY: transform.translateY || 0,
              rotate: transform.rotate || 0,
              scaleX: transform.scaleX || 1,
              scaleY: transform.scaleY || 1
            }
          })
        }
      })
      
      return elementStates
    }

    const loadFloorPlan = () => {
      try {
        const floorPlans = JSON.parse(localStorage.getItem('floorPlans') || '{}')
        const savedPlan = floorPlans[route.params.id]
        
        if (!savedPlan) return
        
        if (savedPlan.originalSVG) {
          loadNewFormatPlan(savedPlan)
        } else if (savedPlan.svgData) {
          parseSVGContent(savedPlan.svgData)
        }
      } catch (error) {
        console.error('Error loading floor plan:', error)
        ElMessage.error('Failed to load floor plan')
      }
    }

    const loadNewFormatPlan = (savedPlan) => {
      originalSVGContent = savedPlan.originalSVG
      parseSVGContent(savedPlan.originalSVG, true)
      
      restoreCoordinateLabels(savedPlan)
      generateGrid()
      restoreGridState(savedPlan)
      
      setTimeout(() => {
        restoreElementStates(savedPlan)
        restoreLayerVisibility(savedPlan)
        setupInteractions()
        setTimeout(fitToScreen, 100)
      }, 100)
    }

    const restoreCoordinateLabels = (savedPlan) => {
      if (savedPlan.coordinateLabels) {
        coordinateLabels = savedPlan.coordinateLabels
      }
    }

    const restoreGridState = (savedPlan) => {
      if (savedPlan.gridOffset && gridLayer) {
        gridOffset = savedPlan.gridOffset
        gridLayer.translate(gridOffset.x, gridOffset.y)
      }
      
      if (gridLayer) {
        gridLayer.back()
        gridLayer.addClass('non-draggable')
      }
    }

    const restoreElementStates = (savedPlan) => {
      if (!savedPlan.elementStates) return
      
      savedPlan.elementStates.forEach(state => {
        const groups = svgDraw.find('g')
        const group = groups.find(g => g.data('element-id') === state.id)
        if (group && state.transform) {
          group.transform(state.transform)
        }
      })
    }

    const restoreLayerVisibility = (savedPlan) => {
      if (!savedPlan.layerVisibility) return
      
      Object.keys(savedPlan.layerVisibility).forEach(layer => {
        if (layerVisibility.value[layer] !== undefined) {
          layerVisibility.value[layer] = savedPlan.layerVisibility[layer] ?? true
        }
      })
      
      Object.keys(savedPlan.layerVisibility).forEach(layer => {
        toggleLayer(layer)
      })
    }

    onMounted(() => {
      initializeFloorData()
      initSVGCanvas()
      nextTick(loadFloorPlan)
    })

    const initializeFloorData = () => {
      try {
        const floors = JSON.parse(localStorage.getItem('floors') || '[]')
        const sites = JSON.parse(localStorage.getItem('sites') || '[]')
        const floorId = parseInt(route.params.id)
        
        const floor = floors.find(f => f.id === floorId || f.id === String(floorId))
        
        if (floor) {
          const site = sites.find(s => s.id === floor.siteId)
          siteName.value = site?.name || 'Unknown Site'
          floorName.value = floor.name
        } else {
          siteName.value = 'Unknown Site'
          floorName.value = 'Unknown Floor'
        }
      } catch (error) {
        console.error('Error initializing floor data:', error)
        siteName.value = 'Unknown Site'
        floorName.value = 'Unknown Floor'
      }
    }

    return {
      svgContainer,
      svgFileInput,
      objectCount,
      selectedObject,
      siteName,
      floorName,
      importStatus,
      zoomLevel,
      layerVisibility,
      dragEnabled,
      triggerSVGInput,
      handleSVGImport,
      toggleLayer,
      toggleDragMode,
      zoomIn,
      zoomOut,
      resetZoom,
      fitToScreen,
      clearCanvas,
      handleWheel,
      saveFloorPlan,
      moveGrid
    }
  }
}
</script>

<style scoped>
.floor-plan-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.page-header {
  background: white;
  padding: 16px 24px;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.designer-container {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

.canvas-container {
  flex: 1;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow: hidden;
  position: relative;
}

.svg-canvas {
  width: 100%;
  height: 100%;
  min-height: 600px;
}

.controls-panel {
  width: 320px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.controls-card {
  border: 1px solid #e6e6e6;
}

.control-group {
  margin-bottom: 16px;
}

.control-group:last-child {
  margin-bottom: 0;
}

.control-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.layer-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.object-properties {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.property-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.property-item label {
  font-weight: 500;
  color: #666;
  margin: 0;
}

.property-item span {
  color: #333;
  font-family: monospace;
  font-size: 12px;
}

.no-selection {
  text-align: center;
  color: #999;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.zoom-info {
  text-align: center;
  margin-top: 8px;
  font-size: 14px;
  color: #666;
}
</style>