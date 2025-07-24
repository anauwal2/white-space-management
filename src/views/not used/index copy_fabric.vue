<template>
  <div class="floor-plan-container">
    <div class="toolbar">
      <el-button type="primary" @click="importSVG">Import SVG</el-button>
      <el-button @click="toggleGrid">{{ gridVisible ? 'Hide Grid' : 'Show Grid' }}</el-button>
      <el-button @click="clearCanvas">Clear Canvas</el-button>
      <input 
        ref="fileInput" 
        type="file" 
        accept=".svg" 
        @change="handleFileSelect" 
        style="display: none;"
      />
    </div>
    <div class="canvas-container">
      <canvas ref="fabricCanvas" id="floor-plan-canvas"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { fabric } from 'fabric'

const fabricCanvas = ref(null)
const fileInput = ref(null)
const gridVisible = ref(true)

let canvas = null
let gridElements = []
let coordinateLabels = {
  top: [],
  bottom: [],
  left: [],
  right: []
}

const CANVAS_WIDTH = 1920
const CANVAS_HEIGHT = 1080

onMounted(() => {
  initializeCanvas()
  createDemoGrid()
})

onBeforeUnmount(() => {
  if (canvas) {
    canvas.dispose()
  }
})

function initializeCanvas() {
  canvas = new fabric.Canvas(fabricCanvas.value, {
    width: CANVAS_WIDTH,
    height: CANVAS_HEIGHT,
    backgroundColor: '#ffffff',
    selection: true
  })

  canvas.on('mouse:wheel', function(opt) {
    const delta = opt.e.deltaY
    let zoom = canvas.getZoom()
    zoom *= 0.999 ** delta
    
    if (zoom > 20) zoom = 20
    if (zoom < 0.01) zoom = 0.01
    
    canvas.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom)
    opt.e.preventDefault()
    opt.e.stopPropagation()
  })

  canvas.on('mouse:down', function(opt) {
    const evt = opt.e
    if (evt.altKey === true) {
      this.isDragging = true
      this.selection = false
      this.lastPosX = evt.clientX
      this.lastPosY = evt.clientY
    }
  })

  canvas.on('mouse:move', function(opt) {
    if (this.isDragging) {
      const e = opt.e
      const vpt = this.viewportTransform
      vpt[4] += e.clientX - this.lastPosX
      vpt[5] += e.clientY - this.lastPosY
      this.requestRenderAll()
      this.lastPosX = e.clientX
      this.lastPosY = e.clientY
    }
  })

  canvas.on('mouse:up', function(opt) {
    this.setViewportTransform(this.viewportTransform)
    this.isDragging = false
    this.selection = true
  })
}

// Create demo grid with coordinate labels like the sample
function createDemoGrid() {
  // Set up demo coordinate labels like AA, AB, AC, etc.
  coordinateLabels = {
    top: [
      { label: 'AA', x: 150, y: 50 },
      { label: 'AB', x: 250, y: 50 },
      { label: 'AC', x: 350, y: 50 },
      { label: 'AD', x: 450, y: 50 },
      { label: 'AE', x: 550, y: 50 }
    ],
    bottom: [
      { label: 'AA', x: 150, y: 750 },
      { label: 'AB', x: 250, y: 750 },
      { label: 'AC', x: 350, y: 750 },
      { label: 'AD', x: 450, y: 750 },
      { label: 'AE', x: 550, y: 750 }
    ],
    left: [
      { label: '35', x: 50, y: 150 },
      { label: '34', x: 50, y: 250 },
      { label: '33', x: 50, y: 350 },
      { label: '32', x: 50, y: 450 },
      { label: '31', x: 50, y: 550 }
    ],
    right: [
      { label: '35', x: 650, y: 150 },
      { label: '34', x: 650, y: 250 },
      { label: '33', x: 650, y: 350 },
      { label: '32', x: 650, y: 450 },
      { label: '31', x: 650, y: 550 }
    ]
  }
  
  generateGrid()
}

// Remove coordinate labels from SVG before import (comprehensive removal)
function removeCoordinateLabels(svgText) {
  // Remove all column coordinate labels (AA, AB, AC, BA, BB, etc.)
  svgText = svgText.replace(/<text[^>]*>[A-Z]{2}<\/text>/g, '')
  
  // Remove all row coordinate labels (numbers like 30, 31, 32, etc.)
  svgText = svgText.replace(/<text[^>]*>\d{1,2}<\/text>/g, '')
  
  // Remove any remaining text elements that might be coordinate labels
  svgText = svgText.replace(/<text[^>]*x="[^"]*"[^>]*y="[^"]*"[^>]*>[A-Z]{1,2}\d*<\/text>/g, '')
  svgText = svgText.replace(/<text[^>]*y="[^"]*"[^>]*x="[^"]*"[^>]*>[A-Z]{1,2}\d*<\/text>/g, '')
  
  console.log('Removed all coordinate labels from SVG')
  return svgText
}

// Detect coordinate labels from original SVG dynamically
function detectCoordinateLabels(originalSVGText) {
  coordinateLabels = { top: [], bottom: [], left: [], right: [] }
  
  console.log('Starting coordinate detection from SVG...')
  
  // Parse SVG to get dimensions and analyze structure
  const parser = new DOMParser()
  const svgDoc = parser.parseFromString(originalSVGText, 'image/svg+xml')
  const svgRoot = svgDoc.documentElement
  
  // Get SVG dimensions for better positioning logic
  const svgWidth = parseFloat(svgRoot.getAttribute('width') || '3660')
  const svgHeight = parseFloat(svgRoot.getAttribute('height') || '1417')
  
  console.log('SVG dimensions:', svgWidth, 'x', svgHeight)
  
  // More comprehensive regex patterns for coordinate detection
  const patterns = [
    // Pattern 1: Standard text elements with coordinates
    /<text[^>]*(?:x="([^"]*)"[^>]*y="([^"]*)"[^>]*>([A-Z]{2})<\/text>|y="([^"]*)"[^>]*x="([^"]*)"[^>]*>([A-Z]{2})<\/text>)/g,
    // Pattern 2: Text with transforms
    /<text[^>]*transform="[^"]*"[^>]*(?:x="([^"]*)"[^>]*y="([^"]*)"[^>]*>([A-Z]{2})<\/text>|y="([^"]*)"[^>]*x="([^"]*)"[^>]*>([A-Z]{2})<\/text>)/g,
    // Pattern 3: Numbers for rows
    /<text[^>]*(?:x="([^"]*)"[^>]*y="([^"]*)"[^>]*>(\d{1,2})<\/text>|y="([^"]*)"[^>]*x="([^"]*)"[^>]*>(\d{1,2})<\/text>)/g
  ]
  
  // Extract column labels (AA, AB, AC, BA, BB, BC, etc.)
  const columnLabelRegex = /<text[^>]*x="([^"]*)"[^>]*y="([^"]*)"[^>]*>([A-Z][A-Z])<\/text>/g
  let match
  
  while ((match = columnLabelRegex.exec(originalSVGText)) !== null) {
    let x = parseFloat(match[1])
    let y = parseFloat(match[2])
    const label = match[3]
    
    // Check for common transform patterns in SVG
    const transformMatch = originalSVGText.match(/matrix\(1,0,0,1,([^,]+),([^)]+)\)/)
    if (transformMatch) {
      const offsetX = parseFloat(transformMatch[1])
      const offsetY = parseFloat(transformMatch[2])
      x += offsetX
      y += offsetY
    }
    
    // Dynamic positioning logic based on SVG dimensions
    const topThreshold = svgHeight * 0.15  // Top 15% of SVG
    const bottomThreshold = svgHeight * 0.85  // Bottom 85% of SVG
    
    if (y <= topThreshold) {
      coordinateLabels.top.push({ label, x, y })
      console.log(`Found top column label: ${label} at (${x}, ${y})`)
    } else if (y >= bottomThreshold) {
      coordinateLabels.bottom.push({ label, x, y })
      console.log(`Found bottom column label: ${label} at (${x}, ${y})`)
    }
  }
  
  // Also check for column labels with y/x attribute order reversed
  const columnLabelRegex2 = /<text[^>]*y="([^"]*)"[^>]*x="([^"]*)"[^>]*>([A-Z][A-Z])<\/text>/g
  while ((match = columnLabelRegex2.exec(originalSVGText)) !== null) {
    let y = parseFloat(match[1])
    let x = parseFloat(match[2])
    const label = match[3]
    
    // Apply common transforms
    const transformMatch = originalSVGText.match(/matrix\(1,0,0,1,([^,]+),([^)]+)\)/)
    if (transformMatch) {
      const offsetX = parseFloat(transformMatch[1])
      const offsetY = parseFloat(transformMatch[2])
      x += offsetX
      y += offsetY
    }
    
    const topThreshold = svgHeight * 0.15
    const bottomThreshold = svgHeight * 0.85
    
    if (y <= topThreshold) {
      coordinateLabels.top.push({ label, x, y })
      console.log(`Found top column label (y,x): ${label} at (${x}, ${y})`)
    } else if (y >= bottomThreshold) {
      coordinateLabels.bottom.push({ label, x, y })
      console.log(`Found bottom column label (y,x): ${label} at (${x}, ${y})`)
    }
  }
  
  // Extract row labels (numbers like 34, 33, 32, 31, 30, etc.)
  const rowLabelRegex = /<text[^>]*x="([^"]*)"[^>]*y="([^"]*)"[^>]*>(\d{1,2})<\/text>/g
  
  while ((match = rowLabelRegex.exec(originalSVGText)) !== null) {
    let x = parseFloat(match[1])
    let y = parseFloat(match[2])
    const label = match[3]
    
    // Apply transforms
    const transformMatch = originalSVGText.match(/matrix\(1,0,0,1,([^,]+),([^)]+)\)/)
    if (transformMatch) {
      const offsetX = parseFloat(transformMatch[1])
      const offsetY = parseFloat(transformMatch[2])
      x += offsetX
      y += offsetY
    }
    
    // Dynamic positioning logic for rows
    const leftThreshold = svgWidth * 0.15   // Left 15% of SVG
    const rightThreshold = svgWidth * 0.85  // Right 85% of SVG
    
    if (x <= leftThreshold) {
      coordinateLabels.left.push({ label, x, y })
      console.log(`Found left row label: ${label} at (${x}, ${y})`)
    } else if (x >= rightThreshold) {
      coordinateLabels.right.push({ label, x, y })
      console.log(`Found right row label: ${label} at (${x}, ${y})`)
    }
  }
  
  // Also check for row labels with y/x attribute order reversed
  const rowLabelRegex2 = /<text[^>]*y="([^"]*)"[^>]*x="([^"]*)"[^>]*>(\d{1,2})<\/text>/g
  while ((match = rowLabelRegex2.exec(originalSVGText)) !== null) {
    let y = parseFloat(match[1])
    let x = parseFloat(match[2])
    const label = match[3]
    
    // Apply transforms
    const transformMatch = originalSVGText.match(/matrix\(1,0,0,1,([^,]+),([^)]+)\)/)
    if (transformMatch) {
      const offsetX = parseFloat(transformMatch[1])
      const offsetY = parseFloat(transformMatch[2])
      x += offsetX
      y += offsetY
    }
    
    const leftThreshold = svgWidth * 0.15
    const rightThreshold = svgWidth * 0.85
    
    if (x <= leftThreshold) {
      coordinateLabels.left.push({ label, x, y })
      console.log(`Found left row label (y,x): ${label} at (${x}, ${y})`)
    } else if (x >= rightThreshold) {
      coordinateLabels.right.push({ label, x, y })
      console.log(`Found right row label (y,x): ${label} at (${x}, ${y})`)
    }
  }
  
  // Remove duplicates and sort coordinates
  coordinateLabels.top = removeDuplicateCoords(coordinateLabels.top).sort((a, b) => a.x - b.x)
  coordinateLabels.bottom = removeDuplicateCoords(coordinateLabels.bottom).sort((a, b) => a.x - b.x)
  coordinateLabels.left = removeDuplicateCoords(coordinateLabels.left).sort((a, b) => b.y - a.y) // Top to bottom
  coordinateLabels.right = removeDuplicateCoords(coordinateLabels.right).sort((a, b) => b.y - a.y) // Top to bottom
  
  console.log('Final detected coordinates:', {
    top: coordinateLabels.top.length + ' labels',
    bottom: coordinateLabels.bottom.length + ' labels', 
    left: coordinateLabels.left.length + ' labels',
    right: coordinateLabels.right.length + ' labels'
  })
  console.log('Coordinate details:', coordinateLabels)
}

// Helper function to remove duplicate coordinates
function removeDuplicateCoords(coords) {
  const unique = []
  coords.forEach(coord => {
    if (!unique.find(c => Math.abs(c.x - coord.x) < 5 && Math.abs(c.y - coord.y) < 5 && c.label === coord.label)) {
      unique.push(coord)
    }
  })
  return unique
}

// Generate grid based on detected coordinates (dynamic)
function generateGrid() {
  // Clear existing grid
  clearGrid()
  
  console.log('Generating grid with coordinates:', coordinateLabels)
  
  // If no coordinates detected, fall back to demo grid
  if (coordinateLabels.top.length === 0 && coordinateLabels.left.length === 0) {
    console.log('No coordinates detected, using demo grid')
    createDemoGrid()
    return
  }
  
  // Calculate precise grid boundaries based on detected coordinates
  let topY, bottomY, leftX, rightX
  
  // Determine vertical boundaries (top/bottom)
  if (coordinateLabels.top.length > 0 && coordinateLabels.bottom.length > 0) {
    // Use actual coordinate positions when both top and bottom are available
    topY = Math.min(...coordinateLabels.top.map(c => c.y)) + 30
    bottomY = Math.max(...coordinateLabels.bottom.map(c => c.y)) - 10
  } else if (coordinateLabels.top.length > 0) {
    topY = Math.min(...coordinateLabels.top.map(c => c.y)) + 30
    bottomY = topY + 600 // Reasonable grid height
  } else if (coordinateLabels.bottom.length > 0) {
    bottomY = Math.max(...coordinateLabels.bottom.map(c => c.y)) - 10
    topY = bottomY - 600 // Reasonable grid height
  } else {
    topY = 100
    bottomY = CANVAS_HEIGHT - 100
  }
  
  // Determine horizontal boundaries (left/right)
  if (coordinateLabels.left.length > 0 && coordinateLabels.right.length > 0) {
    // Use actual coordinate positions when both left and right are available
    leftX = Math.min(...coordinateLabels.left.map(c => c.x)) + 40
    rightX = Math.max(...coordinateLabels.right.map(c => c.x)) - 10
  } else if (coordinateLabels.left.length > 0) {
    leftX = Math.min(...coordinateLabels.left.map(c => c.x)) + 40
    rightX = leftX + 800 // Reasonable grid width
  } else if (coordinateLabels.right.length > 0) {
    rightX = Math.max(...coordinateLabels.right.map(c => c.x)) - 10
    leftX = rightX - 800 // Reasonable grid width
  } else {
    leftX = 100
    rightX = CANVAS_WIDTH - 100
  }
  
  console.log('Grid boundaries:', { topY, bottomY, leftX, rightX })
  
  // Generate vertical grid lines (columns) - more accurate positioning
  if (coordinateLabels.top.length > 0) {
    const columns = coordinateLabels.top.sort((a, b) => a.x - b.x)
    
    // Add grid lines between each column coordinate
    for (let i = 0; i < columns.length; i++) {
      const currentX = columns[i].x
      
      // Create a vertical line at each coordinate position
      const line = new fabric.Line([currentX, topY, currentX, bottomY], {
        stroke: '#ddd',
        strokeWidth: 1,
        strokeDashArray: [2, 2],
        selectable: false,
        evented: false,
        excludeFromExport: true,
        isGridElement: true
      })
      
      canvas.add(line)
      canvas.sendToBack(line)
      gridElements.push(line)
    }
    
    // Add additional grid lines between coordinates for finer grid
    for (let i = 0; i < columns.length - 1; i++) {
      const currentX = columns[i].x
      const nextX = columns[i + 1].x
      const spacing = (nextX - currentX) / 2
      
      if (spacing > 20) { // Only add intermediate lines if there's enough space
        const midX = currentX + spacing
        const midLine = new fabric.Line([midX, topY, midX, bottomY], {
          stroke: '#eee',
          strokeWidth: 0.5,
          strokeDashArray: [1, 3],
          selectable: false,
          evented: false,
          excludeFromExport: true,
          isGridElement: true
        })
        
        canvas.add(midLine)
        canvas.sendToBack(midLine)
        gridElements.push(midLine)
      }
    }
  }
  
  // Generate horizontal grid lines (rows) - more accurate positioning
  if (coordinateLabels.left.length > 0) {
    const rows = coordinateLabels.left.sort((a, b) => a.y - b.y)
    
    // Add grid lines at each row coordinate
    for (let i = 0; i < rows.length; i++) {
      const currentY = rows[i].y
      
      // Create a horizontal line at each coordinate position
      const line = new fabric.Line([leftX, currentY, rightX, currentY], {
        stroke: '#ddd',
        strokeWidth: 1,
        strokeDashArray: [2, 2],
        selectable: false,
        evented: false,
        excludeFromExport: true,
        isGridElement: true
      })
      
      canvas.add(line)
      canvas.sendToBack(line)
      gridElements.push(line)
    }
    
    // Add additional grid lines between coordinates for finer grid
    for (let i = 0; i < rows.length - 1; i++) {
      const currentY = rows[i].y
      const nextY = rows[i + 1].y
      const spacing = Math.abs(nextY - currentY) / 2
      
      if (spacing > 20) { // Only add intermediate lines if there's enough space
        const midY = currentY + (nextY - currentY) / 2
        const midLine = new fabric.Line([leftX, midY, rightX, midY], {
          stroke: '#eee',
          strokeWidth: 0.5,
          strokeDashArray: [1, 3],
          selectable: false,
          evented: false,
          excludeFromExport: true,
          isGridElement: true
        })
        
        canvas.add(midLine)
        canvas.sendToBack(midLine)
        gridElements.push(midLine)
      }
    }
  }
  
  // Add coordinate labels
  addCoordinateLabels()
  
  // Add tile coordinates to cells
  addTileCoordinates()
  
  console.log('Grid generated with', gridElements.length, 'elements')
}

// Add coordinate labels to the grid
function addCoordinateLabels() {
  // Add top labels
  coordinateLabels.top.forEach(coord => {
    const text = new fabric.Text(coord.label, {
      left: coord.x - 10,
      top: coord.y - 20,
      fontSize: 16,
      fontFamily: 'Tahoma',
      fontWeight: 'bold',
      fill: '#666',
      selectable: false,
      evented: false,
      excludeFromExport: true,
      isGridElement: true
    })
    canvas.add(text)
    canvas.sendToBack(text)
    gridElements.push(text)
  })
  
  // Add bottom labels
  coordinateLabels.bottom.forEach(coord => {
    const text = new fabric.Text(coord.label, {
      left: coord.x - 10,
      top: coord.y + 5,
      fontSize: 16,
      fontFamily: 'Tahoma',
      fontWeight: 'bold',
      fill: '#666',
      selectable: false,
      evented: false,
      excludeFromExport: true,
      isGridElement: true
    })
    canvas.add(text)
    canvas.sendToBack(text)
    gridElements.push(text)
  })
  
  // Add left labels
  coordinateLabels.left.forEach(coord => {
    const text = new fabric.Text(coord.label, {
      left: coord.x - 30,
      top: coord.y - 8,
      fontSize: 16,
      fontFamily: 'Tahoma',
      fontWeight: 'bold',
      fill: '#666',
      selectable: false,
      evented: false,
      excludeFromExport: true,
      isGridElement: true
    })
    canvas.add(text)
    canvas.sendToBack(text)
    gridElements.push(text)
  })
  
  // Add right labels
  coordinateLabels.right.forEach(coord => {
    const text = new fabric.Text(coord.label, {
      left: coord.x + 5,
      top: coord.y - 8,
      fontSize: 16,
      fontFamily: 'Tahoma',
      fontWeight: 'bold',
      fill: '#666',
      selectable: false,
      evented: false,
      excludeFromExport: true,
      isGridElement: true
    })
    canvas.add(text)
    canvas.sendToBack(text)
    gridElements.push(text)
  })
}

// Add tile coordinates to each cell (like AA-35, AB-34, etc.)
function addTileCoordinates() {
  const columns = coordinateLabels.top.length > 0 ? coordinateLabels.top : coordinateLabels.bottom
  const rows = coordinateLabels.left.length > 0 ? coordinateLabels.left : coordinateLabels.right
  
  if (columns.length === 0 || rows.length === 0) return
  
  // Sort coordinates to ensure proper ordering
  const sortedColumns = [...columns].sort((a, b) => a.x - b.x)
  const sortedRows = [...rows].sort((a, b) => a.y - b.y)
  
  sortedColumns.forEach((col, colIndex) => {
    sortedRows.forEach((row, rowIndex) => {
      const tileCoordinate = `${col.label}-${row.label}`
      
      // Calculate precise positioning for tile coordinates
      const tileX = col.x - 18
      const tileY = row.y - 8
      
      const text = new fabric.Text(tileCoordinate, {
        left: tileX,
        top: tileY,
        fontSize: 9,
        fontFamily: 'Arial',
        fill: '#888',
        selectable: false,
        evented: false,
        excludeFromExport: true,
        isGridElement: true,
        opacity: 0.7
      })
      canvas.add(text)
      canvas.sendToBack(text)
      gridElements.push(text)
    })
  })
  
  console.log('Added tile coordinates for', sortedColumns.length * sortedRows.length, 'cells')
}

function clearGrid() {
  gridElements.forEach(element => {
    canvas.remove(element)
  })
  gridElements = []
}

function toggleGrid() {
  gridElements.forEach(element => {
    element.visible = !element.visible
  })
  gridVisible.value = !gridVisible.value
  canvas.requestRenderAll()
}

function importSVG() {
  fileInput.value.click()
}

function handleFileSelect(event) {
  const file = event.target.files[0]
  if (!file || file.type !== 'image/svg+xml') {
    console.error('Please select a valid SVG file')
    return
  }

  const reader = new FileReader()
  reader.onload = function(e) {
    const svgString = e.target.result
    loadSVGToCanvas(svgString)
  }
  reader.readAsText(file)
}

function loadSVGToCanvas(svgString) {
  console.log('=== STARTING SVG IMPORT WITH DYNAMIC COORDINATE DETECTION ===')
  
  // Step 1: Detect coordinates from original SVG BEFORE cleaning
  console.log('Step 1: Detecting coordinate labels from original SVG...')
  detectCoordinateLabels(svgString)
  
  // Check if we found any coordinates
  const totalCoords = coordinateLabels.top.length + coordinateLabels.bottom.length + 
                     coordinateLabels.left.length + coordinateLabels.right.length
  
  if (totalCoords === 0) {
    console.log('⚠️  No coordinate labels detected in SVG!')
    console.log('SVG might not contain coordinate labels or they might be in a different format.')
  } else {
    console.log(`✅ Successfully detected ${totalCoords} coordinate labels!`)
  }
  
  // Step 2: Remove coordinate labels before loading
  console.log('Step 2: Cleaning coordinate labels before import...')
  const cleanedSVG = removeCoordinateLabels(svgString)
  
  // Step 3: Load cleaned SVG into Fabric.js
  console.log('Step 3: Loading cleaned SVG into Fabric.js canvas...')
  fabric.loadSVGFromString(cleanedSVG, (objects, options) => {
    // Clear existing objects except grid
    canvas.getObjects().forEach(obj => {
      if (!obj.isGridElement) {
        canvas.remove(obj)
      }
    })
    
    console.log(`Loaded ${objects.length} SVG objects`)
    
    // Add SVG objects
    objects.forEach((obj, index) => {
      obj.set({
        selectable: true,
        evented: true,
        id: `svg-object-${index}`
      })
      canvas.add(obj)
    })
    
    // Step 4: Generate grid with detected coordinates
    console.log('Step 4: Generating coordinate-based grid...')
    generateGrid()
    
    canvas.requestRenderAll()
    console.log('=== SVG IMPORT COMPLETE ===')
    
    if (totalCoords > 0) {
      console.log('🎉 Dynamic grid generated based on detected coordinates!')
    } else {
      console.log('📋 Using demo grid (no coordinates detected)')
    }
  })
}

function clearCanvas() {
  canvas.getObjects().forEach(obj => {
    if (!obj.isGridElement) {
      canvas.remove(obj)
    }
  })
  canvas.requestRenderAll()
}
</script>

<style scoped>
.floor-plan-container {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
}

.toolbar {
  padding: 10px;
  background-color: #ffffff;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  gap: 10px;
}

.canvas-container {
  flex: 1;
  padding: 20px;
  overflow: hidden;
}

#floor-plan-canvas {
  border: 1px solid #ccc;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>