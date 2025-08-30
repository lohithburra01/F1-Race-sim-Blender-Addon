# F1 Track Visualizer

A Blender addon that transforms Formula 1 telemetry data into accurate 3D track visualizations with integrated speed data and curve generation.
<img width="1492" height="640" alt="image" src="https://github.com/user-attachments/assets/d684c451-be07-4c1c-aa1f-b2b565899e2c" />

## Overview

This addon eliminates the manual process of creating F1 track layouts by directly importing real telemetry data from Formula 1's official APIs. Instead of approximating track shapes, you get precise racing lines based on actual driver data.
<img width="983" height="900" alt="image" src="https://github.com/user-attachments/assets/49fa80e6-9a11-45cf-be42-2799189e4862" />

## Features

### Telemetry Integration
- **Fast F1 API**: Direct integration with official F1 telemetry services
- **Real-time data**: Fetch live session data or historical race information
- **Driver-specific**: Generate tracks based on individual driver racing lines
- **Session flexibility**: Support for practice, qualifying, sprint, and race sessions

### Automatic Dependency Management
- **One-click installation**: Installs required packages (fastf1, pandas) automatically
- **Modern compatibility**: Uses Blender 4.5+ compatible installation methods
- **Error handling**: Fallback directories and clear user feedback
- **No manual setup**: Eliminates the typical Python package installation headaches

### Track Generation
- **Precise geometry**: Creates tracks from actual GPS coordinates
- **Curve options**: NURBS or Bezier curve generation
- **Speed visualization**: Optional speed data integration with color mapping
- **Scale control**: Adjustable scaling for different scene requirements

### Data Processing
- **CSV export**: Saves telemetry data for external analysis
- **Cache management**: Efficient data caching for faster repeated access
- **Coordinate transformation**: Proper world-space positioning
- **Track closure detection**: Automatically closes circuit layouts

## Installation

1. Download the addon file
2. In Blender: Edit > Preferences > Add-ons > Install
3. Select the downloaded file and enable the addon
4. Find the panel in 3D Viewport > N-Panel > "F1 Track"

## Usage

### First Time Setup

1. **Install Dependencies**: Click "Install Dependencies" button
2. **Wait for installation**: fastf1 and pandas will be installed automatically
3. **Restart Blender** (recommended for full compatibility)

### Creating Track Visualization

1. **Set session parameters**:
   - **Season**: Year (e.g., 2023, 2024)
   - **Grand Prix**: Race location (e.g., "Bahrain", "Monaco")
   - **Session Type**: Practice, Qualifying, Sprint, or Race
   - **Driver ID**: Three-letter driver code (e.g., "VER", "HAM", "LEC")

2. **Configure cache directory**: Set location for data storage (uses temp directory by default)

3. **Fetch telemetry data**: Click "Fetch F1 Telemetry"
   - Downloads session data from F1 APIs
   - Processes fastest lap telemetry
   - Exports coordinate data to CSV

4. **Generate track**: Click "Create Track Visualization"
   - Imports CSV coordinate data
   - Creates smooth curve geometry
   - Applies scaling and positioning

### Advanced Settings

**Track Generation**:
- **Scale Factor**: Adjusts overall track size (1.0-100.0)
- **Curve Type**: NURBS (smoother) or Bezier curves
- **Track Thickness**: Visual thickness of the track line
- **Curve Resolution**: Smoothness of the generated curves
- **Speed Data**: Optionally include speed visualization

## Technical Implementation

### API Integration
```python
# Fetches session data using Fast F1
session = fastf1.get_session(season, grand_prix, session_type)
session.load()

# Extracts driver-specific data
laps = session.laps.pick_driver(driver_id)
fastest_lap = laps.pick_fastest()
telemetry = fastest_lap.get_telemetry()
```

### Dependency Management
Uses modern Blender addon deployment:
```python
subprocess.check_call([
    sys.executable, "-m", "pip", "install",
    "--upgrade", "--target", modules_path,
    package
])
```

### Coordinate Processing
- Transforms F1 coordinate system to Blender world space
- Applies scaling and centering for optimal viewport display
- Handles both 2D (X,Y) and 3D (X,Y,Z) coordinate data

### Cache System
- Stores downloaded data locally to avoid repeated API calls
- Configurable cache directory with fallback options
- Automatic cache directory creation and validation

## Data Sources

**Fast F1 API**: Official Formula 1 telemetry data including:
- GPS coordinates (X, Y, Z)
- Speed data
- Time stamps
- Sector information
- Lap times

**Session Support**:
- Free Practice 1, 2, 3
- Qualifying
- Sprint Qualifying  
- Sprint Race
- Main Race

## File Output

**CSV Format**:
```csv
Time,X,Y,Z,Speed
0.000,1234.56,789.12,0.00,234
0.100,1235.67,790.23,0.00,235
...
```

**Blender Objects**:
- Curve object with proper naming convention
- Material assignment for speed visualization
- Proper scaling and world positioning

## Use Cases

- **Broadcast Graphics**: Accurate track layouts for TV production
- **Race Analysis**: Visualize racing lines and speed differences  
- **Educational Content**: Teaching F1 circuits and racing strategy
- **Simulation Setup**: Base geometry for racing simulators
- **Motion Graphics**: Foundation for animated F1 content

## Error Handling

- **API failures**: Clear error messages with troubleshooting steps
- **Missing data**: Validation for driver/session availability
- **Dependency issues**: Automatic fallback installation paths
- **File system**: Robust directory creation and permission handling

## Requirements

- Blender 4.0+
- Internet connection for API access
- ~50MB storage for cache data per session

## Workflow Integration

Works seamlessly with:
- **After Effects**: Export curves for motion graphics
- **Game Engines**: Import track geometry for racing games
- **CAD Software**: Precise track measurements for simulation
- **Other Blender addons**: Combines with camera arrays, lighting systems

## Performance Optimization

- **Efficient caching**: Avoids repeated API calls
- **Smart curve generation**: Optimized point distribution
- **Memory management**: Proper cleanup of temporary data
- **Progress feedback**: User updates during long operations

## Development Notes

Built using production-grade patterns:
- Modern Blender addon architecture
- Comprehensive error handling
- User-friendly progress reporting
- Cross-platform compatibility
- Clean separation of concerns

## API Rate Limiting

Respects Fast F1 API guidelines:
- Caches data locally to minimize requests
- Implements reasonable delays between calls
- Provides clear feedback on data fetching progress

## License

MIT License - feel free to modify and distribute.

## Author

Built by Lohith Burra - Technical Artist specializing in F1 broadcast pipeline automation.

## Contributing

Issues and pull requests welcome. Please include:
- Blender version
- F1 session details (if data-related)
- Steps to reproduce any issues
