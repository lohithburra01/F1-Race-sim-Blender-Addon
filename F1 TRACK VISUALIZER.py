import bpy
import os
import sys
import site
import subprocess
import tempfile
import csv
import importlib.util
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, EnumProperty, FloatProperty, BoolProperty

bl_info = {
    "name": "F1 Track Visualizer",
    "author": "Lohith Burra",
    "version": (2, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > F1 Track Tab",
    "description": "Visualize F1 tracks from telemetry data with automatic dependency management",
    "category": "3D View",
}

# Dependency Management Functions
def get_modules_path():
    """Return a writable directory for installing Python packages."""
    return bpy.utils.user_resource("SCRIPTS", path="modules", create=True)

def append_modules_to_sys_path(modules_path):
    """Ensure Blender can find installed packages."""
    if modules_path not in sys.path:
        sys.path.append(modules_path)
        site.addsitedir(modules_path)

def check_dependencies():
    """Check if required packages are available."""
    required_packages = ["fastf1", "pandas"]
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_package_to_blender(package, modules_path):
    """Install a package to Blender's user modules directory."""
    try:
        subprocess.check_call([
            sys.executable,  # Blender's Python executable
            "-m", "pip", "install",
            "--upgrade", "--target", modules_path,
            package
        ])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {package}: {e}")
        return False

# Global flag to track if dependencies are available
def dependencies_available():
    """Check if dependencies are available without caching."""
    return len(check_dependencies()) == 0

class F1TrackProperties(PropertyGroup):
    season: StringProperty(
        name="Season",
        description="F1 Season (e.g., 2023)",
        default="2023"
    )
    
    grand_prix: StringProperty(
        name="Grand Prix",
        description="Grand Prix name (e.g., Bahrain)",
        default="Bahrain"
    )
    
    session_type: EnumProperty(
        name="Session Type",
        description="Type of session",
        items=[
            ('R', "Race", "Race session"),
            ('Q', "Qualifying", "Qualifying session"),
            ('FP1', "Practice 1", "Free Practice 1"),
            ('FP2', "Practice 2", "Free Practice 2"),
            ('FP3', "Practice 3", "Free Practice 3"),
        ],
        default='R'
    )
    
    driver_id: StringProperty(
        name="Driver ID",
        description="Driver's three-letter code (e.g., VER, HAM)",
        default="VER"
    )
    
    cache_dir: StringProperty(
        name="Cache Directory",
        description="Directory to store FastF1 cache",
        default=os.path.join(tempfile.gettempdir(), "fastf1_cache"),
        subtype='DIR_PATH'
    )
    
    scale_factor: FloatProperty(
        name="Scale Factor",
        description="Scale factor for track size",
        default=10.0,
        min=0.1,
        max=100.0
    )
    
    curve_type: EnumProperty(
        name="Curve Type",
        description="Type of curve to use",
        items=[
            ('NURBS', "NURBS", "NURBS curve (smoother)"),
            ('BEZIER', "Bezier", "Bezier curve"),
        ],
        default='NURBS'
    )
    
    track_thickness: FloatProperty(
        name="Track Thickness",
        description="Thickness of the track curve",
        default=0.05,
        min=0.01,
        max=1.0
    )
    
    curve_resolution: FloatProperty(
        name="Curve Resolution",
        description="Resolution of the curve (higher = smoother)",
        default=12,
        min=1,
        max=64
    )
    
    show_speed_data: BoolProperty(
        name="Show Speed Data",
        description="Create visual representation of speed data",
        default=False
    )
    
    csv_file_path: StringProperty(
        name="CSV File Path",
        description="Path to the CSV file with track data",
        default="",
        subtype='FILE_PATH'
    )

class OBJECT_OT_InstallF1Dependencies(Operator):
    bl_idname = "object.install_f1_dependencies"
    bl_label = "Install Dependencies"
    bl_description = "Install required Python packages (fastf1, pandas) using modern method"
    
    def execute(self, context):
        # Set up modules path
        modules_path = get_modules_path()
        append_modules_to_sys_path(modules_path)
        
        missing_packages = check_dependencies()
        
        if not missing_packages:
            self.report({'INFO'}, "All dependencies are already installed!")
            return {'FINISHED'}
        
        # Install missing packages
        success_count = 0
        for package in missing_packages:
            self.report({'INFO'}, f"Installing {package}...")
            if install_package_to_blender(package, modules_path):
                success_count += 1
                self.report({'INFO'}, f"Successfully installed {package}")
            else:
                self.report({'ERROR'}, f"Failed to install {package}")
        
        if success_count == len(missing_packages):
            self.report({'INFO'}, "All dependencies installed! You may need to restart Blender.")
        else:
            self.report({'WARNING'}, f"Only {success_count}/{len(missing_packages)} packages installed successfully")
            
        return {'FINISHED'}

class OBJECT_OT_FetchF1Data(Operator):
    bl_idname = "object.fetch_f1_data"
    bl_label = "Fetch F1 Telemetry"
    bl_description = "Fetch F1 telemetry data and save to CSV"
    
    def execute(self, context):
        if not dependencies_available():
            self.report({'ERROR'}, "Required packages not installed. Please install dependencies first.")
            return {'CANCELLED'}
        
        props = context.scene.f1_track_props
        
        try:
            # Import here after confirming dependencies are available
            import fastf1
            import pandas as pd
            
            # Create cache directory if it doesn't exist
            os.makedirs(props.cache_dir, exist_ok=True)
            
            # Enable cache
            fastf1.Cache.enable_cache(props.cache_dir)
            
            # Load session
            session = fastf1.get_session(int(props.season), props.grand_prix, props.session_type)
            session.load()
            
            # Extract laps of the selected driver
            laps = session.laps.pick_driver(props.driver_id)
            
            if laps.empty:
                self.report({'ERROR'}, f"No lap data found for driver {props.driver_id}")
                return {'CANCELLED'}
            
            # Find the fastest lap
            fastest_lap = laps.loc[laps['LapTime'].idxmin()]
            
            # Extract telemetry data for the fastest lap
            telemetry = fastest_lap.get_telemetry()
            
            # Convert the 'Time' column to seconds
            telemetry['Time'] = telemetry['Time'].dt.total_seconds()
            
            # Make sure we have coordinate columns
            if 'X' not in telemetry.columns or 'Y' not in telemetry.columns:
                self.report({'ERROR'}, "Telemetry data doesn't contain X/Y coordinates")
                return {'CANCELLED'}
            
            # If Z is not available, create a flat track
            if 'Z' not in telemetry.columns:
                telemetry['Z'] = 0
            
            # Select columns for the CSV
            columns_to_save = ['Time', 'X', 'Y', 'Z']
            if 'Speed' in telemetry.columns:
                columns_to_save.append('Speed')
                
            telemetry_df = telemetry[columns_to_save]
            
            # Save to CSV
            csv_path = os.path.join(bpy.path.abspath("//"), f"telemetry_{props.driver_id}_{props.grand_prix}_{props.season}.csv")
            if bpy.path.abspath("//") == "":  # If file is not saved
                csv_path = os.path.join(tempfile.gettempdir(), f"telemetry_{props.driver_id}_{props.grand_prix}_{props.season}.csv")
                
            telemetry_df.to_csv(csv_path, index=False)
            
            # Update the CSV file path in properties
            props.csv_file_path = csv_path
            
            self.report({'INFO'}, f"Telemetry data saved to {csv_path}")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Error fetching F1 data: {str(e)}")
            return {'CANCELLED'}

class OBJECT_OT_CreateTrackFromCSV(Operator):
    bl_idname = "object.create_track_from_csv"
    bl_label = "Create Track Visualization"
    bl_description = "Create track visualization from CSV data"
    
    def execute(self, context):
        props = context.scene.f1_track_props
        
        if not props.csv_file_path:
            self.report({'ERROR'}, "CSV file path is not set")
            return {'CANCELLED'}
        
        try:
            # Read coordinates from the CSV file
            coordinates = []
            with open(props.csv_file_path, 'r') as file:
                reader = csv.reader(file)
                header = next(reader)  # Get header row
                
                # Determine column indices
                x_idx, y_idx, z_idx = None, None, None
                for i, col in enumerate(header):
                    if col.upper() == 'X':
                        x_idx = i
                    elif col.upper() == 'Y':
                        y_idx = i
                    elif col.upper() == 'Z':
                        z_idx = i
                
                if x_idx is None or y_idx is None:
                    self.report({'ERROR'}, "CSV must contain X and Y columns")
                    return {'CANCELLED'}
                
                if z_idx is None:  # If no Z column, use flat track
                    z_idx = -1
                    
                for row in reader:
                    if z_idx == -1:  # No Z column
                        x, y = float(row[x_idx]), float(row[y_idx])
                        coordinates.append((x, y, 0.0))
                    else:
                        x, y, z = float(row[x_idx]), float(row[y_idx]), float(row[z_idx])
                        coordinates.append((x, y, z))
            
            # Auto-scale the coordinates for better visibility in Blender
            min_x = min(coord[0] for coord in coordinates)
            min_y = min(coord[1] for coord in coordinates)
            min_z = min(coord[2] for coord in coordinates)
            
            # Shift coordinates to start near origin
            coordinates = [(x - min_x, y - min_y, z - min_z) for x, y, z in coordinates]
            
            # Apply scaling factor
            scaling_factor = props.scale_factor
            coordinates = [(x * scaling_factor, y * scaling_factor, z * scaling_factor) for x, y, z in coordinates]
            
            # Create a new curve in Blender
            curve_name = f"Track_{os.path.basename(props.csv_file_path).split('.')[0]}"
            curve_data = bpy.data.curves.new(name=curve_name, type='CURVE')
            curve_data.dimensions = '3D'
            
            if props.curve_type == 'NURBS':
                # Create NURBS curve
                spline = curve_data.splines.new(type='NURBS')
                spline.points.add(len(coordinates) - 1)  # Add points to the spline
                
                # Set points and adjust curve parameters for smoothness
                for i, coord in enumerate(coordinates):
                    x, y, z = coord
                    spline.points[i].co = (x, y, z, 1.0)  # NURBS points use 4D coordinates (w=1.0)
                
                # Adjust NURBS curve parameters for smoothness
                spline.use_endpoint_u = True  # Ensure the curve passes through end points
                spline.order_u = 4  # Higher order = smoother curve (3-6 is typical range, 4 is cubic)
                spline.resolution_u = int(props.curve_resolution)  # Higher resolution = more segments between control points
                
                # Check if track is closed (start and end points close together)
                start, end = coordinates[0], coordinates[-1]
                distance = ((end[0]-start[0])**2 + (end[1]-start[1])**2 + (end[2]-start[2])**2)**0.5
                if distance < 10.0:  # Arbitrary threshold, adjust as needed
                    spline.use_cyclic_u = True
            
            else:  # Bezier
                spline = curve_data.splines.new(type='BEZIER')
                spline.bezier_points.add(len(coordinates) - 1)  # Add points to the spline
                
                for i, coord in enumerate(coordinates):
                    x, y, z = coord
                    bp = spline.bezier_points[i]
                    bp.co = (x, y, z)  # Set the main control point
                    bp.handle_left_type = 'AUTO'  # Auto handles for smooth curves
                    bp.handle_right_type = 'AUTO'
                
                # Check if track is closed (start and end points close together)
                start, end = coordinates[0], coordinates[-1]
                distance = ((end[0]-start[0])**2 + (end[1]-start[1])**2 + (end[2]-start[2])**2)**0.5
                if distance < 10.0:  # Arbitrary threshold, adjust as needed
                    spline.use_cyclic_u = True
            
            # Create a new object for the curve
            curve_object = bpy.data.objects.new(curve_name, curve_data)
            bpy.context.collection.objects.link(curve_object)
            
            # Add thickness to the curve for better visualization
            curve_data.bevel_depth = props.track_thickness
            curve_data.bevel_resolution = 4  # Smoothness of the bevel
            
            # Select and make the new object active
            bpy.ops.object.select_all(action='DESELECT')
            curve_object.select_set(True)
            bpy.context.view_layer.objects.active = curve_object
            
            self.report({'INFO'}, "Track curve created successfully!")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Error creating track: {str(e)}")
            return {'CANCELLED'}

class VIEW3D_PT_F1TrackPanel(Panel):
    bl_label = "F1 Track Visualizer"
    bl_idname = "VIEW3D_PT_f1_track_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'F1 Track'
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.f1_track_props
        
        # Dependencies check
        box = layout.box()
        missing_packages = check_dependencies()
        
        if missing_packages:
            box.label(text="Required packages not installed:", icon='ERROR')
            for package in missing_packages:
                box.label(text=f"- {package}")
            box.operator("object.install_f1_dependencies", icon='IMPORT')
        else:
            box.label(text="All dependencies installed", icon='CHECKMARK')
        
        # F1 Data section
        box = layout.box()
        box.label(text="F1 Telemetry Data", icon='AUTO')
        
        col = box.column(align=True)
        col.prop(props, "season")
        col.prop(props, "grand_prix")
        col.prop(props, "session_type")
        col.prop(props, "driver_id")
        col.prop(props, "cache_dir")
        
        # Only enable the button if dependencies are available
        row = box.row()
        row.enabled = not bool(missing_packages)
        row.operator("object.fetch_f1_data", icon='IMPORT')
        
        if missing_packages:
            box.label(text="Install dependencies first", icon='INFO')
        
        # Track Visualization section
        box = layout.box()
        box.label(text="Track Visualization", icon='CURVE_DATA')
        
        col = box.column(align=True)
        col.prop(props, "csv_file_path")
        col.prop(props, "scale_factor")
        col.prop(props, "curve_type")
        col.prop(props, "track_thickness")
        col.prop(props, "curve_resolution")
        col.prop(props, "show_speed_data")
        
        box.operator("object.create_track_from_csv", icon='MOD_CURVE')

classes = (
    F1TrackProperties,
    OBJECT_OT_InstallF1Dependencies,
    OBJECT_OT_FetchF1Data,
    OBJECT_OT_CreateTrackFromCSV,
    VIEW3D_PT_F1TrackPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.f1_track_props = bpy.props.PointerProperty(type=F1TrackProperties)
    
    # Set up modules path on addon registration
    modules_path = get_modules_path()
    append_modules_to_sys_path(modules_path)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.f1_track_props

if __name__ == "__main__":
    register()