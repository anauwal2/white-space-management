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
              <el-checkbox v-model="showFloorShapeLayer" @change="toggleLayer('floor-shape')">
                Floor Shape
              </el-checkbox>
              <el-checkbox v-model="showCustomerZonesLayer" @change="toggleLayer('customer-zones')">
                Customer Zones
              </el-checkbox>
              <el-checkbox v-model="showServerRacksLayer" @change="toggleLayer('server-racks')">
                Server Racks
              </el-checkbox>
              <el-checkbox v-model="showCoolingUnitsLayer" @change="toggleLayer('cooling-units')">
                Cooling Units
              </el-checkbox>
              <el-checkbox v-model="showCoolingTilesLayer" @change="toggleLayer('cooling-tiles')">
                Cooling Tiles
              </el-checkbox>
              <el-checkbox v-model="showPDULayer" @change="toggleLayer('pdu-ppc')">
                PDUs/PPCs
              </el-checkbox>
              <el-checkbox v-model="showOtherLayer" @change="toggleLayer('other')">
                Other Elements
              </el-checkbox>
              <el-checkbox v-model="showGridLayer" @change="toggleLayer('grid')">
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

export default {
  name: 'FloorPlan',
  setup() {
    const route = useRoute()
    const svgContainer = ref(null)
    const svgFileInput = ref(null)
    const objectCount = ref(0)
    const selectedObject = ref(null)
    const siteName = ref('')
    const floorName = ref('')
    const importStatus = ref('Ready')
    const zoomLevel = ref(1)
    
    // Layer visibility controls
    const showFloorShapeLayer = ref(true)
    const showCustomerZonesLayer = ref(true)
    const showServerRacksLayer = ref(true)
    const showCoolingUnitsLayer = ref(true)
    const showCoolingTilesLayer = ref(true)
    const showPDULayer = ref(true)
    const showOtherLayer = ref(true)
    const showGridLayer = ref(true)
    const dragEnabled = ref(true)
    
    let svgDraw = null
    let currentSVGContent = null
    let originalSVGContent = null // Store the original imported SVG before modifications
    let layerGroups = {}
    let selectedElement = null
    let gridLayer = null
    let coordinateLabels = {
      top: [],
      bottom: [],
      left: [],
      right: []
    }
    let gridOffset = { x: 0, y: 0 } // Store grid offset
    
    // Initialize SVG.js canvas
    const initSVGCanvas = () => {
      nextTick(() => {
        if (svgContainer.value) {
          // Create SVG.js drawing area
          svgDraw = SVG().addTo(svgContainer.value).size('100%', '100%')
          svgDraw.viewbox(0, 0, 3660, 1417) // Default viewbox
          
          // Enable panning and zooming
          svgDraw.panZoom({
            zoomMin: 0.1,
            zoomMax: 10,
            zoomFactor: 0.1
          })
          
          console.log('SVG.js canvas initialized')
        }
      })
    }

    // Trigger SVG file input
    const triggerSVGInput = () => {
      svgFileInput.value?.click()
    }

    // Handle SVG file import
    const handleSVGImport = (event) => {
      const file = event.target.files[0]
      if (file && (file.type === 'image/svg+xml' || file.name.endsWith('.svg'))) {
        importStatus.value = 'Reading SVG file...'
        
        const reader = new FileReader()
        reader.onload = (e) => {
          try {
            const svgContent = e.target.result
            console.log('SVG Content loaded')
            parseSVGContent(svgContent)
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
      } else {
        ElMessage.error('Please select a valid SVG file')
      }
    }

    // Remove coordinate labels from SVG content before import
    const removeCoordinateLabels = (svgText) => {
      // Remove column coordinate labels (AA, AB, AC, BA, BB, BC, etc.)
      // These appear at y="164" (top) and typically at bottom as well
      svgText = svgText.replace(/<text[^>]*x="[^"]*"\s+y="164"[^>]*>[A-Z][A-Z]<\/text>/g, '')
      svgText = svgText.replace(/<text[^>]*y="164"\s+x="[^"]*"[^>]*>[A-Z][A-Z]<\/text>/g, '')
      
      // Remove column labels from bottom (typically higher y values)
      svgText = svgText.replace(/<text[^>]*x="[^"]*"\s+y="(1[4-9][0-9][0-9]|[2-9][0-9][0-9][0-9])"[^>]*>[A-Z][A-Z]<\/text>/g, '')
      svgText = svgText.replace(/<text[^>]*y="(1[4-9][0-9][0-9]|[2-9][0-9][0-9][0-9])"\s+x="[^"]*"[^>]*>[A-Z][A-Z]<\/text>/g, '')
      
      // Remove row coordinate labels (numbers like 34, 33, 32, 31, 30, etc.)
      // These appear at x="-38" (left) and x="3480" (right) or similar positions
      svgText = svgText.replace(/<text[^>]*x="-?\d+"\s+y="[^"]*"[^>]*>\d{1,2}<\/text>/g, '')
      svgText = svgText.replace(/<text[^>]*y="[^"]*"\s+x="-?\d+"[^>]*>\d{1,2}<\/text>/g, '')
      
      // Remove any remaining coordinate-style labels at edge positions
      svgText = svgText.replace(/<text[^>]*x="([-]?[0-9]{1,2}|3[4-9][0-9][0-9])"[^>]*>\d{1,2}<\/text>/g, '')
      svgText = svgText.replace(/<text[^>]*x="([-]?[0-9]{1,2}|3[4-9][0-9][0-9])"[^>]*>[A-Z][A-Z]<\/text>/g, '')
      
      console.log('Removed coordinate labels from SVG')
      return svgText
    }

    // Parse and display SVG content
    const parseSVGContent = (svgText, isLoadingFromSave = false) => {
      try {
        importStatus.value = 'Loading SVG...'
        
        // Ensure SVG canvas is initialized
        if (!svgDraw) {
          console.error('SVG canvas not initialized')
          ElMessage.error('SVG canvas not initialized. Please try again.')
          importStatus.value = 'Error'
          return
        }
        
        // Clear existing content
        svgDraw.clear()
        
        // Parse SVG using DOMParser
        const parser = new DOMParser()
        const svgDoc = parser.parseFromString(svgText, 'image/svg+xml')
        const svgRoot = svgDoc.documentElement
        
        // Get SVG dimensions
        const width = parseFloat(svgRoot.getAttribute('width') || '3660')
        const height = parseFloat(svgRoot.getAttribute('height') || '1417')
        
        console.log('SVG Dimensions:', width, 'x', height)
        
        // Remove coordinate labels from SVG before import
        const cleanedSVGText = removeCoordinateLabels(svgText)
        
        // Store the original SVG content (after cleaning but before grid generation)
        if (!isLoadingFromSave) {
          originalSVGContent = cleanedSVGText
        }
        
        // Update viewbox
        svgDraw.viewbox(0, 0, width, height)
        
        // Import the cleaned SVG content into SVG.js
        const importedSVG = svgDraw.svg(cleanedSVGText)
        
        // Only generate grid if this is a fresh import, not loading from save
        if (!isLoadingFromSave) {
          // Detect coordinate labels from the original SVG (before cleaning)
          detectCoordinateLabels(svgText)
          
          // Generate grid based on detected coordinates
          generateGrid()
          
          // Move grid by (100, 50) offset
          moveGrid(13, -14)
          
          // Send grid to back and make it non-draggable
          if (gridLayer) {
            gridLayer.back() // Send to the very back
            gridLayer.addClass('non-draggable') // Add class to identify as non-draggable
          }
        }
        
        // Organize elements into layers
        organizeIntoLayers()
        
        // Set up interaction
        setupInteractions()
        
        // Fit to screen
        setTimeout(() => {
          fitToScreen()
        }, 100)
        
        importStatus.value = 'Complete'
        ElMessage.success('SVG imported successfully')
        
      } catch (error) {
        console.error('Error processing SVG:', error)
        ElMessage.error('Failed to process SVG: ' + error.message)
        importStatus.value = 'Error'
      }
    }

    // Detect coordinate labels from original SVG text
    const detectCoordinateLabels = (originalSVGText) => {
      // Reset coordinate labels
      coordinateLabels = {
        top: [],
        bottom: [],
        left: [],
        right: []
      }
      
      // Extract column labels (AA, AB, AC, BA, BB, BC, etc.)
      const columnLabelRegex = /<text[^>]*x="([^"]*)"[^>]*y="([^"]*)"[^>]*>([A-Z][A-Z])<\/text>/g
      let match
      
      while ((match = columnLabelRegex.exec(originalSVGText)) !== null) {
        const x = parseFloat(match[1])
        const y = parseFloat(match[2])
        const label = match[3]
        
        // Apply the transform matrix (1,0,0,1,98,-84) that's common in this SVG
        const actualX = x + 98
        const actualY = y - 84
        
        // Classify based on position
        if (actualY < 200) {
          coordinateLabels.top.push({ label, x: actualX, y: actualY })
        } else if (actualY > 1300) {
          coordinateLabels.bottom.push({ label, x: actualX, y: actualY })
        }
      }
      
      // Extract row labels (34, 33, 32, etc.)
      const rowLabelRegex = /<text[^>]*x="([^"]*)"[^>]*y="([^"]*)"[^>]*>(\d{1,2})<\/text>/g
      
      while ((match = rowLabelRegex.exec(originalSVGText)) !== null) {
        const x = parseFloat(match[1])
        const y = parseFloat(match[2])
        const label = match[3]
        
        // Apply the transform matrix (1,0,0,1,98,-84) that's common in this SVG
        const actualX = x + 98
        const actualY = y - 84
        
        // Classify based on position
        if (actualX < 200) {
          coordinateLabels.left.push({ label, x: actualX, y: actualY })
        } else if (actualX > 3400) {
          coordinateLabels.right.push({ label, x: actualX, y: actualY })
        }
      }
      
      // Sort coordinates for consistent ordering
      coordinateLabels.top.sort((a, b) => a.x - b.x)
      coordinateLabels.bottom.sort((a, b) => a.x - b.x)
      coordinateLabels.left.sort((a, b) => b.y - a.y) // Top to bottom (descending Y)
      coordinateLabels.right.sort((a, b) => b.y - a.y) // Top to bottom (descending Y)
      
      console.log('Detected coordinates from original SVG:', coordinateLabels)
    }

    // Generate grid based on detected coordinates
    const generateGrid = () => {
      if (!svgDraw) return
      
      // Remove existing grid if it exists
      if (gridLayer) {
        gridLayer.remove()
      }
      
      // Create grid layer
      gridLayer = svgDraw.group().addClass('grid-layer')
      
      // Calculate grid boundaries dynamically
      const topY = coordinateLabels.top.length > 0 ? Math.min(...coordinateLabels.top.map(c => c.y)) - 20 : 80
      const bottomY = coordinateLabels.bottom.length > 0 ? Math.max(...coordinateLabels.bottom.map(c => c.y)) + 20 : 1420
      const leftX = coordinateLabels.left.length > 0 ? Math.min(...coordinateLabels.left.map(c => c.x)) - 20 : 60
      const rightX = coordinateLabels.right.length > 0 ? Math.max(...coordinateLabels.right.map(c => c.x)) + 20 : 3520
      
      // Generate vertical grid lines (columns)
      if (coordinateLabels.top.length > 0 || coordinateLabels.bottom.length > 0) {
        const columnCoords = [...coordinateLabels.top, ...coordinateLabels.bottom]
        const uniqueColumns = []
        
        columnCoords.forEach(coord => {
          if (!uniqueColumns.find(c => Math.abs(c.x - coord.x) < 5)) {
            uniqueColumns.push(coord)
          }
        })
        
        // Sort columns by X position
        uniqueColumns.sort((a, b) => a.x - b.x)
        
        // Draw grid lines between columns (not through the labels)
        for (let i = 0; i < uniqueColumns.length - 1; i++) {
          const currentX = uniqueColumns[i].x
          const nextX = uniqueColumns[i + 1].x
          const gridLineX = currentX + (nextX - currentX) / 2
          
          const line = gridLayer.line(gridLineX, topY, gridLineX, bottomY)
            .stroke({ color: '#ddd', width: 1, dasharray: '2,2' })
            .addClass('grid-line-vertical')
        }
        
        // Add boundary lines at the edges
        if (uniqueColumns.length > 0) {
          const firstCol = uniqueColumns[0]
          const lastCol = uniqueColumns[uniqueColumns.length - 1]
          const colSpacing = uniqueColumns.length > 1 ? uniqueColumns[1].x - uniqueColumns[0].x : 36
          
          // Left boundary
          const leftBoundary = gridLayer.line(firstCol.x - colSpacing/2, topY, firstCol.x - colSpacing/2, bottomY)
            .stroke({ color: '#ddd', width: 1, dasharray: '2,2' })
            .addClass('grid-line-vertical')
            
          // Right boundary  
          const rightBoundary = gridLayer.line(lastCol.x + colSpacing/2, topY, lastCol.x + colSpacing/2, bottomY)
            .stroke({ color: '#ddd', width: 1, dasharray: '2,2' })
            .addClass('grid-line-vertical')
        }
      }
      
      // Generate horizontal grid lines (rows)
      if (coordinateLabels.left.length > 0 || coordinateLabels.right.length > 0) {
        const rowCoords = [...coordinateLabels.left, ...coordinateLabels.right]
        const uniqueRows = []
        
        rowCoords.forEach(coord => {
          if (!uniqueRows.find(r => Math.abs(r.y - coord.y) < 5)) {
            uniqueRows.push(coord)
          }
        })
        
        // Sort rows by Y position
        uniqueRows.sort((a, b) => a.y - b.y)
        
        // Draw grid lines between rows (not through the labels)
        for (let i = 0; i < uniqueRows.length - 1; i++) {
          const currentY = uniqueRows[i].y
          const nextY = uniqueRows[i + 1].y
          const gridLineY = currentY + (nextY - currentY) / 2
          
          const line = gridLayer.line(leftX, gridLineY, rightX, gridLineY)
            .stroke({ color: '#ddd', width: 1, dasharray: '2,2' })
            .addClass('grid-line-horizontal')
        }
        
        // Add boundary lines at the edges
        if (uniqueRows.length > 0) {
          const firstRow = uniqueRows[0]
          const lastRow = uniqueRows[uniqueRows.length - 1]
          const rowSpacing = uniqueRows.length > 1 ? uniqueRows[1].y - uniqueRows[0].y : 36
          
          // Top boundary
          const topBoundary = gridLayer.line(leftX, firstRow.y - rowSpacing/2, rightX, firstRow.y - rowSpacing/2)
            .stroke({ color: '#ddd', width: 1, dasharray: '2,2' })
            .addClass('grid-line-horizontal')
            
          // Bottom boundary
          const bottomBoundary = gridLayer.line(leftX, lastRow.y + rowSpacing/2, rightX, lastRow.y + rowSpacing/2)
            .stroke({ color: '#ddd', width: 1, dasharray: '2,2' })
            .addClass('grid-line-horizontal')
        }
      }
      
      // Add coordinate labels to grid layer
      addCoordinateLabelsToGrid()
      
      console.log('Grid generated successfully')
    }

    // Add coordinate labels to the grid
    const addCoordinateLabelsToGrid = () => {
      if (!gridLayer) return
      
      // Add top labels
      coordinateLabels.top.forEach(coord => {
        gridLayer.text(coord.label)
          .move(coord.x - 10, coord.y - 20)
          .font({ family: 'Tahoma', size: 16, weight: 'bold' })
          .fill('#666')
          .addClass('coordinate-label-top')
      })
      
      // Add bottom labels  
      coordinateLabels.bottom.forEach(coord => {
        gridLayer.text(coord.label)
          .move(coord.x - 10, coord.y + 5)
          .font({ family: 'Tahoma', size: 16, weight: 'bold' })
          .fill('#666')
          .addClass('coordinate-label-bottom')
      })
      
      // Add left labels
      coordinateLabels.left.forEach(coord => {
        gridLayer.text(coord.label)
          .move(coord.x - 20, coord.y - 8)
          .font({ family: 'Tahoma', size: 16, weight: 'bold' })
          .fill('#666')
          .addClass('coordinate-label-left')
      })
      
      // Add right labels
      coordinateLabels.right.forEach(coord => {
        gridLayer.text(coord.label)
          .move(coord.x + 5, coord.y - 8)
          .font({ family: 'Tahoma', size: 16, weight: 'bold' })
          .fill('#666')
          .addClass('coordinate-label-right')
      })
    }

    // Move the entire grid including labels by x,y offset
    const moveGrid = (offsetX, offsetY) => {
      if (!gridLayer) {
        console.warn('No grid layer to move')
        return
      }
      
      // Get current transform or create new one
      const currentTransform = gridLayer.transform()
      const newX = (currentTransform.translateX || 0) + offsetX
      const newY = (currentTransform.translateY || 0) + offsetY
      
      // Apply translation to the entire grid layer
      gridLayer.translate(newX, newY)
      
      // Track the total grid offset
      gridOffset.x = newX
      gridOffset.y = newY
      
      console.log(`Grid moved by (${offsetX}, ${offsetY}). New position: (${newX}, ${newY})`)
    }

    // Organize SVG elements into logical layers
    const organizeIntoLayers = () => {
      if (!svgDraw) return
      
      // Initialize layer groups
      layerGroups = {
        'floor-shape': [],
        'customer-zones': [],
        'server-racks': [],
        'cooling-units': [],
        'cooling-tiles': [],
        'pdu-ppc': [],
        'other': [],
        'grid': []
      }
      
      // Add grid layer to layerGroups if it exists
      if (gridLayer) {
        layerGroups['grid'].push(gridLayer)
      }
      
      let totalElements = 0
      
      // Find all group elements
      const groups = svgDraw.find('g')
      
      groups.forEach((group, index) => {
        const elementType = classifyElement(group)
        
        // Add to appropriate layer
        layerGroups[elementType].push(group)
        
        // Add data attributes for identification
        group.data('element-type', elementType)
        group.data('element-id', `${elementType}-${index}`)
        
        totalElements++
      })
      
      objectCount.value = totalElements
      console.log('Layer organization:', layerGroups)
    }

    // Group related elements together (like server racks with multiple groups)
    const groupRelatedElements = (groups) => {
      const result = []
      const processed = new Set()
      
      console.log('Starting groupRelatedElements with', groups.length, 'groups')
      
      groups.forEach((group, index) => {
        if (processed.has(index)) return
        
        const elementType = classifyElement(group)
        const transform = group.attr('transform') || ''
        
        // For server racks and other equipment, look for consecutive groups with same transform pattern
        if (['server-racks', 'cooling-units', 'pdu-ppc'].includes(elementType)) {
          const relatedGroups = [group]
          processed.add(index)
          
          // Extract transform pattern (translate coordinates)
          const transformMatch = transform.match(/translate\(([^)]+)\)/)
          if (transformMatch) {
            const translatePattern = transformMatch[1]
            console.log(`Looking for groups with translate pattern: ${translatePattern}`)
            
            // Look for other groups with the same translate pattern
            groups.forEach((otherGroup, otherIndex) => {
              if (processed.has(otherIndex) || index === otherIndex) return
              
              const otherTransform = otherGroup.attr('transform') || ''
              if (otherTransform.includes(`translate(${translatePattern})`)) {
                const otherType = classifyElement(otherGroup)
                // More flexible grouping - any element with same translate should group together
                if (['server-racks', 'cooling-units', 'pdu-ppc', 'other'].includes(otherType)) {
                  console.log(`Found related group: ${otherType} with same translate`)
                  relatedGroups.push(otherGroup)
                  processed.add(otherIndex)
                }
              }
            })
          }
          
          console.log(`Created ${elementType} group with ${relatedGroups.length} elements`)
          result.push({
            type: elementType,
            groups: relatedGroups,
            transform: transform
          })
        } else {
          // Single group elements
          processed.add(index)
          result.push({
            type: elementType,
            groups: [group],
            transform: transform
          })
        }
      })
      
      console.log(`groupRelatedElements result: ${result.length} element groups`)
      return result
    }

    // Classify elements based on their attributes
    const classifyElement = (element) => {
      const fill = element.attr('fill') || ''
      const stroke = element.attr('stroke') || ''
      const transform = element.attr('transform') || ''
      
      // Check for floor shape (silver fill with base transform)
      if (fill.includes('silver') && transform.includes('matrix(1,0,0,1,98,-84)')) {
        const paths = element.find('path')
        if (paths.length > 0) {
          const pathData = paths[0].attr('d') || ''
          if (pathData.length > 200) {
            return 'floor-shape'
          }
        }
      }
      
      // Check for customer zones (blue highlighted areas)
      if (fill.includes('rgb(0,120,215)') && element.attr('fill-opacity') === '0.0784') {
        return 'customer-zones'
      }
      
      // Check for server racks (gray/red fills with transforms)
      if ((fill.includes('rgb(110,110,110)') || fill.includes('rgb(230,0,0)')) && 
          (transform.includes('translate') || transform.includes('rotate'))) {
        return 'server-racks'
      }
      
      // Check for cooling units (blue fills)
      if (fill.includes('rgb(62,153,223)') || fill.includes('rgb(171,211,241)')) {
        return 'cooling-units'
      }
      
      // Check for cooling tiles (many curve commands)
      const paths = element.find('path')
      for (let i = 0; i < paths.length; i++) {
        const pathData = paths[i].attr('d') || ''
        const cCount = (pathData.match(/C/g) || []).length
        if (cCount >= 30 && cCount <= 50) {
          return 'cooling-tiles'
        }
      }
      
      // Check for PDUs/PPCs (green fills)
      if (fill.includes('rgb(103,203,51)') || fill.includes('rgb(189,232,167)')) {
        return 'pdu-ppc'
      }
      
      return 'other'
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
      
      // Click on background to deselect
      svgDraw.on('click', () => {
        deselectAll()
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

    // Toggle layer visibility
    const toggleLayer = (layerType) => {
      if (!layerGroups[layerType]) return
      
      const isVisible = getLayerVisibility(layerType)
      
      layerGroups[layerType].forEach(group => {
        group.css({ display: isVisible ? 'block' : 'none' })
      })
      
      console.log(`Layer ${layerType} ${isVisible ? 'shown' : 'hidden'}`)
    }

    // Get layer visibility state
    const getLayerVisibility = (layerType) => {
      switch (layerType) {
        case 'floor-shape': return showFloorShapeLayer.value
        case 'customer-zones': return showCustomerZonesLayer.value
        case 'server-racks': return showServerRacksLayer.value
        case 'cooling-units': return showCoolingUnitsLayer.value
        case 'cooling-tiles': return showCoolingTilesLayer.value
        case 'pdu-ppc': return showPDULayer.value
        case 'other': return showOtherLayer.value
        case 'grid': return showGridLayer.value
        default: return true
      }
    }

    // Zoom controls
    const zoomIn = () => {
      if (svgDraw) {
        const currentZoom = svgDraw.zoom()
        svgDraw.zoom(currentZoom * 1.2)
        zoomLevel.value = svgDraw.zoom()
      }
    }

    const zoomOut = () => {
      if (svgDraw) {
        const currentZoom = svgDraw.zoom()
        svgDraw.zoom(currentZoom * 0.8)
        zoomLevel.value = svgDraw.zoom()
      }
    }

    const resetZoom = () => {
      if (svgDraw) {
        svgDraw.zoom(1)
        // Reset viewbox instead of using panTo
        svgDraw.viewbox(0, 0, 3660, 1417)
        zoomLevel.value = 1
      }
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

    // Clear canvas
    const clearCanvas = () => {
      if (svgDraw) {
        svgDraw.clear()
        layerGroups = {}
        gridLayer = null
        coordinateLabels = { top: [], bottom: [], left: [], right: [] }
        gridOffset = { x: 0, y: 0 }
        originalSVGContent = null
        objectCount.value = 0
        selectedObject.value = null
        importStatus.value = 'Ready'
      }
    }

    // Handle mouse wheel for zooming
    const handleWheel = (e) => {
      e.preventDefault()
      if (svgDraw) {
        const delta = e.deltaY > 0 ? 0.9 : 1.1
        const currentZoom = svgDraw.zoom()
        svgDraw.zoom(currentZoom * delta)
        zoomLevel.value = svgDraw.zoom()
      }
    }

    // Toggle drag mode
    const toggleDragMode = () => {
      if (!svgDraw) return
      
      // Get all groups with element types (excluding floor-shape and grid)
      const allGroups = svgDraw.find('g').filter(g => {
        const elementType = g.data('element-type')
        const isNonDraggable = g.hasClass('non-draggable')
        return elementType && elementType !== 'floor-shape' && elementType !== 'grid' && !isNonDraggable
      })
      
      allGroups.forEach(group => {
        if (dragEnabled.value) {
          group.draggable()
        } else {
          group.draggable(false)
        }
      })
      
      console.log(`Drag mode ${dragEnabled.value ? 'enabled' : 'disabled'}`)
      ElMessage.info(`Drag mode ${dragEnabled.value ? 'enabled' : 'disabled'}`)
    }

    // Save floor plan
    const saveFloorPlan = () => {
      if (svgDraw && originalSVGContent) {
        // Get current state of all elements
        const elementStates = []
        const groups = svgDraw.find('g')
        
        groups.forEach(group => {
          const elementType = group.data('element-type')
          if (elementType && elementType !== 'grid') {
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
        
        const floorPlans = JSON.parse(localStorage.getItem('floorPlans') || '{}')
        const floorId = route.params.id
        
        floorPlans[floorId] = {
          originalSVG: originalSVGContent, // Store the original SVG without grid
          elementStates: elementStates, // Store element positions/transforms
          coordinateLabels: coordinateLabels, // Store detected coordinate labels
          gridOffset: gridOffset, // Store grid offset
          layerVisibility: {
            'floor-shape': showFloorShapeLayer.value,
            'customer-zones': showCustomerZonesLayer.value,
            'server-racks': showServerRacksLayer.value,
            'cooling-units': showCoolingUnitsLayer.value,
            'cooling-tiles': showCoolingTilesLayer.value,
            'pdu-ppc': showPDULayer.value,
            'other': showOtherLayer.value,
            'grid': showGridLayer.value
          },
          lastModified: new Date().toISOString(),
          objectCount: objectCount.value
        }
        
        localStorage.setItem('floorPlans', JSON.stringify(floorPlans))
        ElMessage.success('Floor plan saved successfully')
      } else {
        ElMessage.warning('No floor plan to save. Please import an SVG first.')
      }
    }

    // Load existing floor plan
    const loadFloorPlan = () => {
      const floorPlans = JSON.parse(localStorage.getItem('floorPlans') || '{}')
      const floorId = route.params.id
      
      if (floorPlans[floorId]) {
        const savedPlan = floorPlans[floorId]
        
        // Check if this is the new format with originalSVG
        if (savedPlan.originalSVG) {
          console.log('Loading floor plan with new format:', floorId)
          
          // Set the original SVG content
          originalSVGContent = savedPlan.originalSVG
          
          // Load the original SVG without regenerating grid
          parseSVGContent(savedPlan.originalSVG, true)
          
          // Restore coordinate labels
          if (savedPlan.coordinateLabels) {
            coordinateLabels = savedPlan.coordinateLabels
          }
          
          // Generate grid with saved coordinates
          generateGrid()
          
          // Restore grid offset
          if (savedPlan.gridOffset) {
            gridOffset = savedPlan.gridOffset
            if (gridLayer) {
              gridLayer.translate(gridOffset.x, gridOffset.y)
            }
          }
          
          // Send grid to back
          if (gridLayer) {
            gridLayer.back()
            gridLayer.addClass('non-draggable')
          }
          
          // Wait for elements to be organized before applying transforms
          setTimeout(() => {
            // Restore element transforms
            if (savedPlan.elementStates) {
              savedPlan.elementStates.forEach(state => {
                const groups = svgDraw.find('g')
                const group = groups.find(g => g.data('element-id') === state.id)
                if (group && state.transform) {
                  group.transform(state.transform)
                }
              })
            }
            
            // Restore layer visibility
            if (savedPlan.layerVisibility) {
              showFloorShapeLayer.value = savedPlan.layerVisibility['floor-shape'] ?? true
              showCustomerZonesLayer.value = savedPlan.layerVisibility['customer-zones'] ?? true
              showServerRacksLayer.value = savedPlan.layerVisibility['server-racks'] ?? true
              showCoolingUnitsLayer.value = savedPlan.layerVisibility['cooling-units'] ?? true
              showCoolingTilesLayer.value = savedPlan.layerVisibility['cooling-tiles'] ?? true
              showPDULayer.value = savedPlan.layerVisibility['pdu-ppc'] ?? true
              showOtherLayer.value = savedPlan.layerVisibility['other'] ?? true
              showGridLayer.value = savedPlan.layerVisibility['grid'] ?? true
              
              // Apply visibility
              Object.keys(savedPlan.layerVisibility).forEach(layer => {
                toggleLayer(layer)
              })
            }
            
            // Set up interactions after loading
            setupInteractions()
            
            // Fit to screen
            setTimeout(() => {
              fitToScreen()
            }, 100)
          }, 100)
          
        } else if (savedPlan.svgData) {
          // Old format - just load the SVG as before
          console.log('Loading floor plan with old format:', floorId)
          parseSVGContent(savedPlan.svgData)
        }
      }
    }

    // Initialize on mount
    onMounted(() => {
      const floors = JSON.parse(localStorage.getItem('floors') || '[]')
      const sites = JSON.parse(localStorage.getItem('sites') || '[]')
      const floorId = parseInt(route.params.id)
      
      console.log('Looking for floor with ID:', floorId)
      const floor = floors.find(f => f.id === floorId || f.id === String(floorId))
      
      if (floor) {
        console.log('Found floor:', floor)
        const site = sites.find(s => s.id === floor.siteId)
        siteName.value = site ? site.name : 'Unknown Site'
        floorName.value = floor.name
      } else {
        console.log('Floor not found. Available floors:', floors)
        siteName.value = 'Unknown Site'
        floorName.value = 'Unknown Floor'
      }
      
      initSVGCanvas()
      // Wait for next tick to ensure SVG canvas is initialized before loading floor plan
      nextTick(() => {
        loadFloorPlan()
      })
    })

    return {
      svgContainer,
      svgFileInput,
      objectCount,
      selectedObject,
      siteName,
      floorName,
      importStatus,
      zoomLevel,
      showFloorShapeLayer,
      showCustomerZonesLayer,
      showServerRacksLayer,
      showCoolingUnitsLayer,
      showCoolingTilesLayer,
      showPDULayer,
      showOtherLayer,
      showGridLayer,
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