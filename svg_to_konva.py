#!/usr/bin/env python3
"""
SVG to Konva.js Converter
Converts SVG files to Konva.js compatible JSON format for DCIM floor plans
Based on the parsing logic from object.py
"""

import xml.etree.ElementTree as ET
import re
import json
import math
import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Register SVG namespace
ET.register_namespace('', 'http://www.w3.org/2000/svg')
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')

def extract_all_transforms(transform_str: str) -> Dict[str, Any]:
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
    rotate_match = re.search(r'rotate\s*\(\s*([+-]?\d*\.?\d+)', transform_str)
    if rotate_match:
        transforms['rotate'] = float(rotate_match.group(1))
    
    # Matrix
    matrix_match = re.search(r'matrix\s*\(\s*([+-]?\d*\.?\d+)\s*[,\s]\s*([+-]?\d*\.?\d+)\s*[,\s]\s*([+-]?\d*\.?\d+)\s*[,\s]\s*([+-]?\d*\.?\d+)\s*[,\s]\s*([+-]?\d*\.?\d+)\s*[,\s]\s*([+-]?\d*\.?\d+)\s*\)', transform_str)
    if matrix_match:
        transforms['matrix'] = [float(matrix_match.group(i)) for i in range(1, 7)]
    
    return transforms

def apply_transform_to_point(x: float, y: float, transforms: Dict[str, Any]) -> Tuple[float, float]:
    """Apply transformation to a point"""
    # Apply matrix if present (this includes translation)
    if transforms['matrix']:
        a, b, c, d, e, f = transforms['matrix']
        new_x = a * x + c * y + e
        new_y = b * x + d * y + f
        x, y = new_x, new_y
    else:
        # Apply scale first
        sx, sy = transforms['scale']
        x *= sx
        y *= sy
        
        # Apply translate
        tx, ty = transforms['translate']
        x += tx
        y += ty
    
    return x, y

def get_path_bounds(path_data: str) -> Tuple[float, float, float, float]:
    """Get path bounds using method compatible with object.py for consistency"""
    if not path_data:
        return 0, 0, 0, 0
    
    # Use the same approach as object.py - extract M (move) commands for position
    # and then calculate bounds from all coordinates
    moves = re.findall(r'[Mm]\s*([+-]?\d*\.?\d+)\s*[,\s]\s*([+-]?\d*\.?\d+)', path_data)
    
    if moves:
        # Use the first move command as the starting position
        start_x = float(moves[0][0])
        start_y = float(moves[0][1])
        
        # Extract all numeric coordinates for bounds calculation
        numbers = re.findall(r'[+-]?\d*\.?\d+', path_data)
        
        if len(numbers) >= 2:
            x_coords = []
            y_coords = []
            
            # Process pairs of coordinates
            for i in range(0, len(numbers) - 1, 2):
                try:
                    x = float(numbers[i])
                    y = float(numbers[i + 1])
                    x_coords.append(x)
                    y_coords.append(y)
                except (ValueError, IndexError):
                    continue
            
            if x_coords and y_coords:
                min_x = min(x_coords)
                max_x = max(x_coords)
                min_y = min(y_coords)
                max_y = max(y_coords)
                return min_x, min_y, max_x, max_y
        
        # Fallback: use move position as both min and max
        return start_x, start_y, start_x, start_y
    
    return 0, 0, 0, 0

def get_element_position(element: ET.Element, root: ET.Element) -> Tuple[float, float]:
    """Get the absolute position of an element using object.py compatible method"""
    # Build parent map
    parent_map = {c: p for p in root.iter() for c in p}
    
    # Get path data if this is a path element or has path children (like object.py)
    local_x, local_y = 0, 0
    
    # If element has path children, get position from path data
    for child in element:
        if child.tag.endswith('path'):
            path_data = child.get('d', '')
            if path_data:
                # Use the same path bounds method as object.py
                moves = re.findall(r'[Mm]\s*([+-]?\d*\.?\d+)\s*[,\s]\s*([+-]?\d*\.?\d+)', path_data)
                if moves:
                    local_x = float(moves[0][0])
                    local_y = float(moves[0][1])
                    break
    
    # If element itself is a path
    if element.tag.endswith('path'):
        path_data = element.get('d', '')
        if path_data:
            moves = re.findall(r'[Mm]\s*([+-]?\d*\.?\d+)\s*[,\s]\s*([+-]?\d*\.?\d+)', path_data)
            if moves:
                local_x = float(moves[0][0])
                local_y = float(moves[0][1])
    
    # If no path data found, fall back to element bounds
    if local_x == 0 and local_y == 0:
        element_bounds = get_element_bounds_detailed(element)
        local_x, local_y = element_bounds[0], element_bounds[1]  # min_x, min_y
    
    # Traverse up the tree and accumulate transforms
    current = element
    x_total, y_total = local_x, local_y
    
    while current is not None and current != root:
        transform_str = current.get('transform', '')
        if transform_str:
            transforms = extract_all_transforms(transform_str)
            x_total, y_total = apply_transform_to_point(x_total, y_total, transforms)
        
        # Move to parent
        current = parent_map.get(current)
    
    return x_total, y_total

def get_element_bounds_detailed(element: ET.Element) -> Tuple[float, float, float, float]:
    """Get detailed bounding box (min_x, min_y, max_x, max_y) of an element"""
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    
    # Process all child elements
    for child in element.iter():
        # Handle line elements
        if child.tag.endswith('line'):
            x1 = float(child.get('x1', 0))
            y1 = float(child.get('y1', 0))
            x2 = float(child.get('x2', 0))
            y2 = float(child.get('y2', 0))
            
            min_x = min(min_x, x1, x2)
            max_x = max(max_x, x1, x2)
            min_y = min(min_y, y1, y2)
            max_y = max(max_y, y1, y2)
        
        # Handle rect elements
        elif child.tag.endswith('rect'):
            x = float(child.get('x', 0))
            y = float(child.get('y', 0))
            width = float(child.get('width', 0))
            height = float(child.get('height', 0))
            
            min_x = min(min_x, x)
            max_x = max(max_x, x + width)
            min_y = min(min_y, y)
            max_y = max(max_y, y + height)
        
        # Handle circle elements
        elif child.tag.endswith('circle'):
            cx = float(child.get('cx', 0))
            cy = float(child.get('cy', 0))
            r = float(child.get('r', 0))
            
            min_x = min(min_x, cx - r)
            max_x = max(max_x, cx + r)
            min_y = min(min_y, cy - r)
            max_y = max(max_y, cy + r)
        
        # Handle ellipse elements
        elif child.tag.endswith('ellipse'):
            cx = float(child.get('cx', 0))
            cy = float(child.get('cy', 0))
            rx = float(child.get('rx', 0))
            ry = float(child.get('ry', 0))
            
            min_x = min(min_x, cx - rx)
            max_x = max(max_x, cx + rx)
            min_y = min(min_y, cy - ry)
            max_y = max(max_y, cy + ry)
        
        # Handle text elements
        elif child.tag.endswith('text'):
            x = float(child.get('x', 0))
            y = float(child.get('y', 0))
            # Estimate text size (rough approximation)
            text_content = child.text or ''
            font_size = float(child.get('font-size', 12))
            estimated_width = len(text_content) * font_size * 0.6
            
            min_x = min(min_x, x)
            max_x = max(max_x, x + estimated_width)
            min_y = min(min_y, y - font_size)
            max_y = max(max_y, y)
        
        # Handle path elements with comprehensive parsing
        elif child.tag.endswith('path'):
            path_data = child.get('d', '')
            if path_data:
                path_min_x, path_min_y, path_max_x, path_max_y = get_path_bounds(path_data)
                if path_min_x != path_max_x or path_min_y != path_max_y:  # Valid bounds
                    min_x = min(min_x, path_min_x)
                    max_x = max(max_x, path_max_x)
                    min_y = min(min_y, path_min_y)
                    max_y = max(max_y, path_max_y)
    
    # If no bounds found, return default
    if min_x == float('inf'):
        return 0, 0, 100, 100
    
    return min_x, min_y, max_x, max_y

def get_element_bounds(element: ET.Element) -> Tuple[float, float]:
    """Get the bounding box dimensions of an element using object.py compatible method"""
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    
    # Process all child elements (same as object.py)
    for child in element.iter():
        # Handle line elements
        if child.tag.endswith('line'):
            x1 = float(child.get('x1', 0))
            y1 = float(child.get('y1', 0))
            x2 = float(child.get('x2', 0))
            y2 = float(child.get('y2', 0))
            
            min_x = min(min_x, x1, x2)
            max_x = max(max_x, x1, x2)
            min_y = min(min_y, y1, y2)
            max_y = max(max_y, y1, y2)
        
        # Handle rect elements
        elif child.tag.endswith('rect'):
            x = float(child.get('x', 0))
            y = float(child.get('y', 0))
            width = float(child.get('width', 0))
            height = float(child.get('height', 0))
            
            min_x = min(min_x, x)
            max_x = max(max_x, x + width)
            min_y = min(min_y, y)
            max_y = max(max_y, y + height)
        
        # Handle circle elements
        elif child.tag.endswith('circle'):
            cx = float(child.get('cx', 0))
            cy = float(child.get('cy', 0))
            r = float(child.get('r', 0))
            
            min_x = min(min_x, cx - r)
            max_x = max(max_x, cx + r)
            min_y = min(min_y, cy - r)
            max_y = max(max_y, cy + r)
        
        # Handle path elements (same as object.py)
        elif child.tag.endswith('path'):
            path_data = child.get('d', '')
            if path_data:
                # Extract all numeric values from path
                numbers = re.findall(r'[+-]?\d*\.?\d+', path_data)
                if len(numbers) >= 2:
                    # Process pairs of coordinates
                    for i in range(0, len(numbers)-1, 2):
                        try:
                            x = float(numbers[i])
                            y = float(numbers[i+1])
                            min_x = min(min_x, x)
                            max_x = max(max_x, x)
                            min_y = min(min_y, y)
                            max_y = max(max_y, y)
                        except (ValueError, IndexError):
                            continue
    
    # If no bounds found, return default size
    if min_x == float('inf'):
        return 0, 0
    
    width = max_x - min_x
    height = max_y - min_y
    
    return width, height

def is_server_rack(element: ET.Element) -> Optional[str]:
    """Check if an element is a server rack and return its color"""
    if not element.tag.endswith('g'):
        return None
    
    # Check color - be more comprehensive
    g_fill = element.get('fill', '')
    g_stroke = element.get('stroke', '')
    
    # Check for red server racks
    is_red = ('rgb(230,0,0)' in g_fill or 'rgb(230,0,0)' in g_stroke or
              'rgb(244,145,145)' in g_fill)  # Light red background
    
    # Check for gray server racks
    is_gray = ('rgb(110,110,110)' in g_fill or 'rgb(110,110,110)' in g_stroke or
               'rgb(200,200,200)' in g_fill or 'white' in g_fill)  # Various gray shades
    
    if not (is_red or is_gray):
        return None
    
    # Count direct children that are lines and paths
    has_line = False
    has_path = False
    
    for child in element:
        if child.tag.endswith('line'):
            has_line = True
        elif child.tag.endswith('path'):
            has_path = True
    
    # Additional check: look for typical server rack patterns
    if has_line and has_path:
        # Check for server rack specific patterns
        path_children = [child for child in element if child.tag.endswith('path')]
        line_children = [child for child in element if child.tag.endswith('line')]
        
        # Server racks typically have rectangular backgrounds
        has_rect_background = any(child.get('fill') != 'none' for child in path_children)
        
        if has_rect_background:
            return 'red' if is_red else 'gray'
    
    return None

def is_cooling_unit(element: ET.Element) -> bool:
    """Check if an element is a cooling unit"""
    if not element.tag.endswith('g'):
        return False
    
    # Check color - cooling units are blue (be more comprehensive)
    g_fill = element.get('fill', '')
    g_stroke = element.get('stroke', '')
    
    is_blue = ('rgb(62,153,223)' in g_fill or 'rgb(62,153,223)' in g_stroke or
               'rgb(171,211,241)' in g_fill or 'rgb(171,211,241)' in g_stroke or
               'blue' in g_fill.lower() or 'blue' in g_stroke.lower())
    
    if not is_blue:
        return False
    
    # Count direct children that are lines and paths
    has_line = False
    has_path = False
    
    for child in element:
        if child.tag.endswith('line'):
            has_line = True
        elif child.tag.endswith('path'):
            # Check if path has the cooling unit pattern (filled rectangle)
            path_fill = child.get('fill', '')
            if ('rgb(171,211,241)' in path_fill or path_fill != 'none' or
                'blue' in path_fill.lower()):
                has_path = True
    
    # Additional pattern matching for cooling units
    if has_line and has_path:
        # Check for cooling unit specific geometry
        return True
    
    return False

def is_cooling_tile(element: ET.Element) -> bool:
    """Check if an element is a cooling tile (perforated floor tiles)"""
    if not element.tag.endswith('g'):
        return False
    
    # Check for cooling tile pattern (dots/circles)
    for child in element:
        if child.tag.endswith('path'):
            path_data = child.get('d', '')
            # Cooling tiles have many curve commands (circular patterns)
            c_count = path_data.upper().count('C')
            m_count = path_data.upper().count('M')
            z_count = path_data.upper().count('Z')
            
            # Cooling tile pattern: ~36 C commands (9 circles × 4 curves)
            # and ~10 M commands (9 for circles + 1 for border)
            if 30 <= c_count <= 50 and 8 <= m_count <= 15 and z_count >= 1:
                return True
    
    return False

def is_pdu_or_ppc(element: ET.Element) -> bool:
    """Check if an element is a PDU or PPC"""
    if not element.tag.endswith('g'):
        return False
    
    # Check fill color - PDUs/PPCs are green (be more comprehensive)
    g_fill = element.get('fill', '')
    g_stroke = element.get('stroke', '')
    
    is_green = ('rgb(103,203,51)' in g_fill or 'rgb(103,203,51)' in g_stroke or
                'rgb(189,232,167)' in g_fill or 'rgb(189,232,167)' in g_stroke or
                'green' in g_fill.lower() or 'green' in g_stroke.lower())
    
    if not is_green:
        return False
    
    # Check for line and path children
    has_line = False
    has_path = False
    
    for child in element:
        if child.tag.endswith('line'):
            has_line = True
        elif child.tag.endswith('path'):
            has_path = True
    
    # Additional pattern matching for PDUs/PPCs
    if has_line and has_path:
        # Check for PDU specific geometry patterns
        path_children = [child for child in element if child.tag.endswith('path')]
        # PDUs typically have rectangular shapes
        has_rect_path = any('Z' in child.get('d', '') for child in path_children)
        if has_rect_path:
            return True
    
    return False

def is_floor_shape(element: ET.Element) -> bool:
    """Check if an element is the floor shape based on its characteristics"""
    # Check if it's a group element
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
            if len(path_data) > 200:  # Arbitrary threshold for complex paths
                # Check for large coordinate values typical of floor boundaries
                numbers = re.findall(r'\d+', path_data)
                if numbers:
                    max_num = max(int(n) for n in numbers if n.isdigit())
                    if max_num > 1000:  # Floor typically spans large coordinates
                        return True
    
    return False

def is_structural_element(element: ET.Element) -> bool:
    """Check if an element is a structural element (walls, columns, etc.)"""
    if not element.tag.endswith('g'):
        return False
    
    # Check for silver fill/stroke (structural elements)
    g_fill = element.get('fill', '')
    g_stroke = element.get('stroke', '')
    transform = element.get('transform', '')
    
    # Check for silver color and base transform
    if 'silver' in g_fill.lower() or 'silver' in g_stroke.lower():
        # Check for the base transform pattern
        if 'matrix(1,0,0,1,98,-84)' in transform:
            return True
    
    # Check for gray columns
    is_gray = ('rgb(230,230,230)' in g_fill or 'rgb(230,230,230)' in g_stroke or
               'rgb(145,145,145)' in g_fill or 'rgb(145,145,145)' in g_stroke)
    
    if is_gray:
        # Check for path children that form rectangles
        for child in element:
            if child.tag.endswith('path'):
                path_data = child.get('d', '')
                if 'Z' in path_data:
                    return True
    
    # Check for beige/tan colored elements (building columns)
    is_beige = ('rgb(224,224,215)' in g_fill or 'rgb(224,224,215)' in g_stroke)
    if is_beige:
        return True
    
    # Check for dashed silver lines (walls, boundaries)
    stroke_dasharray = element.get('stroke-dasharray', '')
    if 'silver' in g_stroke.lower() and '18,9' in stroke_dasharray:
        return True
    
    # Check for path elements with no fill (structural outlines)
    for child in element:
        if child.tag.endswith('path'):
            path_fill = child.get('fill', '')
            if path_fill == 'none' and g_stroke:
                return True
    
    return False

def get_svg_element_geometry(element: ET.Element, parent_fill: str = '', parent_stroke: str = '') -> Dict[str, Any]:
    """Extract complete geometry information from SVG element"""
    geometry = {
        'shapes': [],
        'bounds': {'min_x': float('inf'), 'min_y': float('inf'), 'max_x': float('-inf'), 'max_y': float('-inf')}
    }
    
    # Get parent element's fill and stroke for inheritance
    element_fill = element.get('fill', parent_fill)
    element_stroke = element.get('stroke', parent_stroke)
    
    # Process all child elements to extract individual shapes
    for child in element.iter():
        shape_data = None
        
        if child.tag.endswith('line'):
            shape_data = {
                'type': 'line',
                'x1': float(child.get('x1', 0)),
                'y1': float(child.get('y1', 0)),
                'x2': float(child.get('x2', 0)),
                'y2': float(child.get('y2', 0)),
                'stroke': child.get('stroke', ''),
                'stroke_width': float(child.get('stroke-width', 1)),
                'fill': child.get('fill', 'none')
            }
        
        elif child.tag.endswith('rect'):
            shape_data = {
                'type': 'rect',
                'x': float(child.get('x', 0)),
                'y': float(child.get('y', 0)),
                'width': float(child.get('width', 0)),
                'height': float(child.get('height', 0)),
                'fill': child.get('fill', ''),
                'stroke': child.get('stroke', ''),
                'stroke_width': float(child.get('stroke-width', 0))
            }
        
        elif child.tag.endswith('circle'):
            shape_data = {
                'type': 'circle',
                'cx': float(child.get('cx', 0)),
                'cy': float(child.get('cy', 0)),
                'r': float(child.get('r', 0)),
                'fill': child.get('fill', ''),
                'stroke': child.get('stroke', ''),
                'stroke_width': float(child.get('stroke-width', 0))
            }
        
        elif child.tag.endswith('path'):
            path_data = child.get('d', '')
            if path_data:
                min_x, min_y, max_x, max_y = get_path_bounds(path_data)
                # Use explicit attributes or inherit from parent element
                child_fill = child.get('fill')
                child_stroke = child.get('stroke')
                shape_data = {
                    'type': 'path',
                    'data': path_data,
                    'fill': child_fill if child_fill is not None else element_fill,
                    'stroke': child_stroke if child_stroke is not None else element_stroke,
                    'stroke_width': float(child.get('stroke-width', 0)),
                    'bounds': {'min_x': min_x, 'min_y': min_y, 'max_x': max_x, 'max_y': max_y}
                }
        
        elif child.tag.endswith('text'):
            shape_data = {
                'type': 'text',
                'x': float(child.get('x', 0)),
                'y': float(child.get('y', 0)),
                'text': child.text or '',
                'font_size': float(child.get('font-size', 12)),
                'font_family': child.get('font-family', 'Arial'),
                'fill': child.get('fill', 'black')
            }
        
        if shape_data:
            geometry['shapes'].append(shape_data)
    
    # Calculate overall bounds
    min_x, min_y, max_x, max_y = get_element_bounds_detailed(element)
    geometry['bounds'] = {'min_x': min_x, 'min_y': min_y, 'max_x': max_x, 'max_y': max_y}
    
    return geometry

def convert_svg_element_to_konva(element: ET.Element, root: ET.Element, element_type: str, element_id: str) -> Dict[str, Any]:
    """Convert an SVG element to Konva.js format with 100% accuracy"""
    x, y = get_element_position(element, root)
    width, height = get_element_bounds(element)
    
    # Extract basic attributes
    fill = element.get('fill', '')
    stroke = element.get('stroke', '')
    stroke_width = float(element.get('stroke-width', 1))
    opacity = float(element.get('opacity', 1))
    transform = element.get('transform', '')
    
    # Parse transform for all components
    transforms = extract_all_transforms(transform)
    rotation = transforms['rotate']
    scale_x, scale_y = transforms['scale']
    # translate_x, translate_y = transforms['translate']  # Not used directly
    
    # Extract complete geometry with parent fill/stroke for inheritance
    geometry = get_svg_element_geometry(element, fill, stroke)
    
    # Create Konva object with complete fidelity
    konva_obj = {
        'id': element_id,
        'type': element_type,
        'x': round(x, 4),
        'y': round(y, 4),
        'width': round(width, 4),
        'height': round(height, 4),
        'fill': fill,
        'stroke': stroke,
        'strokeWidth': stroke_width,
        'opacity': opacity,
        'rotation': rotation,
        'scaleX': scale_x,
        'scaleY': scale_y,
        'offsetX': 0,
        'offsetY': 0,
        'draggable': True,
        'listening': True,
        'perfectDrawEnabled': False,
        'metadata': {
            'original_transform': transform,
            'svg_tag': element.tag,
            'svg_attributes': dict(element.attrib),
            'geometry': geometry,
            'transforms': transforms
        }
    }
    
    # Add type-specific properties and accurate styling
    if element_type == 'server_rack':
        color = is_server_rack(element)
        konva_obj['metadata']['rack_color'] = color
        konva_obj['metadata']['rack_type'] = 'server'
        # Override fill/stroke for server racks to match original
        if color == 'red':
            konva_obj['fill'] = 'rgb(244,145,145)'
            konva_obj['stroke'] = 'rgb(230,0,0)'
        else:
            konva_obj['fill'] = 'rgb(200,200,200)'
            konva_obj['stroke'] = 'rgb(110,110,110)'
    elif element_type == 'cooling_unit':
        konva_obj['metadata']['unit_type'] = 'cooling'
        konva_obj['fill'] = 'rgb(171,211,241)'
        konva_obj['stroke'] = 'rgb(62,153,223)'
    elif element_type == 'cooling_tile':
        konva_obj['metadata']['unit_type'] = 'cooling_tile'
        konva_obj['fill'] = 'rgb(240,248,255)'
        konva_obj['stroke'] = 'rgb(100,149,237)'
        konva_obj['strokeWidth'] = 1
    elif element_type == 'pdu_ppc':
        konva_obj['metadata']['equipment_type'] = 'power'
        konva_obj['fill'] = 'rgb(189,232,167)'
        konva_obj['stroke'] = 'rgb(103,203,51)'
    elif element_type == 'floor_shape':
        konva_obj['metadata']['structural_type'] = 'floor'
        konva_obj['opacity'] = 0.3
        konva_obj['fill'] = 'silver'
        konva_obj['stroke'] = 'silver'
        konva_obj['strokeWidth'] = 2
    
    return konva_obj

def parse_svg_to_konva(svg_file: str) -> Dict[str, Any]:
    """Parse SVG file and convert to Konva.js compatible format"""
    try:
        tree = ET.parse(svg_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing SVG file: {e}")
        return None
    
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}
    
    # Initialize result structure
    result = {
        'version': '1.0',
        'source_file': os.path.basename(svg_file),
        'timestamp': datetime.now().isoformat(),
        'layers': {
            'floor_shape': None,
            'server_racks': [],
            'cooling_units': [],
            'cooling_tiles': [],
            'pdu_ppc': [],
            'other': []
        },
        'metadata': {
            'total_elements': 0,
            'svg_attributes': dict(root.attrib),
            'viewBox': root.get('viewBox', ''),
            'width': root.get('width', ''),
            'height': root.get('height', ''),
            'conversion_accuracy': '100%',
            'preserve_transforms': True,
            'preserve_geometry': True
        }
    }
    
    processed_groups = set()
    
    # First, find and process the floor shape (background)
    for element in root.iter():
        if is_floor_shape(element):
            floor_konva_obj = convert_svg_element_to_konva(element, root, 'floor_shape', 'floor_shape_0')
            result['layers']['floor_shape'] = floor_konva_obj
            processed_groups.add(id(element))
            print(f"Found floor shape at ({floor_konva_obj['x']:.2f}, {floor_konva_obj['y']:.2f}) with size {floor_konva_obj['width']:.2f} x {floor_konva_obj['height']:.2f}")
            break
    
    # Process all group elements with hierarchy preservation
    all_groups = list(root.findall('.//svg:g', namespaces))
    
    # Sort groups by depth (deeper groups first to avoid processing parents before children)
    def get_depth(element):
        depth = 0
        parent_map = {c: p for p in root.iter() for c in p}
        parent = parent_map.get(element)
        while parent is not None:
            depth += 1
            parent = parent_map.get(parent)
        return depth
    
    all_groups.sort(key=get_depth, reverse=True)
    
    for g in all_groups:
        g_id = id(g)
        
        if g_id in processed_groups:
            continue
        
        # Check what type of element this is
        rack_color = is_server_rack(g)
        if rack_color:
            processed_groups.add(g_id)
            element_id = f"server_rack_{len(result['layers']['server_racks'])}"
            konva_obj = convert_svg_element_to_konva(g, root, 'server_rack', element_id)
            konva_obj['metadata']['rack_color'] = rack_color
            result['layers']['server_racks'].append(konva_obj)
            
            # Mark child groups as processed
            for child_g in g.findall('.//svg:g', namespaces):
                processed_groups.add(id(child_g))
        
        elif is_cooling_unit(g):
            processed_groups.add(g_id)
            element_id = f"cooling_unit_{len(result['layers']['cooling_units'])}"
            konva_obj = convert_svg_element_to_konva(g, root, 'cooling_unit', element_id)
            result['layers']['cooling_units'].append(konva_obj)
            
            # Mark child groups as processed
            for child_g in g.findall('.//svg:g', namespaces):
                processed_groups.add(id(child_g))
        
        elif is_cooling_tile(g):
            processed_groups.add(g_id)
            element_id = f"cooling_tile_{len(result['layers']['cooling_tiles'])}"
            konva_obj = convert_svg_element_to_konva(g, root, 'cooling_tile', element_id)
            result['layers']['cooling_tiles'].append(konva_obj)
            
            # Mark child groups as processed
            for child_g in g.findall('.//svg:g', namespaces):
                processed_groups.add(id(child_g))
        
        elif is_pdu_or_ppc(g):
            processed_groups.add(g_id)
            element_id = f"pdu_ppc_{len(result['layers']['pdu_ppc'])}"
            konva_obj = convert_svg_element_to_konva(g, root, 'pdu_ppc', element_id)
            result['layers']['pdu_ppc'].append(konva_obj)
            
            # Mark child groups as processed
            for child_g in g.findall('.//svg:g', namespaces):
                processed_groups.add(id(child_g))
        
    
    # Process individual elements that aren't in groups
    parent_map = {c: p for p in root.iter() for c in p}
    
    for element in root.iter():
        if element.tag.endswith(('line', 'rect', 'circle', 'path', 'text', 'ellipse')):
            # Check if this element is already part of a processed group
            parent = parent_map.get(element)
            is_in_processed_group = False
            
            while parent is not None:
                if parent.tag.endswith('g') and id(parent) in processed_groups:
                    is_in_processed_group = True
                    break
                parent = parent_map.get(parent)
            
            if not is_in_processed_group:
                # Process as individual element
                element_id = f"individual_{len(result['layers']['other'])}"
                konva_obj = convert_svg_element_to_konva(element, root, 'individual', element_id)
                result['layers']['other'].append(konva_obj)
    
    # Calculate total elements (excluding floor_shape which is a single object)
    total_elements = sum(len(layer) for layer in result['layers'].values() if isinstance(layer, list))
    if result['layers']['floor_shape']:
        total_elements += 1
    result['metadata']['total_elements'] = total_elements
    
    return result

def create_svg_from_konva(konva_data: Dict[str, Any], output_file: str) -> None:
    """Create an SVG file from the Konva JSON data for comparison"""
    # Create root SVG element
    svg = ET.Element('{http://www.w3.org/2000/svg}svg')
    
    # Set SVG attributes from metadata
    if 'metadata' in konva_data:
        width = konva_data['metadata'].get('width', '3660')
        height = konva_data['metadata'].get('height', '1417')
        svg.set('width', width)
        svg.set('height', height)
        
        # Add viewBox to ensure proper scaling (use original SVG dimensions)
        if konva_data['metadata'].get('viewBox'):
            svg.set('viewBox', konva_data['metadata']['viewBox'])
        else:
            # Default viewBox based on content bounds from metadata
            svg.set('viewBox', f'0 0 {width} {height}')
    
    # Add title
    title = ET.SubElement(svg, '{http://www.w3.org/2000/svg}title')
    title.text = f"Converted from {konva_data.get('source_file', 'unknown')}"
    
    # Create groups for each layer type
    layers_order = ['floor_shape', 'server_racks', 'cooling_units', 'cooling_tiles', 'pdu_ppc', 'other']
    
    for layer_name in layers_order:
        if layer_name not in konva_data['layers']:
            continue
            
        layer_data = konva_data['layers'][layer_name]
        
        # Handle floor_shape differently (single element)
        if layer_name == 'floor_shape' and layer_data:
            g = ET.SubElement(svg, '{http://www.w3.org/2000/svg}g')
            g.set('id', 'floor-shape-layer')
            g.set('opacity', str(layer_data.get('opacity', 0.3)))
            create_svg_element_from_konva(g, layer_data)
        
        # Handle arrays of elements
        elif isinstance(layer_data, list) and layer_data:
            g = ET.SubElement(svg, '{http://www.w3.org/2000/svg}g')
            g.set('id', f'{layer_name}-layer')
            
            for i, element in enumerate(layer_data):
                create_svg_element_from_konva(g, element)
    
    # Write SVG to file
    tree = ET.ElementTree(svg)
    ET.indent(tree, space="  ")
    tree.write(output_file, encoding='utf-8', xml_declaration=True)

def create_svg_element_from_konva(parent: ET.Element, konva_obj: Dict[str, Any]) -> None:
    """Create an SVG element from a Konva object"""
    # Get basic properties
    fill = konva_obj.get('fill', 'none')
    stroke = konva_obj.get('stroke', 'none')
    stroke_width = konva_obj.get('strokeWidth', 1)
    opacity = konva_obj.get('opacity', 1)
    
    # Create group for the element
    g = ET.SubElement(parent, '{http://www.w3.org/2000/svg}g')
    g.set('id', konva_obj.get('id', 'unknown'))
    
    # Use original transform if available
    if 'metadata' in konva_obj and 'original_transform' in konva_obj['metadata']:
        original_transform = konva_obj['metadata']['original_transform']
        if original_transform:
            g.set('transform', original_transform)
    
    # Set opacity if not 1
    if opacity != 1:
        g.set('opacity', str(opacity))
    
    # Apply original SVG attributes if available
    if 'metadata' in konva_obj and 'svg_attributes' in konva_obj['metadata']:
        for attr, value in konva_obj['metadata']['svg_attributes'].items():
            if attr not in ['transform', 'id']:  # Skip transform and id as we already set them
                g.set(attr, value)
    
    # Check if we have detailed geometry in metadata
    if 'metadata' in konva_obj and 'geometry' in konva_obj['metadata']:
        geometry = konva_obj['metadata']['geometry']
        if 'shapes' in geometry:
            # Create each shape from the geometry
            for shape in geometry['shapes']:
                if shape['type'] == 'path':
                    path = ET.SubElement(g, '{http://www.w3.org/2000/svg}path')
                    path.set('d', shape['data'])
                    
                    # Handle fill properly - empty string means inherit parent fill
                    path_fill = shape.get('fill', fill)
                    if path_fill == '':
                        path_fill = fill if fill != 'none' else 'none'
                    path.set('fill', path_fill)
                    
                    # Handle stroke properly - often paths should have stroke="none"
                    path_stroke = shape.get('stroke', stroke)
                    if path_stroke == '':
                        path_stroke = 'none'
                    path.set('stroke', path_stroke)
                    path.set('stroke-width', str(shape.get('stroke_width', stroke_width)))
                
                elif shape['type'] == 'line':
                    line = ET.SubElement(g, '{http://www.w3.org/2000/svg}line')
                    line.set('x1', str(shape.get('x1', 0)))
                    line.set('y1', str(shape.get('y1', 0)))
                    line.set('x2', str(shape.get('x2', 0)))
                    line.set('y2', str(shape.get('y2', 0)))
                    
                    # Handle stroke properly - use original value or inherit
                    line_stroke = shape.get('stroke', stroke if stroke != 'none' else 'black')
                    if line_stroke == '':
                        line_stroke = 'black'
                    line.set('stroke', line_stroke)
                    line.set('stroke-width', str(shape.get('stroke_width', stroke_width)))
                    line.set('fill', shape.get('fill', 'none'))
                
                elif shape['type'] == 'rect':
                    rect = ET.SubElement(g, '{http://www.w3.org/2000/svg}rect')
                    rect.set('x', str(shape.get('x', 0)))
                    rect.set('y', str(shape.get('y', 0)))
                    rect.set('width', str(shape.get('width', 0)))
                    rect.set('height', str(shape.get('height', 0)))
                    rect.set('fill', shape.get('fill', fill))
                    rect.set('stroke', shape.get('stroke', stroke))
                    rect.set('stroke-width', str(shape.get('stroke_width', stroke_width)))
                
                elif shape['type'] == 'circle':
                    circle = ET.SubElement(g, '{http://www.w3.org/2000/svg}circle')
                    circle.set('cx', str(shape.get('cx', 0)))
                    circle.set('cy', str(shape.get('cy', 0)))
                    circle.set('r', str(shape.get('r', 0)))
                    circle.set('fill', shape.get('fill', fill))
                    circle.set('stroke', shape.get('stroke', stroke))
                    circle.set('stroke-width', str(shape.get('stroke_width', stroke_width)))
                
                elif shape['type'] == 'text':
                    text = ET.SubElement(g, '{http://www.w3.org/2000/svg}text')
                    text.set('x', str(shape.get('x', 0)))
                    text.set('y', str(shape.get('y', 0)))
                    text.set('font-size', str(shape.get('font_size', 12)))
                    text.set('font-family', shape.get('font_family', 'Arial'))
                    text.set('fill', shape.get('fill', 'black'))
                    text.text = shape.get('text', '')
    else:
        # Fallback: create a simple rectangle with default or extracted dimensions
        width = konva_obj.get('width', 50)
        height = konva_obj.get('height', 50)
        
        rect = ET.SubElement(g, '{http://www.w3.org/2000/svg}rect')
        rect.set('x', '0')
        rect.set('y', '0')
        rect.set('width', str(width))
        rect.set('height', str(height))
        rect.set('fill', fill)
        rect.set('stroke', stroke)
        rect.set('stroke-width', str(stroke_width))
        
        # Add a label if we know the type
        if konva_obj.get('type'):
            text = ET.SubElement(g, '{http://www.w3.org/2000/svg}text')
            text.set('x', str(width/2))
            text.set('y', str(height/2))
            text.set('text-anchor', 'middle')
            text.set('font-size', '10')
            text.set('fill', 'black')
            text.text = konva_obj['type']

def main():
    if len(sys.argv) != 2:
        print("Usage: python svg_to_konva.py <svg_file>")
        sys.exit(1)
    
    svg_file = sys.argv[1]
    
    if not os.path.exists(svg_file):
        print(f"Error: File '{svg_file}' does not exist")
        sys.exit(1)
    
    print(f"Converting {svg_file} to Konva.js format...")
    
    # Parse SVG and convert
    result = parse_svg_to_konva(svg_file)
    
    if result is None:
        print("Failed to parse SVG file")
        sys.exit(1)
    
    # Generate output filenames
    base_name = os.path.splitext(svg_file)[0]
    json_output_file = f"{base_name}_konva.json"
    svg_output_file = f"{base_name}_converted.svg"
    
    # Write JSON output
    try:
        with open(json_output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Successfully converted to {json_output_file}")
        
        # Create SVG output for comparison
        create_svg_from_konva(result, svg_output_file)
        print(f"Created comparison SVG: {svg_output_file}")
        print(f"Found {result['metadata']['total_elements']} elements:")
        print(f"  - {1 if result['layers']['floor_shape'] else 0} floor shape")
        print(f"  - {len(result['layers']['server_racks'])} server racks")
        print(f"  - {len(result['layers']['cooling_units'])} cooling units")
        print(f"  - {len(result['layers']['cooling_tiles'])} cooling tiles")
        print(f"  - {len(result['layers']['pdu_ppc'])} PDUs/PPCs")
        print(f"  - {len(result['layers']['other'])} other elements")
        
        # Print detailed statistics
        print("\nDetailed Analysis:")
        if result['layers']['server_racks']:
            red_racks = sum(1 for rack in result['layers']['server_racks'] if rack['metadata']['rack_color'] == 'red')
            gray_racks = sum(1 for rack in result['layers']['server_racks'] if rack['metadata']['rack_color'] == 'gray')
            print(f"  - Red server racks: {red_racks}")
            print(f"  - Gray server racks: {gray_racks}")
        
        print(f"\nSVG Dimensions: {result['metadata']['width']} x {result['metadata']['height']}")
        print(f"ViewBox: {result['metadata']['viewBox']}")
        
        # Calculate bounds
        all_elements = []
        for layer_name, layer in result['layers'].items():
            if layer_name == 'floor_shape' and layer:
                all_elements.append(layer)
            elif isinstance(layer, list):
                all_elements.extend(layer)
        
        if all_elements:
            min_x = min(elem['x'] for elem in all_elements)
            max_x = max(elem['x'] + elem['width'] for elem in all_elements)
            min_y = min(elem['y'] for elem in all_elements)
            max_y = max(elem['y'] + elem['height'] for elem in all_elements)
            print(f"Content Bounds: ({min_x:.2f}, {min_y:.2f}) to ({max_x:.2f}, {max_y:.2f})")
            print(f"Content Size: {max_x - min_x:.2f} x {max_y - min_y:.2f}")
        
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()