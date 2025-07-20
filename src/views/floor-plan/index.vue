<template>
  <div class="floor-plan-page">
    <div class="page-header">
      <h2>{{ siteName }} - {{ floorName }}</h2>
      <div class="header-actions">
        <el-button @click="$router.back()">
          <el-icon><Back /></el-icon>
          Back
        </el-button>
        <el-button type="primary" @click="importJSON">
          <el-icon><Document /></el-icon>
          Import JSON
        </el-button>
        <el-button type="success" @click="saveFloorPlan">
          <el-icon><Check /></el-icon>
          Save Plan
        </el-button>
      </div>
    </div>

    <div class="designer-container">
      <div class="canvas-container">
        <v-stage
          ref="stage"
          :config="stageConfig"
          @wheel="handleWheel"
          @mousedown="handleStageMouseDown"
          @mousemove="handleStageMouseMove"
          @mouseup="handleStageMouseUp"
        >
          <v-layer ref="layer">
            <!-- SVG objects will be rendered here as Konva objects -->
          </v-layer>
        </v-stage>
      </div>
      
      <div class="controls-panel">
        <el-card class="controls-card">
          <template #header>
            <span>Import Controls</span>
          </template>
          
          <div class="control-group">
            <el-button @click="triggerJSONInput" type="primary">
              <el-icon><Document /></el-icon>
              Select JSON File
            </el-button>
            <input 
              ref="jsonFileInput" 
              type="file" 
              accept=".json" 
              @change="handleJSONImport" 
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
            <label>Layer Controls:</label>
            <div class="layer-controls">
              <el-checkbox v-model="showFloorShapeLayer" @change="toggleFloorShapeLayer">
                Floor Shape
              </el-checkbox>
              <el-checkbox v-model="showServerRacksLayer" @change="toggleServerRacksLayer">
                Server Racks
              </el-checkbox>
              <el-checkbox v-model="showCoolingUnitsLayer" @change="toggleCoolingUnitsLayer">
                Cooling Units
              </el-checkbox>
              <el-checkbox v-model="showCoolingTilesLayer" @change="toggleCoolingTilesLayer">
                Cooling Tiles
              </el-checkbox>
              <el-checkbox v-model="showPDULayer" @change="togglePDULayer">
                PDUs/PPCs
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
              <span>{{ selectedObject.className }}</span>
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
            <div class="property-item">
              <label>Rotation:</label>
              <span>{{ selectedObject.rotation }}°</span>
            </div>
          </div>
          <div v-else class="no-selection">
            <el-text tag="small">No object selected</el-text>
            <el-text tag="small">Use mouse wheel to zoom</el-text>
            <el-text tag="small">Drag to pan</el-text>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import Konva from 'konva'

export default {
  name: 'FloorPlan',
  setup() {
    const stage = ref(null)
    const layer = ref(null)
    const jsonFileInput = ref(null)
    const objectCount = ref(0)
    const selectedObject = ref(null)
    const siteName = ref('')
    const floorName = ref('')
    const importStatus = ref('Ready')
    const zoomLevel = ref(1)
    const showFloorShapeLayer = ref(true)
    const showServerRacksLayer = ref(true)
    const showCoolingUnitsLayer = ref(true)
    const showCoolingTilesLayer = ref(true)
    const showPDULayer = ref(true)
    
    // Stage configuration
    const stageConfig = {
      width: 1200,
      height: 700,
      draggable: true
    }

    let transformer = null

    // Initialize stage and transformer
    const initStage = () => {
      nextTick(() => {
        if (stage.value && layer.value) {
          const konvaStage = stage.value.getNode()
          const konvaLayer = layer.value.getNode()
          
          // Create transformer for resize/rotate handles
          transformer = new Konva.Transformer({
            enabledAnchors: ['top-left', 'top-center', 'top-right', 'middle-right', 'middle-left', 'bottom-left', 'bottom-center', 'bottom-right'],
            boundBoxFunc: (oldBox, newBox) => {
              // Limit minimum size
              if (newBox.width < 5 || newBox.height < 5) {
                return oldBox
              }
              return newBox
            }
          })
          
          konvaLayer.add(transformer)
          
          // Handle selection
          konvaStage.on('click tap', (e) => {
            if (e.target === konvaStage) {
              // Clicked on empty area
              transformer.nodes([])
              selectedObject.value = null
              return
            }
            
            // Skip if clicking on transformer
            if (e.target.getParent() === transformer) {
              return
            }
            
            // Find the topmost listening element (in case we clicked on a child)
            let targetNode = e.target
            while (targetNode && !targetNode.listening() && targetNode.getParent()) {
              targetNode = targetNode.getParent()
            }
            
            // Skip if we couldn't find a listening parent
            if (!targetNode || !targetNode.listening()) {
              return
            }
            
            // Select clicked object
            transformer.nodes([targetNode])
            selectedObject.value = {
              id: targetNode.id(),
              className: targetNode.elementType || targetNode.getClassName(),
              x: targetNode.displayX !== undefined ? targetNode.displayX : targetNode.x(),
              y: targetNode.displayY !== undefined ? targetNode.displayY : targetNode.y(),
              width: targetNode.width ? targetNode.width() : 0,
              height: targetNode.height ? targetNode.height() : 0,
              rotation: targetNode.rotation()
            }
          })
          
          // Update selection info when object changes
          konvaStage.on('dragmove transform', () => {
            if (transformer.nodes().length > 0) {
              const node = transformer.nodes()[0]
              // For floor shapes being dragged, update display position
              if (node.elementType === 'floor_shape' && node.displayX !== undefined) {
                // Floor shape display position doesn't change with drag
                // Keep showing the original JSON position
              }
              selectedObject.value = {
                id: node.id(),
                className: node.elementType || node.getClassName(),
                x: node.displayX !== undefined ? node.displayX : node.x(),
                y: node.displayY !== undefined ? node.displayY : node.y(),
                width: node.width ? (node.width() * node.scaleX()) : 0,
                height: node.height ? (node.height() * node.scaleY()) : 0,
                rotation: node.rotation()
              }
            }
          })
        }
      })
    }


    // Handle JSON file import
    const handleJSONImport = (event) => {
      const file = event.target.files[0]
      if (file && (file.type === 'application/json' || file.name.endsWith('.json'))) {
        importStatus.value = 'Reading JSON file...'
        
        const reader = new FileReader()
        reader.onload = (e) => {
          try {
            const jsonContent = e.target.result
            const konvaData = JSON.parse(jsonContent)
            console.log('JSON Content:', konvaData)
            parseJSONContent(konvaData)
          } catch (error) {
            console.error('Error parsing JSON:', error)
            ElMessage.error('Failed to parse JSON file')
            importStatus.value = 'Error'
          }
        }
        reader.onerror = () => {
          ElMessage.error('Failed to read JSON file')
          importStatus.value = 'Error'
        }
        reader.readAsText(file)
      } else {
        ElMessage.error('Please select a valid JSON file')
      }
    }

    // Parse JSON content from converted SVG
    const parseJSONContent = (jsonData) => {
      try {
        importStatus.value = 'Parsing JSON structure...'
        
        const konvaLayer = layer.value.getNode()
        
        // Clear existing objects except transformer
        konvaLayer.children.forEach(child => {
          if (child !== transformer) {
            child.destroy()
          }
        })
        
        console.log('JSON Data:', jsonData)
        
        // Calculate floor shape bounds and transform for relative positioning
        let floorBounds = null
        let floorTransform = null
        if (jsonData.layers?.floor_shape?.metadata?.geometry?.bounds) {
          floorBounds = jsonData.layers.floor_shape.metadata.geometry.bounds
        }
        if (jsonData.layers?.floor_shape?.metadata?.transforms?.matrix) {
          floorTransform = jsonData.layers.floor_shape.metadata.transforms.matrix
        }
        
        console.log('Floor bounds:', floorBounds)
        console.log('Floor transform matrix:', floorTransform)
        
        let totalElements = 0
        
        // Create layers for different element types
        const layers = {
          floor_shape: new Konva.Group({
            id: 'floor-shape-layer',
            name: 'floor-shape',
            visible: showFloorShapeLayer.value
          }),
          server_racks: new Konva.Group({
            id: 'server-racks-layer',
            name: 'server-racks',
            visible: showServerRacksLayer.value
          }),
          cooling_units: new Konva.Group({
            id: 'cooling-units-layer',
            name: 'cooling-units',
            visible: showCoolingUnitsLayer.value
          }),
          cooling_tiles: new Konva.Group({
            id: 'cooling-tiles-layer',
            name: 'cooling-tiles',
            visible: showCoolingTilesLayer.value
          }),
          pdu_ppc: new Konva.Group({
            id: 'pdu-ppc-layer',
            name: 'pdu-ppc',
            visible: showPDULayer.value
          })
        }
        
        // Process each layer from JSON
        if (jsonData.layers) {
          // Process floor shape (background) - add first so it's behind everything
          if (jsonData.layers.floor_shape) {
            const konvaElement = createKonvaFromJSON(jsonData.layers.floor_shape, null, null) // Floor shape doesn't need offset
            if (konvaElement) {
              konvaElement.id('floor-shape-0')
              layers.floor_shape.add(konvaElement)
              totalElements++
            }
          }
          
          
          // Process server racks
          if (jsonData.layers.server_racks) {
            jsonData.layers.server_racks.forEach((element, index) => {
              const konvaElement = createKonvaFromJSON(element, floorBounds, floorTransform)
              if (konvaElement) {
                konvaElement.id(`server-rack-${index}`)
                layers.server_racks.add(konvaElement)
                totalElements++
              }
            })
          }
          
          // Process cooling units
          if (jsonData.layers.cooling_units) {
            jsonData.layers.cooling_units.forEach((element, index) => {
              const konvaElement = createKonvaFromJSON(element, floorBounds, floorTransform)
              if (konvaElement) {
                konvaElement.id(`cooling-unit-${index}`)
                layers.cooling_units.add(konvaElement)
                totalElements++
              }
            })
          }
          
          // Process cooling tiles
          if (jsonData.layers.cooling_tiles) {
            jsonData.layers.cooling_tiles.forEach((element, index) => {
              const konvaElement = createKonvaFromJSON(element, floorBounds, floorTransform)
              if (konvaElement) {
                konvaElement.id(`cooling-tile-${index}`)
                layers.cooling_tiles.add(konvaElement)
                totalElements++
              }
            })
          }
          
          // Process PDUs/PPCs
          if (jsonData.layers.pdu_ppc) {
            jsonData.layers.pdu_ppc.forEach((element, index) => {
              const konvaElement = createKonvaFromJSON(element, floorBounds, floorTransform)
              if (konvaElement) {
                konvaElement.id(`pdu-ppc-${index}`)
                layers.pdu_ppc.add(konvaElement)
                totalElements++
              }
            })
          }
        }
        
        // Add all layers to the main layer in correct order (floor first, then others)
        konvaLayer.add(layers.floor_shape)
        konvaLayer.add(layers.server_racks)
        konvaLayer.add(layers.cooling_units)
        konvaLayer.add(layers.cooling_tiles)
        konvaLayer.add(layers.pdu_ppc)
        
        objectCount.value = totalElements
        
        konvaLayer.draw()
        
        // Fit to screen after import
        setTimeout(() => {
          fitToScreen()
        }, 100)
        
        importStatus.value = 'Complete'
        ElMessage.success(`Imported ${totalElements} elements from JSON`)
        
      } catch (error) {
        console.error('Error processing JSON:', error)
        ElMessage.error('Failed to process JSON: ' + error.message)
        importStatus.value = 'Error'
      }
    }

    
    
    
    
    
    
    

    // Create Konva element from JSON object
    const createKonvaFromJSON = (jsonElement, floorBounds = null, floorTransform = null) => {
      try {
        // Calculate relative position if floor bounds are available and this isn't the floor shape
        let relativeX = jsonElement.x || 0
        let relativeY = jsonElement.y || 0
        
        if (floorBounds && floorTransform && jsonElement.type !== 'floor_shape') {
          // Use empirical working values for accurate positioning
          relativeX = (jsonElement.x || 0) 
          relativeY = (jsonElement.y || 0) 
          
          console.log(`Element ${jsonElement.type}: original (${jsonElement.x}, ${jsonElement.y}) -> relative (${relativeX}, ${relativeY})`)
        }
        
        const konvaProps = {
          id: jsonElement.id,
          x: relativeX,
          y: relativeY,
          width: jsonElement.width || 0,
          height: jsonElement.height || 0,
          fill: jsonElement.fill || 'transparent',
          stroke: jsonElement.stroke || 'none',
          strokeWidth: jsonElement.strokeWidth || 1,
          rotation: jsonElement.rotation || 0,
          scaleX: jsonElement.scaleX || 1,
          scaleY: jsonElement.scaleY || 1,
          offsetX: 0,
          offsetY: 0,
          draggable: true,
          listening: true
        }
        
        // Create appropriate Konva shape based on element type
        let konvaElement
        
        switch (jsonElement.type) {
          case 'server_rack':
            konvaElement = new Konva.Rect({
              ...konvaProps,
              fill: jsonElement.fill || (jsonElement.metadata?.rack_color === 'red' ? 'rgb(244,145,145)' : 'rgb(200,200,200)'),
              stroke: jsonElement.stroke || (jsonElement.metadata?.rack_color === 'red' ? 'rgb(230,0,0)' : 'rgb(110,110,110)')
            })
            break
            
          case 'cooling_unit':
            konvaElement = new Konva.Rect({
              ...konvaProps,
              fill: jsonElement.fill || 'rgb(171,211,241)',
              stroke: jsonElement.stroke || 'rgb(62,153,223)'
            })
            break
            
          case 'cooling_tile':
            konvaElement = new Konva.Rect({
              ...konvaProps,
              fill: jsonElement.fill || 'rgb(240,248,255)',
              stroke: jsonElement.stroke || 'rgb(100,149,237)',
              dash: [5, 5]  // Dashed border for cooling tiles
            })
            break
            
          case 'pdu_ppc':
            konvaElement = new Konva.Rect({
              ...konvaProps,
              fill: jsonElement.fill || 'rgb(189,232,167)',
              stroke: jsonElement.stroke || 'rgb(103,203,51)'
            })
            break
            
          case 'floor_shape':
            // Check if we have complex geometry with path data
            if (jsonElement.metadata?.geometry?.shapes) {
              const shapes = jsonElement.metadata.geometry.shapes
              const pathShapes = shapes.filter(shape => shape.type === 'path' && shape.data)
              
              if (pathShapes.length > 0) {
                // For floor shape, the path data already contains the absolute positioning
                // We should place the group at 0,0 and let the path data define the shape location
                
                // Create a group to hold complex path shapes
                konvaElement = new Konva.Group({
                  id: jsonElement.id,
                  x: 0,  // Floor shape at origin, path data handles positioning
                  y: 0,
                  opacity: jsonElement.opacity || 0.3,
                  draggable: true,  // Make floor draggable
                  listening: true   // Make floor clickable
                })
                
                // Store dimensions and position as custom properties for display
                konvaElement.width = () => jsonElement.width || 0
                konvaElement.height = () => jsonElement.height || 0
                // Store the actual floor position from JSON for display
                konvaElement.displayX = jsonElement.x
                konvaElement.displayY = jsonElement.y
                
                // Add each path shape to the group
                pathShapes.forEach((shape) => {
                  // Use original path data without any transformation
                  const pathElement = new Konva.Path({
                    data: shape.data,
                    fill: shape.fill || jsonElement.fill || 'silver',
                    stroke: shape.stroke || jsonElement.stroke || 'silver',
                    strokeWidth: shape.stroke_width || jsonElement.strokeWidth || 2,
                    listening: false  // Prevent child paths from capturing clicks
                  })
                  konvaElement.add(pathElement)
                })
              } else {
                // Fallback to rectangle
                konvaElement = new Konva.Rect({
                  ...konvaProps,
                  fill: jsonElement.fill || 'silver',
                  stroke: jsonElement.stroke || 'silver',
                  opacity: jsonElement.opacity || 0.3,
                  draggable: true,
                  listening: true
                })
              }
            } else {
              // Simple rectangle fallback
              konvaElement = new Konva.Rect({
                ...konvaProps,
                fill: jsonElement.fill || 'silver',
                stroke: jsonElement.stroke || 'silver',
                opacity: jsonElement.opacity || 0.3,
                draggable: true,
                listening: true
              })
            }
            break
            
            
          default:
            konvaElement = new Konva.Rect({
              ...konvaProps,
              fill: jsonElement.fill || 'transparent',
              stroke: jsonElement.stroke || 'black'
            })
        }
        
        // Add metadata as custom properties
        if (jsonElement.metadata) {
          konvaElement.metadata = jsonElement.metadata
        }
        
        // Store element type for proper display
        konvaElement.elementType = jsonElement.type || 'Unknown'
        
        // Add click handler for selection
        konvaElement.on('click', () => {
          const elementType = jsonElement.type || 'Unknown'
          const elementId = jsonElement.id || 'Unknown'
          
          console.log(`${elementType} ${elementId} clicked!`)
          ElMessage.info(`${elementType} ${elementId} selected`)
          
          // Select this element with transformer
          transformer.nodes([konvaElement])
          selectedObject.value = {
            id: elementId,
            className: elementType,
            x: konvaElement.displayX !== undefined ? konvaElement.displayX : konvaElement.x(),
            y: konvaElement.displayY !== undefined ? konvaElement.displayY : konvaElement.y(),
            width: konvaElement.width ? konvaElement.width() : 0,
            height: konvaElement.height ? konvaElement.height() : 0,
            rotation: konvaElement.rotation()
          }
        })
        
        // Add hover effects
        konvaElement.on('mouseenter', () => {
          document.body.style.cursor = 'pointer'
        })
        
        konvaElement.on('mouseleave', () => {
          document.body.style.cursor = 'default'
        })
        
        return konvaElement
        
      } catch (error) {
        console.error('Error creating Konva element from JSON:', error)
        return null
      }
    }

    // Create Konva element from SVG element
    const createKonvaElement = (element) => {
      const tagName = element.tagName.toLowerCase()
      
      switch (tagName) {
        case 'g':
          return createKonvaGroup(element)
        case 'path':
          return createKonvaPath(element)
        case 'line':
          return createKonvaLine(element)
        case 'rect':
          return createKonvaRect(element)
        case 'circle':
          return createKonvaCircle(element)
        case 'text':
          return createKonvaText(element)
        default:
          return null
      }
    }
    
    // Create Konva group
    const createKonvaGroup = (groupElement) => {
      const group = new Konva.Group()
      
      // Apply transform if present
      const transform = groupElement.getAttribute('transform')
      if (transform) {
        applyTransform(group, transform)
      }
      
      // Process child elements
      Array.from(groupElement.children).forEach(child => {
        const konvaChild = createKonvaElement(child)
        if (konvaChild) {
          group.add(konvaChild)
        }
      })
      
      return group
    }
    
    // Create Konva path
    const createKonvaPath = (pathElement) => {
      const data = pathElement.getAttribute('d')
      if (!data) return null
      
      return new Konva.Path({
        data: data,
        fill: pathElement.getAttribute('fill') || 'transparent',
        stroke: pathElement.getAttribute('stroke') || 'none',
        strokeWidth: parseFloat(pathElement.getAttribute('stroke-width') || '0')
      })
    }
    
    // Create Konva line
    const createKonvaLine = (lineElement) => {
      const x1 = parseFloat(lineElement.getAttribute('x1') || '0')
      const y1 = parseFloat(lineElement.getAttribute('y1') || '0')
      const x2 = parseFloat(lineElement.getAttribute('x2') || '0')
      const y2 = parseFloat(lineElement.getAttribute('y2') || '0')
      
      return new Konva.Line({
        points: [x1, y1, x2, y2],
        stroke: lineElement.getAttribute('stroke') || 'black',
        strokeWidth: parseFloat(lineElement.getAttribute('stroke-width') || '1'),
        fill: lineElement.getAttribute('fill') || 'none'
      })
    }
    
    // Create Konva rect
    const createKonvaRect = (rectElement) => {
      return new Konva.Rect({
        x: parseFloat(rectElement.getAttribute('x') || '0'),
        y: parseFloat(rectElement.getAttribute('y') || '0'),
        width: parseFloat(rectElement.getAttribute('width') || '0'),
        height: parseFloat(rectElement.getAttribute('height') || '0'),
        fill: rectElement.getAttribute('fill') || 'transparent',
        stroke: rectElement.getAttribute('stroke') || 'none',
        strokeWidth: parseFloat(rectElement.getAttribute('stroke-width') || '0')
      })
    }
    
    // Create Konva circle
    const createKonvaCircle = (circleElement) => {
      return new Konva.Circle({
        x: parseFloat(circleElement.getAttribute('cx') || '0'),
        y: parseFloat(circleElement.getAttribute('cy') || '0'),
        radius: parseFloat(circleElement.getAttribute('r') || '0'),
        fill: circleElement.getAttribute('fill') || 'transparent',
        stroke: circleElement.getAttribute('stroke') || 'none',
        strokeWidth: parseFloat(circleElement.getAttribute('stroke-width') || '0')
      })
    }
    
    // Create Konva text
    const createKonvaText = (textElement) => {
      return new Konva.Text({
        x: parseFloat(textElement.getAttribute('x') || '0'),
        y: parseFloat(textElement.getAttribute('y') || '0'),
        text: textElement.textContent || '',
        fontSize: parseFloat(textElement.getAttribute('font-size') || '12'),
        fontFamily: textElement.getAttribute('font-family') || 'Arial',
        fill: textElement.getAttribute('fill') || 'black'
      })
    }
    
    // Apply SVG transform to Konva node
    const applyTransform = (konvaNode, transformString) => {
      // Parse transform string (simplified - handles basic transforms)
      const matrixMatch = transformString.match(/matrix\(([^)]+)\)/)
      const translateMatch = transformString.match(/translate\(([^)]+)\)/)
      const rotateMatch = transformString.match(/rotate\(([^)]+)\)/)
      
      if (matrixMatch) {
        const values = matrixMatch[1].split(',').map(v => parseFloat(v.trim()))
        if (values.length >= 6) {
          konvaNode.scaleX(values[0])
          konvaNode.scaleY(values[3])
          konvaNode.x(values[4])
          konvaNode.y(values[5])
        }
      }
      
      if (translateMatch) {
        const coords = translateMatch[1].split(',').map(v => parseFloat(v.trim()))
        konvaNode.x(coords[0] || 0)
        konvaNode.y(coords[1] || 0)
      }
      
      if (rotateMatch) {
        const rotation = parseFloat(rotateMatch[1].split(',')[0])
        konvaNode.rotation(rotation)
      }
    }


    // Zoom functions
    const handleWheel = (e) => {
      e.evt.preventDefault()
      
      const konvaStage = stage.value.getNode()
      const oldScale = konvaStage.scaleX()
      const pointer = konvaStage.getPointerPosition()
      
      const mousePointTo = {
        x: (pointer.x - konvaStage.x()) / oldScale,
        y: (pointer.y - konvaStage.y()) / oldScale
      }
      
      let direction = e.evt.deltaY > 0 ? -1 : 1
      const scaleBy = 1.05
      const newScale = direction > 0 ? oldScale * scaleBy : oldScale / scaleBy
      
      // Limit zoom
      const clampedScale = Math.max(0.1, Math.min(3, newScale))
      
      konvaStage.scale({ x: clampedScale, y: clampedScale })
      zoomLevel.value = clampedScale
      
      const newPos = {
        x: pointer.x - mousePointTo.x * clampedScale,
        y: pointer.y - mousePointTo.y * clampedScale
      }
      
      konvaStage.position(newPos)
    }

    const zoomIn = () => {
      const konvaStage = stage.value.getNode()
      const newScale = Math.min(konvaStage.scaleX() * 1, 3)
      konvaStage.scale({ x: newScale, y: newScale })
      zoomLevel.value = newScale
    }

    const zoomOut = () => {
      const konvaStage = stage.value.getNode()
      const newScale = Math.max(konvaStage.scaleX() / 1.2, 0.1)
      konvaStage.scale({ x: newScale, y: newScale })
      zoomLevel.value = newScale
    }

    const resetZoom = () => {
      const konvaStage = stage.value.getNode()
      konvaStage.scale({ x: 1, y: 1 })
      konvaStage.position({ x: 0, y: 0 })
      zoomLevel.value = 1
    }

    const fitToScreen = () => {
      const konvaStage = stage.value.getNode()
      const konvaLayer = layer.value.getNode()
      
      // Get bounding box of all objects
      const bbox = konvaLayer.getClientRect({ skipTransform: true })
      
      if (bbox.width === 0 || bbox.height === 0) return
      
      // Calculate scale to fit content with some padding
      const padding = 50
      const scaleX = (stageConfig.width - padding * 2) / bbox.width
      const scaleY = (stageConfig.height - padding * 2) / bbox.height
      const scale = Math.min(scaleX, scaleY, 1.0) // Don't scale up beyond 100%
      
      konvaStage.scale({ x: scale, y: scale })
      zoomLevel.value = scale
      
      console.log('Fit to screen - bbox:', bbox, 'scale:', scale)
      
      // Position content to align to top-left with padding
      konvaStage.position({
        x: padding - bbox.x * scale,
        y: padding - bbox.y * scale
      })
    }

    // Stage event handlers
    const handleStageMouseDown = () => {
      // Handled by Konva stage click event
    }

    const handleStageMouseMove = () => {
      // Update zoom level when panning
      const konvaStage = stage.value.getNode()
      zoomLevel.value = konvaStage.scaleX()
    }

    const handleStageMouseUp = () => {
      // Handled by Konva
    }


    // Trigger JSON file input
    const triggerJSONInput = () => {
      jsonFileInput.value.click()
    }

    // Clear canvas
    const clearCanvas = () => {
      const konvaLayer = layer.value.getNode()
      konvaLayer.children.forEach(child => {
        if (child !== transformer) {
          child.destroy()
        }
      })
      transformer.nodes([])
      konvaLayer.draw()
      objectCount.value = 0
      selectedObject.value = null
      importStatus.value = 'Ready'
    }


    // Import JSON
    const importJSON = () => {
      triggerJSONInput()
    }

    // Save floor plan
    const saveFloorPlan = () => {
      if (stage.value) {
        const konvaStage = stage.value.getNode()
        const stageData = konvaStage.toJSON()
        const floorPlans = JSON.parse(localStorage.getItem('floorPlans') || '{}')
        const floorId = window.location.hash.split('/').pop()
        
        floorPlans[floorId] = {
          konvaData: stageData,
          lastModified: new Date().toISOString()
        }
        
        localStorage.setItem('floorPlans', JSON.stringify(floorPlans))
        ElMessage.success('Floor plan saved successfully')
      }
    }

    // Toggle layer visibility
    const toggleFloorShapeLayer = () => {
      const konvaLayer = layer.value.getNode()
      const floorShapeLayer = konvaLayer.findOne('#floor-shape-layer')
      if (floorShapeLayer) {
        floorShapeLayer.visible(showFloorShapeLayer.value)
        konvaLayer.draw()
      }
    }


    const toggleServerRacksLayer = () => {
      const konvaLayer = layer.value.getNode()
      const serverRacksLayer = konvaLayer.findOne('#server-racks-layer')
      if (serverRacksLayer) {
        serverRacksLayer.visible(showServerRacksLayer.value)
        konvaLayer.draw()
      }
    }

    const toggleCoolingUnitsLayer = () => {
      const konvaLayer = layer.value.getNode()
      const coolingUnitsLayer = konvaLayer.findOne('#cooling-units-layer')
      if (coolingUnitsLayer) {
        coolingUnitsLayer.visible(showCoolingUnitsLayer.value)
        konvaLayer.draw()
      }
    }

    const toggleCoolingTilesLayer = () => {
      const konvaLayer = layer.value.getNode()
      const coolingTilesLayer = konvaLayer.findOne('#cooling-tiles-layer')
      if (coolingTilesLayer) {
        coolingTilesLayer.visible(showCoolingTilesLayer.value)
        konvaLayer.draw()
      }
    }

    const togglePDULayer = () => {
      const konvaLayer = layer.value.getNode()
      const pduLayer = konvaLayer.findOne('#pdu-ppc-layer')
      if (pduLayer) {
        pduLayer.visible(showPDULayer.value)
        konvaLayer.draw()
      }
    }


    // Load floor plan data
    const loadFloorPlan = () => {
      const floorId = window.location.hash.split('/').pop()
      const floors = JSON.parse(localStorage.getItem('floors') || '[]')
      const floor = floors.find(f => f.id.toString() === floorId)
      
      if (floor) {
        floorName.value = floor.name
        siteName.value = floor.siteName
      }
    }

    // Lifecycle hooks
    onMounted(() => {
      loadFloorPlan()
      initStage()
    })

    return {
      stage,
      layer,
      jsonFileInput,
      objectCount,
      selectedObject,
      siteName,
      floorName,
      importStatus,
      zoomLevel,
      showFloorShapeLayer,
      showServerRacksLayer,
      showCoolingUnitsLayer,
      showCoolingTilesLayer,
      showPDULayer,
      stageConfig,
      handleJSONImport,
      handleWheel,
      handleStageMouseDown,
      handleStageMouseMove,
      handleStageMouseUp,
      triggerJSONInput,
      clearCanvas,
      importJSON,
      saveFloorPlan,
      zoomIn,
      zoomOut,
      resetZoom,
      fitToScreen,
      toggleFloorShapeLayer,
      toggleServerRacksLayer,
      toggleCoolingUnitsLayer,
      toggleCoolingTilesLayer,
      togglePDULayer,
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
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.designer-container {
  flex: 1;
  display: flex;
  padding: 20px;
  gap: 20px;
}

.canvas-container {
  flex: 1;
  background: white;
  border-radius: 8px;
  padding: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.controls-panel {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.controls-card {
  background: white;
}

.control-group {
  margin-bottom: 16px;
}

.control-group:last-child {
  margin-bottom: 0;
}

.zoom-info {
  text-align: center;
  font-size: 12px;
  color: #666;
  margin-top: 5px;
}

.object-properties {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.property-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.property-item label {
  font-weight: 500;
  color: #606266;
}

.no-selection {
  text-align: center;
  padding: 20px;
  color: #909399;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.layer-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

.layer-controls .el-checkbox {
  margin-right: 0;
}
</style>