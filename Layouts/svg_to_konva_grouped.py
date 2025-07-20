#!/usr/bin/env python3
"""
SVG to Konva.js Grouped Elements Converter

This script converts SVG floor plans into Konva.js JSON format with individually grouped
and clickable elements (servers, cooling units, etc.). Each element is given a unique ID
and can be interacted with independently in the Konva.js canvas.
"""

import xml.etree.ElementTree as ET
import json
import re
import sys
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict

@dataclass
class KonvaElement:
    """Represents a Konva.js element with all necessary properties"""
    type: str
    id: str
    name: str
    x: float = 0
    y: float = 0
    width: Optional[float] = None
    height: Optional[float] = None
    fill: Optional[str] = None
    stroke: Optional[str] = None
    strokeWidth: Optional[float] = None
    opacity: Optional[float] = None
    rotation: Optional[float] = None
    scaleX: Optional[float] = None
    scaleY: Optional[float] = None
    listening: bool = True
    draggable: bool = False
    
    # Additional properties for specific shapes
    radius: Optional[float] = None  # For circles
    points: Optional[List[float]] = None  # For lines and polygons
    data: Optional[str] = None  # For paths
    text: Optional[str] = None  # For text
    fontSize: Optional[float] = None
    fontFamily: Optional[str] = None
    
    # Group-specific properties
    children: List['KonvaElement'] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Konva.js compatible dictionary"""
        result = {}
        
        # Type mapping
        type_map = {
            'group': 'Group',
            'rect': 'Rect',
            'circle': 'Circle',
            'path': 'Path',
            'line': 'Line',
            'text': 'Text'
        }
        
        result['className'] = type_map.get(self.type, 'Shape')
        
        # Add non-None attributes
        attrs = {}
        for key, value in asdict(self).items():
            if key in ['type', 'children', 'metadata']:
                continue
            if value is not None:
                attrs[key] = value
        
        result['attrs'] = attrs
        
        # Add children for groups
        if self.children:
            result['children'] = [child.to_dict() for child in self.children]
        
        return result

class SVGToKonvaGroupedConverter:
    """Converts SVG floor plans to grouped Konva.js format"""
    
    def __init__(self):
        self.element_counters = defaultdict(int)
        self.all_elements = []
        
    def parse_svg_file(self, filename: str) -> Optional[ET.Element]:
        """Parse SVG file and return root element"""
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
            return root
        except Exception as e:
            print(f"Error parsing SVG file: {e}")
            return None
    
    def extract_transforms(self, transform_str: str) -> Dict[str, Any]:
        """Extract all transformation values from a transform string"""
        transforms = {
            'translate': (0.0, 0.0),
            'scale': (1.0, 1.0),
            'rotate': 0.0,
            'matrix': None
        }
        
        if not transform_str:
            return transforms
        
        # Translate
        translate_match = re.search(r'translate\s*\(\s*([+-]?\d*\.?\d+)\s*[,\s]\s*([+-]?\d*\.?\d+)\s*\)', transform_str)
        if translate_match:
            transforms['translate'] = (float(translate_match.group(1)), float(translate_match.group(2)))
        
        # Scale
        scale_match = re.search(r'scale\s*\(\s*([+-]?\d*\.?\d+)(?:\s*[,\s]\s*([+-]?\d*\.?\d+))?\s*\)', transform_str)
        if scale_match:
            sx = float(scale_match.group(1))
            sy = float(scale_match.group(2)) if scale_match.group(2) else sx
            transforms['scale'] = (sx, sy)
        
        # Rotate
        rotate_match = re.search(r'rotate\s*\(\s*([+-]?\d*\.?\d+)(?:\s*[,\s]\s*([+-]?\d*\.?\d+)\s*[,\s]\s*([+-]?\d*\.?\d+))?\s*\)', transform_str)
        if rotate_match:
            angle = float(rotate_match.group(1))
            transforms['rotate'] = angle
        
        # Matrix
        matrix_match = re.search(r'matrix\s*\(\s*([+-]?\d*\.?\d+)\s*[,\s]\s*([+-]?\d*\.?\d+)\s*[,\s]\s*([+-]?\d*\.?\d+)\s*[,\s]\s*([+-]?\d*\.?\d+)\s*[,\s]\s*([+-]?\d*\.?\d+)\s*[,\s]\s*([+-]?\d*\.?\d+)\s*\)', transform_str)
        if matrix_match:
            transforms['matrix'] = [float(matrix_match.group(i)) for i in range(1, 7)]
        
        return transforms
    
    def apply_transform_to_point(self, x: float, y: float, transforms: Dict[str, Any]) -> Tuple[float, float]:
        """Apply transformation to a point"""
        # Apply scale
        sx, sy = transforms['scale']
        x *= sx
        y *= sy
        
        # Apply matrix if present
        if transforms['matrix']:
            a, b, c, d, e, f = transforms['matrix']
            new_x = a * x + c * y + e
            new_y = b * x + d * y + f
            x, y = new_x, new_y
        else:
            # Apply translate
            tx, ty = transforms['translate']
            x += tx
            y += ty
        
        return x, y
    
    def get_element_position(self, element: ET.Element, root: ET.Element) -> Tuple[float, float]:
        """Get the absolute position of an element"""
        # Build parent map
        parent_map = {c: p for p in root.iter() for c in p}
        
        # Start with 0,0
        x_total, y_total = 0, 0
        
        # Traverse up the tree and accumulate transforms
        current = element
        while current is not None and current != root:
            transform_str = current.get('transform', '')
            if transform_str:
                transforms = self.extract_transforms(transform_str)
                x_total, y_total = self.apply_transform_to_point(x_total, y_total, transforms)
            
            # Move to parent
            current = parent_map.get(current)
        
        return x_total, y_total
    
    def parse_color(self, color_str: str) -> str:
        """Parse color string to hex format"""
        if not color_str:
            return None
        
        # Already hex
        if color_str.startswith('#'):
            return color_str
        
        # RGB format
        rgb_match = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color_str)
        if rgb_match:
            r, g, b = [int(x) for x in rgb_match.groups()]
            return f'#{r:02x}{g:02x}{b:02x}'
        
        # Named colors
        color_map = {
            'red': '#ff0000',
            'green': '#00ff00',
            'blue': '#0000ff',
            'black': '#000000',
            'white': '#ffffff',
            'silver': '#c0c0c0',
            'gray': '#808080',
            'grey': '#808080'
        }
        
        return color_map.get(color_str.lower(), color_str)
    
    def is_server_rack(self, element: ET.Element) -> Optional[str]:
        """Check if element is a server rack and return color type"""
        if not element.tag.endswith('g'):
            return None
        
        # Check color
        g_fill = element.get('fill', '')
        g_stroke = element.get('stroke', '')
        
        is_red = 'rgb(230,0,0)' in g_fill or 'rgb(230,0,0)' in g_stroke
        is_gray = 'rgb(110,110,110)' in g_fill or 'rgb(110,110,110)' in g_stroke
        
        if not (is_red or is_gray):
            return None
        
        # Check for line and path children
        has_line = any(child.tag.endswith('line') for child in element)
        has_path = any(child.tag.endswith('path') for child in element)
        
        if has_line and has_path:
            return 'red' if is_red else 'gray'
        
        return None
    
    def is_cooling_unit(self, element: ET.Element) -> bool:
        """Check if element is a cooling unit"""
        if not element.tag.endswith('g'):
            return False
        
        # Check color - cooling units are blue
        g_fill = element.get('fill', '')
        g_stroke = element.get('stroke', '')
        
        is_blue = ('rgb(62,153,223)' in g_fill or 'rgb(62,153,223)' in g_stroke or
                   'rgb(171,211,241)' in g_fill or 'rgb(171,211,241)' in g_stroke)
        
        if not is_blue:
            return False
        
        # Check for line and path children
        has_line = any(child.tag.endswith('line') for child in element)
        has_path = any(child.tag.endswith('path') for child in element)
        
        return has_line and has_path
    
    def is_cooling_tile(self, element: ET.Element) -> bool:
        """Check if element contains a cooling tile pattern"""
        # Check path elements for cooling tile pattern
        for child in element.iter():
            if child.tag.endswith('path'):
                path_data = child.get('d', '')
                if self.is_cooling_tile_pattern(path_data):
                    return True
        return False
    
    def is_cooling_tile_pattern(self, path_data: str) -> bool:
        """Check if a path represents a cooling tile pattern"""
        if not path_data:
            return False
        
        upper_data = path_data.upper()
        c_count = upper_data.count('C')
        m_count = upper_data.count('M')
        z_count = upper_data.count('Z')
        
        # Cooling tile pattern: ~36 C commands (9 circles × 4 curves)
        # and ~10 M commands (9 for circles + 1 for border)
        return 30 <= c_count <= 50 and 8 <= m_count <= 15 and z_count >= 1
    
    def is_pdu_or_ppc(self, element: ET.Element) -> bool:
        """Check if element is a PDU or PPC"""
        if not element.tag.endswith('g'):
            return False
        
        # Check fill color - PDUs/PPCs are green
        g_fill = element.get('fill', '')
        g_stroke = element.get('stroke', '')
        
        is_green = ('rgb(103,203,51)' in g_fill or 'rgb(103,203,51)' in g_stroke or
                    'rgb(189,232,167)' in g_fill or 'rgb(189,232,167)' in g_stroke)
        
        if not is_green:
            return False
        
        # Check for line and path children
        has_line = any(child.tag.endswith('line') for child in element)
        has_path = any(child.tag.endswith('path') for child in element)
        
        return has_line and has_path
    
    def is_structural_element(self, element: ET.Element) -> bool:
        """Check if element is a structural element (wall, column, etc.)"""
        if not element.tag.endswith('g'):
            return False
        
        # Check for silver color and specific transform
        g_fill = element.get('fill', '')
        transform = element.get('transform', '')
        
        # Structural elements are often silver with base transform
        return 'silver' in g_fill.lower() and 'matrix(1,0,0,1,98,-84)' in transform
    
    def is_floor_shape(self, element: ET.Element) -> bool:
        """Check if element is the floor shape"""
        if not element.tag.endswith('g'):
            return False
        
        # Check fill color - floor is silver
        fill = element.get('fill', '')
        if 'silver' not in fill.lower():
            return False
        
        # Check if it has a large path child
        for child in element:
            if child.tag.endswith('path'):
                path_data = child.get('d', '')
                # Floor paths tend to be very long with many coordinates
                if len(path_data) > 200:
                    # Check for large coordinate values
                    numbers = re.findall(r'\d+', path_data)
                    if numbers:
                        max_num = max(int(n) for n in numbers if n.isdigit())
                        if max_num > 1000:  # Floor typically spans large coordinates
                            return True
        
        return False
    
    def get_element_bounds(self, element: ET.Element) -> Tuple[float, float]:
        """Get the bounding box dimensions of an element"""
        min_x, min_y = float('inf'), float('inf')
        max_x, max_y = float('-inf'), float('-inf')
        
        # Process all child elements
        for child in element.iter():
            # Handle different element types
            if child.tag.endswith('line'):
                x1 = float(child.get('x1', 0))
                y1 = float(child.get('y1', 0))
                x2 = float(child.get('x2', 0))
                y2 = float(child.get('y2', 0))
                
                min_x = min(min_x, x1, x2)
                max_x = max(max_x, x1, x2)
                min_y = min(min_y, y1, y2)
                max_y = max(max_y, y1, y2)
            
            elif child.tag.endswith('rect'):
                x = float(child.get('x', 0))
                y = float(child.get('y', 0))
                width = float(child.get('width', 0))
                height = float(child.get('height', 0))
                
                min_x = min(min_x, x)
                max_x = max(max_x, x + width)
                min_y = min(min_y, y)
                max_y = max(max_y, y + height)
            
            elif child.tag.endswith('circle'):
                cx = float(child.get('cx', 0))
                cy = float(child.get('cy', 0))
                r = float(child.get('r', 0))
                
                min_x = min(min_x, cx - r)
                max_x = max(max_x, cx + r)
                min_y = min(min_y, cy - r)
                max_y = max(max_y, cy + r)
            
            elif child.tag.endswith('path'):
                path_data = child.get('d', '')
                if path_data:
                    # Extract numeric values from path
                    numbers = re.findall(r'[+-]?\d*\.?\d+', path_data)
                    if len(numbers) >= 2:
                        # Process pairs of coordinates
                        for i in range(0, len(numbers)-1, 2):
                            x = float(numbers[i])
                            y = float(numbers[i+1])
                            min_x = min(min_x, x)
                            max_x = max(max_x, x)
                            min_y = min(min_y, y)
                            max_y = max(max_y, y)
        
        # If no bounds found, return default size
        if min_x == float('inf'):
            return 50, 50
        
        width = max_x - min_x
        height = max_y - min_y
        
        return width, height
    
    def convert_svg_element_to_konva(self, element: ET.Element, x_offset: float = 0, y_offset: float = 0) -> List[KonvaElement]:
        """Convert an SVG element and its children to Konva elements"""
        konva_elements = []
        
        for child in element.iter():
            if child.tag.endswith('rect'):
                x = float(child.get('x', 0)) + x_offset
                y = float(child.get('y', 0)) + y_offset
                width = float(child.get('width', 0))
                height = float(child.get('height', 0))
                
                konva_rect = KonvaElement(
                    type='rect',
                    id='',  # Will be set later
                    name='',
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    fill=self.parse_color(child.get('fill', '')),
                    stroke=self.parse_color(child.get('stroke', '')),
                    strokeWidth=float(child.get('stroke-width', 1))
                )
                konva_elements.append(konva_rect)
            
            elif child.tag.endswith('circle'):
                cx = float(child.get('cx', 0)) + x_offset
                cy = float(child.get('cy', 0)) + y_offset
                r = float(child.get('r', 0))
                
                konva_circle = KonvaElement(
                    type='circle',
                    id='',
                    name='',
                    x=cx,
                    y=cy,
                    radius=r,
                    fill=self.parse_color(child.get('fill', '')),
                    stroke=self.parse_color(child.get('stroke', '')),
                    strokeWidth=float(child.get('stroke-width', 1))
                )
                konva_elements.append(konva_circle)
            
            elif child.tag.endswith('line'):
                x1 = float(child.get('x1', 0)) + x_offset
                y1 = float(child.get('y1', 0)) + y_offset
                x2 = float(child.get('x2', 0)) + x_offset
                y2 = float(child.get('y2', 0)) + y_offset
                
                konva_line = KonvaElement(
                    type='line',
                    id='',
                    name='',
                    points=[x1, y1, x2, y2],
                    stroke=self.parse_color(child.get('stroke', '')),
                    strokeWidth=float(child.get('stroke-width', 1))
                )
                konva_elements.append(konva_line)
            
            elif child.tag.endswith('path'):
                # For complex paths, store the original data
                konva_path = KonvaElement(
                    type='path',
                    id='',
                    name='',
                    x=x_offset,
                    y=y_offset,
                    data=child.get('d', ''),
                    fill=self.parse_color(child.get('fill', '')),
                    stroke=self.parse_color(child.get('stroke', '')),
                    strokeWidth=float(child.get('stroke-width', 1))
                )
                konva_elements.append(konva_path)
            
            elif child.tag.endswith('text'):
                x = float(child.get('x', 0)) + x_offset
                y = float(child.get('y', 0)) + y_offset
                
                konva_text = KonvaElement(
                    type='text',
                    id='',
                    name='',
                    x=x,
                    y=y,
                    text=child.text or '',
                    fontSize=float(child.get('font-size', 12)),
                    fontFamily=child.get('font-family', 'Arial'),
                    fill=self.parse_color(child.get('fill', '#000000'))
                )
                konva_elements.append(konva_text)
        
        return konva_elements
    
    def create_grouped_element(self, element: ET.Element, element_type: str, index: int, root: ET.Element) -> KonvaElement:
        """Create a grouped Konva element from an SVG element"""
        # Generate unique ID and name
        element_id = f"{element_type}-{index + 1}"
        element_name = f"{element_type.replace('_', ' ').title()} {index + 1}"
        
        # Get position
        x, y = self.get_element_position(element, root)
        
        # Get dimensions
        width, height = self.get_element_bounds(element)
        
        # Create group
        group = KonvaElement(
            type='group',
            id=element_id,
            name=element_name,
            x=x,
            y=y,
            draggable=True,
            listening=True,
            metadata={
                'element_type': element_type,
                'original_index': index
            }
        )
        
        # Convert child elements
        children = self.convert_svg_element_to_konva(element, -x, -y)
        for i, child in enumerate(children):
            child.id = f"{element_id}-{child.type}-{i}"
            child.name = f"{element_name} {child.type}"
        
        group.children = children
        
        return group
    
    def process_svg_elements(self, root: ET.Element) -> Dict[str, List[KonvaElement]]:
        """Process all SVG elements and group them by type"""
        layers = {
            'floor_shape': [],
            'structural': [],
            'server_racks': [],
            'cooling_units': [],
            'cooling_tiles': [],
            'pdu_ppc': [],
            'other': []
        }
        
        processed_elements = set()
        
        # Process elements by type
        for element in root.iter():
            element_id = id(element)
            
            if element_id in processed_elements:
                continue
            
            if element.tag.endswith('g'):
                # Check element type
                if self.is_floor_shape(element):
                    konva_element = self.create_grouped_element(element, 'floor', 0, root)
                    layers['floor_shape'].append(konva_element)
                    processed_elements.add(element_id)
                
                elif rack_color := self.is_server_rack(element):
                    index = len(layers['server_racks'])
                    konva_element = self.create_grouped_element(element, f'server_rack_{rack_color}', index, root)
                    layers['server_racks'].append(konva_element)
                    processed_elements.add(element_id)
                
                elif self.is_cooling_unit(element):
                    index = len(layers['cooling_units'])
                    konva_element = self.create_grouped_element(element, 'cooling_unit', index, root)
                    layers['cooling_units'].append(konva_element)
                    processed_elements.add(element_id)
                
                elif self.is_cooling_tile(element):
                    index = len(layers['cooling_tiles'])
                    konva_element = self.create_grouped_element(element, 'cooling_tile', index, root)
                    layers['cooling_tiles'].append(konva_element)
                    processed_elements.add(element_id)
                
                elif self.is_pdu_or_ppc(element):
                    index = len(layers['pdu_ppc'])
                    konva_element = self.create_grouped_element(element, 'pdu_ppc', index, root)
                    layers['pdu_ppc'].append(konva_element)
                    processed_elements.add(element_id)
                
                elif self.is_structural_element(element):
                    index = len(layers['structural'])
                    konva_element = self.create_grouped_element(element, 'structural', index, root)
                    layers['structural'].append(konva_element)
                    processed_elements.add(element_id)
        
        return layers
    
    def create_konva_stage(self, layers: Dict[str, List[KonvaElement]], width: int = 3660, height: int = 1417) -> Dict[str, Any]:
        """Create a complete Konva.js stage structure"""
        stage = {
            'attrs': {
                'width': width,
                'height': height
            },
            'className': 'Stage',
            'children': []
        }
        
        # Create layers
        layer_order = ['floor_shape', 'structural', 'cooling_tiles', 'server_racks', 'cooling_units', 'pdu_ppc', 'other']
        
        for layer_name in layer_order:
            if layer_name in layers and layers[layer_name]:
                konva_layer = {
                    'attrs': {
                        'id': f'{layer_name}_layer',
                        'name': layer_name.replace('_', ' ').title() + ' Layer',
                        'visible': True
                    },
                    'className': 'Layer',
                    'children': [elem.to_dict() for elem in layers[layer_name]]
                }
                stage['children'].append(konva_layer)
        
        return stage
    
    def convert(self, svg_filename: str, output_filename: str) -> bool:
        """Main conversion function"""
        print(f"Converting {svg_filename} to grouped Konva.js format...")
        
        # Parse SVG
        root = self.parse_svg_file(svg_filename)
        if root is None:
            return False
        
        # Get SVG dimensions
        width = int(root.get('width', 3660))
        height = int(root.get('height', 1417))
        
        # Process elements
        layers = self.process_svg_elements(root)
        
        # Create Konva stage
        konva_stage = self.create_konva_stage(layers, width, height)
        
        # Add metadata
        result = {
            'version': '1.0',
            'source_file': os.path.basename(svg_filename),
            'stage': konva_stage,
            'metadata': {
                'total_elements': sum(len(layer) for layer in layers.values()),
                'element_counts': {
                    layer_name: len(elements) for layer_name, elements in layers.items() if elements
                },
                'clickable': True,
                'grouped': True
            }
        }
        
        # Write JSON
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        # Print summary
        print(f"\nConversion complete!")
        print(f"Output file: {output_filename}")
        print(f"\nElement counts:")
        for layer_name, elements in layers.items():
            if elements:
                print(f"  {layer_name}: {len(elements)} groups")
        print(f"\nTotal grouped elements: {sum(len(layer) for layer in layers.values())}")
        
        return True

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python svg_to_konva_grouped.py <svg_file>")
        print("Example: python svg_to_konva_grouped.py 'MLQ2 G.F - Power.svg'")
        sys.exit(1)
    
    svg_filename = sys.argv[1]
    
    # Generate output filename
    base_name = os.path.splitext(svg_filename)[0]
    output_filename = f"{base_name}_konva_grouped.json"
    
    # Convert
    converter = SVGToKonvaGroupedConverter()
    success = converter.convert(svg_filename, output_filename)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()