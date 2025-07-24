<template>
  <div class="floor-plan-page">
    <div class="page-header">
      <h2>{{ siteName }} - {{ floorName }} (Fabric.js Version)</h2>
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
        <canvas 
          ref="fabricCanvas" 
          id="fabric-canvas"
          class="fabric-canvas"
        ></canvas>
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
            <el-checkbox v-model="gridVisible" @change="toggleGrid">
              Show Grid
            </el-checkbox>
          </div>

          <div class="control-group">
            <label>Object Count:</label>
            <el-text tag="small">{{ objectCount }}</el-text>
          </div>

          <div class="control-group">
            <label>Status:</label>
            <el-text tag="small">{{ importStatus }}</el-text>
          </div>

          <div class="control-group">
            <label>Zoom Controls:</label>
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
            <span>Grid Settings</span>
          </template>
          
          <div class="control-group">
            <label>Grid Size:</label>
            <el-input-number 
              v-model="gridSize" 
              :min="10" 
              :max="100" 
              @change="updateGrid"
              size="small"
            />
          </div>

          <div class="control-group">
            <label>Grid Color:</label>
            <input 
              type="color" 
              v-model="gridColor" 
              @change="updateGrid"
              class="color-picker"
            />
          </div>

          <div class="control-group">
            <el-checkbox v-model="showCoordinates" @change="updateGrid">
              Show Coordinates
            </el-checkbox>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fabric } from 'fabric'

export default {
  name: 'FloorPlanFabric',
  setup() {
    const route = useRoute()
    
    // Refs
    const fabricCanvas = ref(null)
    const svgFileInput = ref(null)
    const objectCount = ref(0)
    const siteName = ref('')
    const floorName = ref('')
    const importStatus = ref('Ready')
    const zoomLevel = ref(1)
    const gridVisible = ref(true)
    const gridSize = ref(36)
    const gridColor = ref('#dddddd')
    const showCoordinates = ref(true)
    
    // Internal state
    let canvas = null
    let gridGroup = null
    let coordinateLabels = {
      top: [],
      bottom: [],
      left: [],
      right: []
    }
    
    const initFabricCanvas = () => {
      nextTick(() => {
        if (fabricCanvas.value) {
          canvas = new fabric.Canvas('fabric-canvas', {
            width: fabricCanvas.value.parentElement.clientWidth,
            height: fabricCanvas.value.parentElement.clientHeight,
            backgroundColor: '#ffffff'
          })
          
          // Enable zoom and pan
          canvas.on('mouse:wheel', handleMouseWheel)
          canvas.on('mouse:down', handleMouseDown)
          canvas.on('mouse:move', handleMouseMove)
          canvas.on('mouse:up', handleMouseUp)
          
          // Track object count
          canvas.on('object:added', updateObjectCount)
          canvas.on('object:removed', updateObjectCount)
          
          // Initial grid
          generateGrid()
        }
      })
    }

    let isPanning = false
    let lastPosX = 0
    let lastPosY = 0

    const handleMouseDown = (opt) => {
      const evt = opt.e
      if (evt.altKey || evt.button === 1) { // Alt key or middle mouse button for panning
        isPanning = true
        canvas.selection = false
        lastPosX = evt.clientX
        lastPosY = evt.clientY
        canvas.defaultCursor = 'grabbing'
      }
    }

    const handleMouseMove = (opt) => {
      if (isPanning) {
        const evt = opt.e
        const vpt = canvas.viewportTransform
        vpt[4] += evt.clientX - lastPosX
        vpt[5] += evt.clientY - lastPosY
        canvas.requestRenderAll()
        lastPosX = evt.clientX
        lastPosY = evt.clientY
      }
    }

    const handleMouseUp = () => {
      if (isPanning) {
        isPanning = false
        canvas.selection = true
        canvas.defaultCursor = 'default'
      }
    }

    const handleMouseWheel = (opt) => {
      const delta = opt.e.deltaY
      let zoom = canvas.getZoom()
      zoom *= 0.999 ** delta
      if (zoom > 20) zoom = 20
      if (zoom < 0.01) zoom = 0.01
      
      canvas.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom)
      zoomLevel.value = zoom
      opt.e.preventDefault()
      opt.e.stopPropagation()
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

    const parseSVGContent = (svgText) => {
      try {
        importStatus.value = 'Loading SVG...'
        
        if (!canvas) {
          ElMessage.error('Canvas not initialized')
          return
        }
        
        // Clear existing objects except grid
        clearCanvasExceptGrid()
        
        // Extract coordinate labels before cleaning
        extractCoordinateLabels(svgText)
        
        // Clean SVG text (remove coordinate labels)
        const cleanedSVGText = removeCoordinateLabels(svgText)
        
        // Load SVG into Fabric.js
        fabric.loadSVGFromString(cleanedSVGText, (objects, options) => {
          const svgGroup = fabric.util.groupSVGElements(objects, options)
          
          // Position the SVG
          svgGroup.set({
            left: 50,
            top: 50,
            selectable: true,
            evented: true
          })
          
          canvas.add(svgGroup)
          canvas.renderAll()
          
          // Generate grid based on extracted coordinates
          generateGrid()
          
          // Fit to screen
          fitToScreen()
          
          importStatus.value = 'Complete'
          ElMessage.success('SVG imported successfully')
        })
        
      } catch (error) {
        console.error('Error processing SVG:', error)
        ElMessage.error('Failed to process SVG: ' + error.message)
        importStatus.value = 'Error'
      }
    }

    const removeCoordinateLabels = (svgText) => {
      const patterns = [
        /<text[^>]*x="[^"]*"\s+y="164"[^>]*>[A-Z][A-Z]<\/text>/g,
        /<text[^>]*y="164"\s+x="[^"]*"[^>]*>[A-Z][A-Z]<\/text>/g,
        /<text[^>]*x="[^"]*"\s+y="(1[4-9][0-9][0-9]|[2-9][0-9][0-9][0-9])"[^>]*>[A-Z][A-Z]<\/text>/g,
        /<text[^>]*y="(1[4-9][0-9][0-9]|[2-9][0-9][0-9][0-9])"\s+x="[^"]*"[^>]*>[A-Z][A-Z]<\/text>/g,
        /<text[^>]*x="-?\d+"\s+y="[^"]*"[^>]*>\d{1,2}<\/text>/g,
        /<text[^>]*y="[^"]*"\s+x="-?\d+"[^>]*>\d{1,2}<\/text>/g
      ]
      
      return patterns.reduce((text, pattern) => text.replace(pattern, ''), svgText)
    }

    const extractCoordinateLabels = (svgText) => {
      coordinateLabels = {
        top: [],
        bottom: [],
        left: [],
        right: []
      }
      
      // Extract column labels (letters)
      const columnLabelRegex = /<text[^>]*x="([^"]*)"[^>]*y="([^"]*)"[^>]*>([A-Z][A-Z])<\/text>/g
      let match
      
      while ((match = columnLabelRegex.exec(svgText)) !== null) {
        const x = parseFloat(match[1]) + 98
        const y = parseFloat(match[2]) - 84
        const label = match[3]
        
        if (y < 200) {
          coordinateLabels.top.push({ x, y, label })
        } else if (y > 1300) {
          coordinateLabels.bottom.push({ x, y, label })
        }
      }
      
      // Extract row labels (numbers)
      const rowLabelRegex = /<text[^>]*x="([^"]*)"[^>]*y="([^"]*)"[^>]*>(\d{1,2})<\/text>/g
      
      while ((match = rowLabelRegex.exec(svgText)) !== null) {
        const x = parseFloat(match[1]) + 98
        const y = parseFloat(match[2]) - 84
        const label = match[3]
        
        if (x < 200) {
          coordinateLabels.left.push({ x, y, label })
        } else if (x > 3400) {
          coordinateLabels.right.push({ x, y, label })
        }
      }
      
      // Sort coordinates
      coordinateLabels.top.sort((a, b) => a.x - b.x)
      coordinateLabels.bottom.sort((a, b) => a.x - b.x)
      coordinateLabels.left.sort((a, b) => b.y - a.y)
      coordinateLabels.right.sort((a, b) => b.y - a.y)
    }

    const generateGrid = () => {
      if (!canvas) return
      
      // Remove existing grid
      if (gridGroup) {
        canvas.remove(gridGroup)
      }
      
      if (!gridVisible.value) return
      
      const gridLines = []
      const labels = []
      
      // Determine grid boundaries
      const canvasWidth = canvas.width
      const canvasHeight = canvas.height
      
      // If we have coordinate labels, use them to create accurate grid
      if (coordinateLabels.top.length > 0 || coordinateLabels.left.length > 0) {
        generateCoordinateBasedGrid(gridLines, labels)
      } else {
        generateRegularGrid(gridLines, labels, canvasWidth, canvasHeight)
      }
      
      // Create grid group
      gridGroup = new fabric.Group([...gridLines, ...labels], {
        selectable: false,
        evented: false,
        excludeFromExport: true
      })
      
      canvas.add(gridGroup)
      canvas.sendToBack(gridGroup)
      canvas.renderAll()
    }

    const generateCoordinateBasedGrid = (gridLines, labels) => {
      const offset = { x: 50, y: 50 } // Offset to match SVG positioning
      
      // Vertical lines based on column coordinates
      if (coordinateLabels.top.length > 0) {
        coordinateLabels.top.forEach((coord, index) => {
          const x = coord.x + offset.x
          const line = new fabric.Line([x, 0, x, canvas.height], {
            stroke: gridColor.value,
            strokeWidth: 1,
            strokeDashArray: [5, 5],
            selectable: false,
            evented: false
          })
          gridLines.push(line)
          
          if (showCoordinates.value) {
            const label = new fabric.Text(coord.label, {
              left: x - 10,
              top: 10,
              fontSize: 12,
              fill: '#666',
              selectable: false,
              evented: false
            })
            labels.push(label)
          }
        })
      }
      
      // Horizontal lines based on row coordinates
      if (coordinateLabels.left.length > 0) {
        coordinateLabels.left.forEach((coord, index) => {
          const y = coord.y + offset.y
          const line = new fabric.Line([0, y, canvas.width, y], {
            stroke: gridColor.value,
            strokeWidth: 1,
            strokeDashArray: [5, 5],
            selectable: false,
            evented: false
          })
          gridLines.push(line)
          
          if (showCoordinates.value) {
            const label = new fabric.Text(coord.label, {
              left: 10,
              top: y - 6,
              fontSize: 12,
              fill: '#666',
              selectable: false,
              evented: false
            })
            labels.push(label)
          }
        })
      }
    }

    const generateRegularGrid = (gridLines, labels, width, height) => {
      // Vertical lines
      for (let x = 0; x <= width; x += gridSize.value) {
        const line = new fabric.Line([x, 0, x, height], {
          stroke: gridColor.value,
          strokeWidth: 1,
          strokeDashArray: [5, 5],
          selectable: false,
          evented: false
        })
        gridLines.push(line)
        
        if (showCoordinates.value && x > 0) {
          const colIndex = Math.floor(x / gridSize.value)
          const colLabel = String.fromCharCode(65 + (colIndex - 1) % 26) + 
                          String.fromCharCode(65 + Math.floor((colIndex - 1) / 26))
          const label = new fabric.Text(colLabel, {
            left: x - 10,
            top: 5,
            fontSize: 10,
            fill: '#666',
            selectable: false,
            evented: false
          })
          labels.push(label)
        }
      }
      
      // Horizontal lines
      for (let y = 0; y <= height; y += gridSize.value) {
        const line = new fabric.Line([0, y, width, y], {
          stroke: gridColor.value,
          strokeWidth: 1,
          strokeDashArray: [5, 5],
          selectable: false,
          evented: false
        })
        gridLines.push(line)
        
        if (showCoordinates.value && y > 0) {
          const rowNumber = Math.floor(y / gridSize.value)
          const label = new fabric.Text(rowNumber.toString().padStart(2, '0'), {
            left: 5,
            top: y - 6,
            fontSize: 10,
            fill: '#666',
            selectable: false,
            evented: false
          })
          labels.push(label)
        }
      }
    }

    const toggleGrid = () => {
      generateGrid()
    }

    const updateGrid = () => {
      generateGrid()
    }

    const clearCanvas = () => {
      if (!canvas) return
      canvas.clear()
      coordinateLabels = { top: [], bottom: [], left: [], right: [] }
      generateGrid()
      importStatus.value = 'Ready'
    }

    const clearCanvasExceptGrid = () => {
      if (!canvas) return
      
      const objects = canvas.getObjects()
      objects.forEach(obj => {
        if (obj !== gridGroup) {
          canvas.remove(obj)
        }
      })
    }

    const updateObjectCount = () => {
      if (!canvas) return
      const objects = canvas.getObjects()
      objectCount.value = objects.filter(obj => obj !== gridGroup).length
    }

    const zoomIn = () => {
      if (!canvas) return
      const zoom = canvas.getZoom()
      canvas.setZoom(zoom * 1.2)
      zoomLevel.value = canvas.getZoom()
    }

    const zoomOut = () => {
      if (!canvas) return
      const zoom = canvas.getZoom()
      canvas.setZoom(zoom / 1.2)
      zoomLevel.value = canvas.getZoom()
    }

    const resetZoom = () => {
      if (!canvas) return
      canvas.setZoom(1)
      canvas.viewportTransform = [1, 0, 0, 1, 0, 0]
      canvas.renderAll()
      zoomLevel.value = 1
    }

    const fitToScreen = () => {
      if (!canvas) return
      
      const objects = canvas.getObjects().filter(obj => obj !== gridGroup)
      if (objects.length === 0) return
      
      // Get bounding box of all objects
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
      
      objects.forEach(obj => {
        const bound = obj.getBoundingRect()
        minX = Math.min(minX, bound.left)
        minY = Math.min(minY, bound.top)
        maxX = Math.max(maxX, bound.left + bound.width)
        maxY = Math.max(maxY, bound.top + bound.height)
      })
      
      const objectWidth = maxX - minX
      const objectHeight = maxY - minY
      
      const scaleX = (canvas.width * 0.8) / objectWidth
      const scaleY = (canvas.height * 0.8) / objectHeight
      const scale = Math.min(scaleX, scaleY)
      
      canvas.setZoom(scale)
      canvas.viewportTransform[4] = (canvas.width - objectWidth * scale) / 2 - minX * scale
      canvas.viewportTransform[5] = (canvas.height - objectHeight * scale) / 2 - minY * scale
      canvas.renderAll()
      
      zoomLevel.value = scale
    }

    const saveFloorPlan = () => {
      if (!canvas) {
        ElMessage.warning('No canvas to save')
        return
      }
      
      try {
        const floorPlanData = {
          canvasData: JSON.stringify(canvas.toJSON()),
          coordinateLabels,
          gridSettings: {
            visible: gridVisible.value,
            size: gridSize.value,
            color: gridColor.value,
            showCoordinates: showCoordinates.value
          },
          lastModified: new Date().toISOString(),
          objectCount: objectCount.value
        }
        
        const floorPlans = JSON.parse(localStorage.getItem('fabricFloorPlans') || '{}')
        floorPlans[route.params.id] = floorPlanData
        localStorage.setItem('fabricFloorPlans', JSON.stringify(floorPlans))
        
        ElMessage.success('Floor plan saved successfully')
      } catch (error) {
        console.error('Error saving floor plan:', error)
        ElMessage.error('Failed to save floor plan')
      }
    }

    const loadFloorPlan = () => {
      try {
        const floorPlans = JSON.parse(localStorage.getItem('fabricFloorPlans') || '{}')
        const savedPlan = floorPlans[route.params.id]
        
        if (!savedPlan) return
        
        // Load canvas data
        if (savedPlan.canvasData) {
          canvas.loadFromJSON(savedPlan.canvasData, () => {
            canvas.renderAll()
            
            // Restore coordinate labels
            if (savedPlan.coordinateLabels) {
              coordinateLabels = savedPlan.coordinateLabels
            }
            
            // Restore grid settings
            if (savedPlan.gridSettings) {
              gridVisible.value = savedPlan.gridSettings.visible
              gridSize.value = savedPlan.gridSettings.size
              gridColor.value = savedPlan.gridSettings.color
              showCoordinates.value = savedPlan.gridSettings.showCoordinates
            }
            
            // Regenerate grid
            generateGrid()
            
            ElMessage.success('Floor plan loaded successfully')
          })
        }
      } catch (error) {
        console.error('Error loading floor plan:', error)
        ElMessage.error('Failed to load floor plan')
      }
    }

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

    const handleResize = () => {
      if (canvas && fabricCanvas.value) {
        const container = fabricCanvas.value.parentElement
        canvas.setDimensions({
          width: container.clientWidth,
          height: container.clientHeight
        })
        canvas.renderAll()
        generateGrid()
      }
    }

    onMounted(() => {
      initializeFloorData()
      initFabricCanvas()
      nextTick(() => {
        loadFloorPlan()
        window.addEventListener('resize', handleResize)
      })
    })

    onUnmounted(() => {
      window.removeEventListener('resize', handleResize)
      if (canvas) {
        canvas.dispose()
      }
    })

    return {
      fabricCanvas,
      svgFileInput,
      objectCount,
      siteName,
      floorName,
      importStatus,
      zoomLevel,
      gridVisible,
      gridSize,
      gridColor,
      showCoordinates,
      triggerSVGInput,
      handleSVGImport,
      toggleGrid,
      updateGrid,
      clearCanvas,
      zoomIn,
      zoomOut,
      resetZoom,
      fitToScreen,
      saveFloorPlan
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

.fabric-canvas {
  display: block;
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

.zoom-info {
  text-align: center;
  margin-top: 8px;
  font-size: 14px;
  color: #666;
}

.color-picker {
  width: 100%;
  height: 32px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}
</style>