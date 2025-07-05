import os
import logging
from enum import Enum
import geopandas as gpd
from functools import wraps
from pydantic import BaseModel, Field, field_validator
from ecoscope_workflows_ext_ecoscope.tasks.transformation._classification import apply_classification
from ecoscope_workflows_core.annotations import AnyGeoDataFrame
from typing import Union, Dict, Optional, Literal, List, Annotated, TypedDict
from ecoscope_workflows_ext_ecoscope.tasks.results._ecomap import TileLayer
from ecoscope_workflows_ext_ecoscope.tasks.results._ecomap import ViewState
from ecoscope_workflows_ext_ecoscope.tasks.results._ecomap import draw_ecomap
from ecoscope_workflows_ext_ecoscope.tasks.results._ecomap import LegendStyle
from ecoscope_workflows_ext_ecoscope.tasks.transformation import apply_color_map
from ecoscope_workflows_ext_ecoscope.tasks.results._ecomap import LayerDefinition
from ecoscope_workflows_ext_ecoscope.tasks.results._ecomap import NorthArrowStyle
from ecoscope_workflows_ext_ecoscope.tasks.results._ecomap import PointLayerStyle
from ecoscope_workflows_ext_ecoscope.tasks.results._ecomap import LegendDefinition
from ecoscope_workflows_ext_ecoscope.tasks.results._ecomap import PolygonLayerStyle
from ecoscope_workflows_ext_ecoscope.tasks.results._ecomap import create_point_layer
from ecoscope_workflows_ext_ecoscope.tasks.results._ecomap import PolylineLayerStyle
from ecoscope_workflows_ext_ecoscope.tasks.results._ecomap import create_polygon_layer
from ecoscope_workflows_ext_ecoscope.tasks.results._ecomap import create_polyline_layer
from ecoscope_workflows_ext_ecoscope.tasks.analysis._create_meshgrid import create_meshgrid
from ecoscope_workflows_ext_ecoscope.tasks.analysis._time_density import CustomGridCellSize
from ecoscope_workflows_ext_ecoscope.tasks.analysis._calculate_feature_density import calculate_feature_density


class SpeedMapParams(BaseModel):
    cmap: Optional[List[str]] = Field(default=None, description="List of hex color codes")
    map_layers: Optional[List[LayerDefinition]] = Field(default=None, description="List of additional map layers")
    title: Optional[str] = Field(default=None, description="Map title")
    legend_title: Optional[str] = Field(default=None, description="Legend title")
    zoom: Optional[float] = Field(default=None, description="Initial zoom level")
    tile_layers: Optional[List[TileLayer]] = Field(default=None, description="Custom tile layers for base map")
    legend_style: Optional[LegendStyle] = Field(default=None, description="Legend style object")
    north_arrow_style: Optional[NorthArrowStyle] = Field(default=None, description="North arrow style object")
    static: bool = Field(default=False, description="Whether map is static or interactive")
    scheme: str = Field(default="equal_interval", description="Classification type to use")
    label: str = Field(default=None, description="Label suffix to use")
    width: Optional[float] = Field(default=None, description="Size of polyline width to use")

    class Config:
        arbitrary_types_allowed = True


class TracksParams(BaseModel):
    input_column_name: str = Field(..., description="Column name used for color mapping")
    cmap: Optional[List[str]] = Field(default=None, description="List of hex color codes")
    map_layers: Optional[List[LayerDefinition]] = Field(default=None, description="List of additional map layers")
    title: Optional[str] = Field(default=None, description="Map title")
    legend_title: Optional[str] = Field(default=None, description="Legend title")
    zoom: Optional[float] = Field(default=None, description="Initial zoom level")
    tile_layers: Optional[List[TileLayer]] = Field(default=None, description="Custom tile layers for base map")
    legend_style: Optional[LegendStyle] = Field(default=None, description="Legend style object")
    north_arrow_style: Optional[NorthArrowStyle] = Field(default=None, description="North arrow style object")
    static: bool = Field(default=False, description="Whether map is static or interactive")
    scheme: str = Field(default="equal_interval", description="Classification type to use")
    width: Optional[float] = Field(default=None, description="Size of polyline width to use")

    class Config:
        arbitrary_types_allowed = True


class RangeMapParams(BaseModel):
    input_column_name: str = Field(..., description="Column name used for color mapping")
    cmap: Optional[List[str]] = Field(default=None, description="List of hex color codes")
    map_layers: Optional[List[LayerDefinition]] = Field(default=None, description="List of additional map layers")
    title: Optional[str] = Field(default=None, description="Map title")
    legend_title: Optional[str] = Field(default=None, description="Legend title")
    zoom: Optional[float] = Field(default=None, description="Initial zoom level")
    tile_layers: Optional[List[TileLayer]] = Field(default=None, description="Custom tile layers")
    legend_style: Optional[LegendStyle] = Field(default=None, description="Legend style object")
    north_arrow_style: Optional[NorthArrowStyle] = Field(default=None, description="North arrow style object")
    static: bool = Field(default=False, description="Whether map is static or interactive")
    labels: List[str] = Field(default_factory=lambda: ["99th Percentile"], description="Legend labels")

    class Config:
        arbitrary_types_allowed = True


class MCPRangeMapParams(BaseModel):
    input_column_name: str = Field(..., description="Column name used for color mapping")
    cmap: Optional[List[str]] = Field(default=None, description="List of hex color codes")
    mcp_cmap: Optional[List[str]] = Field(default=None, description="List of hex color codes")
    map_layers: Optional[List[LayerDefinition]] = Field(default=None, description="List of additional map layers")
    title: Optional[str] = Field(default=None, description="Map title")
    legend_title: Optional[str] = Field(default=None, description="Legend title")
    zoom: Optional[float] = Field(default=None, description="Initial zoom level")
    tile_layers: Optional[List[TileLayer]] = Field(default=None, description="Custom tile layers")
    legend_style: Optional[LegendStyle] = Field(default=None, description="Legend style object")
    north_arrow_style: Optional[NorthArrowStyle] = Field(default=None, description="North arrow style object")
    static: bool = Field(default=False, description="Whether map is static or interactive")
    labels: List[str] = Field(default_factory=lambda: ["99th Percentile"], description="Legend labels")

    class Config:
        arbitrary_types_allowed = True


class PointMapParams(BaseModel):
    input_column_name: str = Field(..., description="Column used to determine point color")
    label_column: str = Field(default="label", description="Column used for legend labels")
    cmap: Optional[List[str]] = Field(default=None, description="Color map for point categories")
    map_layers: Optional[List[LayerDefinition]] = Field(default=None, description="Additional map layers")
    title: Optional[str] = Field(default=None, description="Map title")
    legend_title: Optional[str] = Field(default=None, description="Legend title")
    zoom: Optional[float] = Field(default=None, description="Initial zoom level")
    tile_layers: Optional[List[TileLayer]] = Field(default=None, description="Custom tile layers")
    legend_style: Optional[LegendStyle] = Field(default=None, description="Legend style object")
    north_arrow_style: Optional[NorthArrowStyle] = Field(default=None, description="North arrow style object")
    radius_size: Optional[float] = Field(default=None, description="Point size")
    static: bool = Field(default=False, description="Whether map is static or interactive")

    class Config:
        arbitrary_types_allowed = True

class PointTracksParams(BaseModel):
    point_input_column_name: str = Field(..., description="Column used to determine point color")
    point_label_column: str = Field(default="label", description="Column used for legend labels")
    point_cmap: Optional[List[str]] = Field(default=None, description="Color map for point categories")
    point_radius_size: Optional[float] = Field(default=None, description="Point size")
    
    tracks_input_column_name: str = Field(..., description="Column name used for color mapping")
    tracks_cmap: Optional[List[str]] = Field(default=None, description="List of hex color codes")
    
    map_layers: Optional[List[LayerDefinition]] = Field(default=None, description="List of additional map layers")
    title: Optional[str] = Field(default=None, description="Map title")
    legend_title: Optional[str] = Field(default=None, description="Legend title")
    zoom: Optional[float] = Field(default=None, description="Initial zoom level")
    tile_layers: Optional[List[TileLayer]] = Field(default=None, description="Custom tile layers for base map")
    legend_style: Optional[LegendStyle] = Field(default=None, description="Legend style object")
    north_arrow_style: Optional[NorthArrowStyle] = Field(default=None, description="North arrow style object")
    static: bool = Field(default=False, description="Whether map is static or interactive")
    scheme: str = Field(default="equal_interval", description="Classification type to use")
    tracks_width: Optional[float] = Field(default=None, description="Size of polyline width to use")

    class Config:
        arbitrary_types_allowed = True
        
class MapStyleConfig:
    """Configuration for map styles."""

    def __init__(self, styles: Dict = None, legend: Dict = None):
        self.styles = styles or {}
        self.legend = legend or {}


class SupportedFormat(str, Enum):
    GPKG = ".gpkg"
    GEOJSON = ".geojson"
    SHP = ".shp"


SUPPORTED_FORMATS = [f.value for f in SupportedFormat]


class MapProcessingConfig(BaseModel):
    path: str = Field(..., description="Directory path to load geospatial files from")
    target_crs: Union[int, str] = Field(default=4326, description="Target CRS to convert maps to")
    recursive: bool = Field(default=False, description="Whether to walk folders recursively")

    @field_validator("path")
    @classmethod
    def validate_path_exists(cls, v):
        if not os.path.exists(v):
            raise ValueError(f"Invalid path: {v}")
        return v


def retry_decorator(retries=3):
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if i == retries - 1:
                        raise

        return inner

    return wrapper


def clean_geodataframe(
    gdf: Annotated[AnyGeoDataFrame, Field(description="The geodataframe to visualize.", exclude=True)],
) -> AnyGeoDataFrame:
    return gdf.loc[(~gdf.geometry.isna()) & (~gdf.geometry.is_empty)]


def setup_logging():
    """Configure logging with proper format and level."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    return logging.getLogger(__name__)


logger = setup_logging()

PrimaryGeomType = Literal["Polygon", "Point", "LineString", "Other", "Mixed", "Line"]


class GeometrySummary(TypedDict):
    total_features: int
    unique_types: List[str]
    type_counts: Dict[str, int]
    primary_type: PrimaryGeomType


def check_shapefile_geometry_type(data: AnyGeoDataFrame) -> GeometrySummary:
    unique_geom_types = data.geometry.geom_type.unique()

    if len(unique_geom_types) == 1:
        geom_type = unique_geom_types[0]
        if "Polygon" in geom_type:
            primary_type: PrimaryGeomType = "Polygon"
        elif "Point" in geom_type:
            primary_type = "Point"
        elif "LineString" in geom_type:
            primary_type = "LineString"
        else:
            primary_type = "Other"
    else:
        primary_type = "Mixed"

    return {
        "total_features": len(data),
        "unique_types": list(unique_geom_types),
        "type_counts": dict(data.geometry.geom_type.value_counts()),
        "primary_type": primary_type,
    }


@retry_decorator()
def load_map_files(config: MapProcessingConfig, log: Optional[logging.Logger] = None) -> Dict[str, AnyGeoDataFrame]:
    """
    Loads geospatial files from the specified path and returns a dictionary
    mapping filenames to cleaned GeoDataFrames, reprojected to target CRS if needed.
    """
    path = config.path
    target_crs = config.target_crs
    recursive = config.recursive

    log = log or logger
    loaded_files: Dict[str, AnyGeoDataFrame] = {}

    walk = os.walk(path) if recursive else [(path, None, os.listdir(path))]
    for root, _, files in walk:
        for file in files:
            if not file.lower().endswith(tuple(SUPPORTED_FORMATS)):
                continue

            try:
                file_path = os.path.join(root, file)
                gdf = gpd.read_file(file_path)

                if gdf.empty:
                    log.warning(f"Skipped empty file: {file}")
                    continue

                if gdf.crs and gdf.crs != target_crs:
                    gdf = gdf.to_crs(target_crs)

                loaded_files[file] = clean_geodataframe(gdf)

            except Exception as e:
                log.error(f"Error processing {file}: {e}")

    return loaded_files


def clean_file_keys(file_dict: dict) -> dict:
    def clean_key(key: str) -> str:
        for ext in SUPPORTED_FORMATS:
            if key.lower().endswith(ext):
                key = key[: -len(ext)]
                break
        return key.replace(" and ", "_").replace(" ", "_").replace(".", "")

    return {clean_key(k): v for k, v in file_dict.items()}


def create_layer_from_gdf(
    filename: str,
    gdf: AnyGeoDataFrame,
    style_config: MapStyleConfig,
    primary_type: PrimaryGeomType,
    logger,
) -> Optional[object]:
    if filename not in style_config.styles:
        logger.warning(f"No style config for '{filename}'")
        return None

    style_params = style_config.styles[filename]
    legend = None

    if style_config.legend and "labels" in style_config.legend and "colors" in style_config.legend:
        legend = LegendDefinition(labels=style_config.legend["labels"], colors=style_config.legend["colors"])

    try:
        if primary_type == "Polygon":
            logger.info(f"Creating polygon layer for '{filename}'")
            return create_polygon_layer(gdf, layer_style=PolygonLayerStyle(**style_params), legend=legend)
        elif primary_type == "Point":
            logger.info(f"Creating point layer for '{filename}'")
            return create_point_layer(gdf, layer_style=PointLayerStyle(**style_params))
        elif primary_type in ("Line", "LineString"):
            logger.info(f"Creating line layer for '{filename}'")
            return create_polyline_layer(gdf, layer_style=PolylineLayerStyle(**style_params))
        else:
            logger.warning(f"Unsupported geometry type '{primary_type}' for file '{filename}'")
    except Exception as e:
        logger.error(f"Error creating layer for '{filename}': {e}")

    return None


def create_map_layers(
    file_dict: Dict[str, AnyGeoDataFrame], style_config: MapStyleConfig, logger
) -> List[LayerDefinition]:
    """
    Create styled map layers from a dictionary of GeoDataFrames using the provided style config.

    Args:
        file_dict: Dictionary mapping filenames to AnyGeoDataFrames.
        style_config: Object holding style definitions and legend config.
        logger: Logger instance for logging info and errors.

    Returns:
        A list of styled map layer objects.
    """
    layers: List[LayerDefinition] = []
    cleaned_files = clean_file_keys(file_dict)

    for filename, gdf in cleaned_files.items():
        try:
            geom_analysis = check_shapefile_geometry_type(gdf)
            primary_type = geom_analysis["primary_type"]
            layer = create_layer_from_gdf(filename, gdf, style_config, primary_type, logger)

            if layer is not None:
                layers.append(layer)
        except Exception as e:
            logger.error(f"Error processing layer for '{filename}': {e}")

    logger.info(f"Successfully created {len(layers)} map layers")
    return layers


def create_view_state_from_gdf(gdf: AnyGeoDataFrame, pitch: int = 0, bearing: int = 0) -> ViewState:
    """
    Create a ViewState object centered on a GeoDataFrame's bounds.

    Parameters:
        gdf (GeoDataFrame): The input GeoDataFrame
        pitch (int): Optional pitch angle (default: 0)
        bearing (int): Optional bearing angle (default: 0)

    Returns:
        ViewState: Computed map view state
    """
    if gdf.empty:
        raise ValueError("GeoDataFrame is empty. Cannot compute ViewState.")

    # Ensure CRS is geographic
    if gdf.crs is None or not gdf.crs.is_geographic:
        try:
            gdf = gdf.to_crs("EPSG:4326")
        except Exception as e:
            logger.warning(f"Could not convert to geographic coordinates: {e}")

    minx, miny, maxx, maxy = gdf.total_bounds
    center_lon = (minx + maxx) / 2
    center_lat = (miny + maxy) / 2
    max_span = max(abs(maxx - minx), abs(maxy - miny))

    # Heuristic zoom calculation
    if max_span <= 0.01:
        zoom = 16
    elif max_span <= 0.1:
        zoom = 13
    elif max_span <= 1:
        zoom = 10
    elif max_span <= 5:
        zoom = 7
    elif max_span <= 20:
        zoom = 5
    else:
        zoom = 2

    return ViewState(longitude=center_lon, latitude=center_lat, zoom=zoom, pitch=pitch, bearing=bearing)


def get_min_speed(speed_range: str) -> float:
    try:
        return float(speed_range.split("-")[0].replace("km/h", "").strip())
    except (ValueError, IndexError):
        return 0.0


def generate_speedmap(
    geodataframe: Annotated[
        AnyGeoDataFrame,
        Field(description="The speed GeoDataFrame.", exclude=True),
    ],
    params: SpeedMapParams,
) -> Annotated[str, Field()]:
    """
    Generate a speed map with customizable visual settings.

    Parameters:
    -----------
    geodataframe : GeoDataFrame
        The input track data with speed.

    params : SpeedMapParams
        Structured input parameters.

    Returns:
    --------
    str: A static HTML representation of the map.
    """
    try:
        if geodataframe.empty:
            raise ValueError("Input GeoDataFrame is empty.")

        cmap = params.cmap or ["#005C35", "#4CAF50", "#AEDC6F", "#FDC66C", "#F46A43", "#A5082F"]

        gdf = geodataframe.copy()
        gdf = apply_classification(
            dataframe=gdf,
            input_column_name="speed_kmhr",
            output_column_name="speed_bins",
            scheme=params.scheme or "equal_interval",
            k=len(cmap),
            label_suffix=params.label or "",
            label_ranges=True,
        )

        gdf = gdf.sort_values(by="speed_kmhr")
        gdf = apply_color_map(gdf, "speed_bins", colormap=cmap, output_column_name="colors")

        unique_pairs = set(zip(gdf["speed_bins"], gdf["colors"]))
        valid_pairs = sorted(unique_pairs, key=lambda x: get_min_speed(x[0]))

        density_values = [pair[0] for pair in valid_pairs]
        speed_colors = [pair[1] for pair in valid_pairs]

        style = PolylineLayerStyle(
            color_column="colors",
            get_width=params.width or 3,
            width_units="pixels",
            opacity=0.5,
            pickable=True,
            auto_highlight=True,
            cap_rounded=True,
        )

        gdf = gdf[["speed_kmhr", "geometry", "speed_bins", "colors"]]
        legend_definition = LegendDefinition(labels=density_values, colors=speed_colors)

        layer = create_polyline_layer(
            geodataframe=gdf,
            layer_style=style,
            legend=legend_definition,
            zoom=True,
        )

        all_layers = params.map_layers + [layer] if params.map_layers else [layer]

        view_state = create_view_state_from_gdf(layer.geodataframe)
        if params.zoom:
            view_state.zoom = params.zoom

        tile_layers = params.tile_layers or [
            TileLayer(layer_name="USGS HILLSHADE", opacity=0.95),
            TileLayer(layer_name="TERRAIN", opacity=0.45),
        ]

        legend_style = params.legend_style or LegendStyle(placement="bottom-right", title=params.legend_title)
        north_arrow_style = params.north_arrow_style or NorthArrowStyle(
            placement="top-left", style={"transform": "scale(1.0)"}
        )

        return draw_ecomap(
            geo_layers=all_layers,
            tile_layers=tile_layers,
            title=params.title,
            legend_style=legend_style,
            north_arrow_style=north_arrow_style,
            static=params.static,
            view_state=view_state,
        )
    except Exception as e:
        logger.error(f"An error occurred when generating custom-speed ecomap: {e}")
        return None


def generate_tracks_ecomap(
    geodataframe: Annotated[
        AnyGeoDataFrame,
        Field(description="The tracks GeoDataFrame.", exclude=True),
    ],
    params: TracksParams,
) -> Annotated[str, Field()]:
    """
    Generate a tracks ecomap with customizable visual settings.

    Parameters:
    -----------
    geodataframe : GeoDataFrame
        The GeoDataFrame containing the track data.

    params : TracksParams
        Structured input parameters.

    Returns:
    --------
    str: A static HTML representation of the map.
    """
    try:
        if geodataframe.empty:
            raise ValueError("Input GeoDataFrame is empty.")

        cmap = params.cmap or ["#005C35", "#4CAF50", "#AEDC6F", "#FDC66C", "#F46A43", "#A5082F"]

        gdf = apply_color_map(
            geodataframe.copy(),
            input_column_name=params.input_column_name,
            colormap=cmap,
            output_column_name="colors",
        )

        unique_pairs = set(zip(gdf[params.input_column_name], gdf["colors"]))
        valid_pairs = sorted(unique_pairs)

        density_values = [pair[0] for pair in valid_pairs]
        colors = [pair[1] for pair in valid_pairs]

        style = PolylineLayerStyle(
            color_column="colors",
            get_width=params.width or 3,
            width_units="pixels",
            opacity=0.5,
            pickable=True,
            auto_highlight=True,
            cap_rounded=True,
        )

        gdf = gdf[[params.input_column_name, "geometry", "colors"]]
        legend_definition = LegendDefinition(labels=density_values, colors=colors)

        layer = create_polyline_layer(
            geodataframe=gdf,
            layer_style=style,
            legend=legend_definition,
            zoom=True,
        )

        all_layers = params.map_layers + [layer] if params.map_layers else [layer]
        view_state = create_view_state_from_gdf(layer.geodataframe)
        if params.zoom:
            view_state.zoom = params.zoom

        tile_layers = params.tile_layers or [
            TileLayer(layer_name="USGS HILLSHADE", opacity=0.95),
            TileLayer(layer_name="TERRAIN", opacity=0.45),
        ]

        legend_style = params.legend_style or LegendStyle(placement="bottom-right", title=params.legend_title)
        north_arrow_style = params.north_arrow_style or NorthArrowStyle(
            placement="top-left", style={"transform": "scale(1.0)"}
        )

        return draw_ecomap(
            geo_layers=all_layers,
            tile_layers=tile_layers,
            title=params.title,
            legend_style=legend_style,
            north_arrow_style=north_arrow_style,
            static=params.static,
            view_state=view_state,
        )
    except Exception as e:
        logger.error(f"An error occurred when generating tracks ecomap: {e}")
        return None


def generate_range_ecomap(
    geodataframe: Annotated[
        AnyGeoDataFrame,
        Field(description="The geodataframe to visualize.", exclude=True),
    ],
    params: RangeMapParams,
) -> Annotated[str, Field()]:
    """
    Generate range ecomap with customizable visual settings.

    Parameters:
    -----------
    geodataframe : GeoDataFrame
        The GeoDataFrame containing range data.

    params : RangeMapParams
        Structured input parameters.

    Returns:
    --------
    str: A static HTML representation of the map.
    """
    try:
        if geodataframe.empty:
            raise ValueError("Input GeoDataFrame is empty.")

        if params.input_column_name not in geodataframe.columns:
            raise ValueError(f"Column '{params.input_column_name}' not found in GeoDataFrame.")

        cmap = params.cmap or ["#d2691e"]
        gdf = apply_color_map(
            geodataframe,
            input_column_name=params.input_column_name,
            colormap=cmap,
            output_column_name="colors",
        )

        style = PolygonLayerStyle(
            extruded=False,
            get_elevation=1000,
            fill_color_column="colors",
            opacity=0.75,
            get_line_width=0.25,
        )

        legend_definition = LegendDefinition(labels=params.labels, colors=cmap)
        layer = create_polyline_layer(geodataframe=gdf, layer_style=style, legend=legend_definition, zoom=True)

        all_layers = params.map_layers + [layer] if params.map_layers else [layer]
        view_state = create_view_state_from_gdf(layer.geodataframe)
        if params.zoom:
            view_state.zoom = params.zoom

        tile_layers = params.tile_layers or [
            TileLayer(layer_name="USGS HILLSHADE", opacity=0.95),
            TileLayer(layer_name="TERRAIN", opacity=0.45),
        ]

        legend_style = params.legend_style or LegendStyle(placement="bottom-right", title=params.legend_title)
        north_arrow_style = params.north_arrow_style or NorthArrowStyle(
            placement="top-left", style={"transform": "scale(1.0)"}
        )

        return draw_ecomap(
            geo_layers=all_layers,
            tile_layers=tile_layers,
            title=params.title,
            legend_style=legend_style,
            north_arrow_style=north_arrow_style,
            static=params.static,
            view_state=view_state,
        )
    except Exception as e:
        logger.info(f"An error occurred when generating home range ecomap: {e}")
        return None


def generate_point_ecomap(
    geodataframe: Annotated[
        AnyGeoDataFrame,
        Field(description="The geodataframe to visualize.", exclude=True),
    ],
    params: PointMapParams,
) -> Annotated[str, Field()]:
    """
    Generate point ecomap with customizable visual settings.

    Parameters:
    -----------
    geodataframe : GeoDataFrame
        The GeoDataFrame containing point data.

    params : PointMapParams
        Structured input parameters.

    Returns:
    --------
    str: A static HTML representation of the map.
    """
    try:
        if geodataframe.empty:
            raise ValueError("Input GeoDataFrame is empty.")

        if params.input_column_name not in geodataframe.columns:
            raise ValueError(f"Missing column '{params.input_column_name}' for color mapping.")
        if params.label_column not in geodataframe.columns:
            raise ValueError(f"Missing column '{params.label_column}' for legend labels.")

        cmap = params.cmap or ["#556b2f"]
        gdf = apply_color_map(
            geodataframe.copy(),
            input_column_name=params.input_column_name,
            colormap=cmap,
            output_column_name="point_colors",
        )

        if gdf.crs is None:
            gdf = gdf.set_crs(epsg=4326)

        style = PointLayerStyle(
            get_radius=params.radius_size or 4,
            fill_color_column="point_colors",
            opacity=0.75,
            get_line_width=0.25,
        )

        unique_pairs = list(set(zip(gdf[params.label_column], gdf["point_colors"])))
        sorted_pairs = sorted(unique_pairs, key=lambda x: str(x[0]).lower())
        legend_labels = [pair[0] for pair in sorted_pairs]
        legend_colors = [pair[1] for pair in sorted_pairs]

        legend_definition = LegendDefinition(labels=legend_labels, colors=legend_colors)

        layer = create_point_layer(geodataframe=gdf, layer_style=style, legend=legend_definition, zoom=True)

        all_layers = params.map_layers + [layer] if params.map_layers else [layer]
        view_state = create_view_state_from_gdf(layer.geodataframe)
        if params.zoom:
            view_state.zoom = params.zoom

        tile_layers = params.tile_layers or [
            TileLayer(layer_name="USGS HILLSHADE", opacity=0.95),
            TileLayer(layer_name="TERRAIN", opacity=0.45),
        ]

        legend_style = params.legend_style or LegendStyle(placement="bottom-right", title=params.legend_title)
        north_arrow_style = params.north_arrow_style or NorthArrowStyle(
            placement="top-left", style={"transform": "scale(1.0)"}
        )

        return draw_ecomap(
            geo_layers=all_layers,
            tile_layers=tile_layers,
            title=params.title,
            legend_style=legend_style,
            north_arrow_style=north_arrow_style,
            static=params.static,
            view_state=view_state,
        )

    except Exception as e:
        logger.error(f"An error occurred when generating point ecomap: {e}")
        return None


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a hex color string to an RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        raise ValueError("Hex color must be 6 characters long.")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def generate_range_mcp_ecomap(
    geodataframe: Annotated[AnyGeoDataFrame, Field(description="The main geodataframe.", exclude=True)],
    mcp_geodataframe: Annotated[AnyGeoDataFrame, Field(description="The MCP geodataframe.", exclude=True)],
    params: MCPRangeMapParams,
) -> Annotated[str, Field()]:
    """
    Generate point ecomap with customizable visual settings.

    Parameters:
    -----------
    geodataframe : GeoDataFrame
        The GeoDataFrame containing range data.
    mcp_geodataframe : GeoDataFrame
        The GeoDataFrame containing MCP data.

    params : MCPRangeMapParams
        Structured input parameters.

    Returns:
    --------
    str: A static HTML representation of the map.
    """
    try:
        if geodataframe.empty:
            raise ValueError("Input GeoDataFrame is empty.")

        if mcp_geodataframe.empty:
            raise ValueError("MCP GeoDataFrame is empty.")

        if params.input_column_name not in geodataframe.columns:
            raise ValueError(f"Column '{params.input_column_name}' not found in GeoDataFrame.")

        cmap = params.cmap or ["#d2691e"]
        mcp_cmap = params.mcp_cmap or ["#ff1493"]
        gdf = apply_color_map(
            geodataframe,
            input_column_name=params.input_column_name,
            colormap=cmap,
            output_column_name="colors",
        )

        style = PolygonLayerStyle(
            extruded=False,
            get_elevation=1000,
            fill_color_column="colors",
            opacity=0.75,
            get_line_width=0.25,
        )

        legend_definition = LegendDefinition(labels=params.labels, colors=cmap)
        hr_layer = create_polygon_layer(geodataframe=gdf, layer_style=style, legend=legend_definition, zoom=True)

        mcp = mcp_geodataframe.copy()
        mcp["value"] = "MCP"
        mcp = apply_color_map(mcp, "value", colormap=mcp_cmap, output_column_name="colors")

        mcp_style = PolygonLayerStyle(
            extruded=False,
            get_elevation=1000,
            get_line_color=hex_to_rgb(mcp_cmap[0]),
            get_fill_color=(255, 255, 255, 0),
            opacity=0.75,
            get_line_width=2.0,
        )

        mcp_layer = create_polyline_layer(
            geodataframe=mcp,
            layer_style=mcp_style,
            legend=LegendDefinition(labels=["MCP"], colors=mcp_cmap),
            zoom=True,
        )

        all_layers = params.map_layers + [hr_layer, mcp_layer] if params.map_layers else [hr_layer, mcp_layer]
        view_state = create_view_state_from_gdf(hr_layer.geodataframe)
        if params.zoom:
            view_state.zoom = params.zoom

        tile_layers = params.tile_layers or [
            TileLayer(layer_name="USGS HILLSHADE", opacity=0.95),
            TileLayer(layer_name="TERRAIN", opacity=0.45),
        ]

        legend_style = params.legend_style or LegendStyle(placement="bottom-right", title=params.legend_title)
        north_arrow_style = params.north_arrow_style or NorthArrowStyle(
            placement="top-left", style={"transform": "scale(1.0)"}
        )

        return draw_ecomap(
            geo_layers=all_layers,
            tile_layers=tile_layers,
            title=params.title,
            legend_style=legend_style,
            north_arrow_style=north_arrow_style,
            static=params.static,
            view_state=view_state,
        )
    except Exception as e:
        logger.info(f"An error occurred when generating home range ecomap: {e}")
        return None

def generate_point_tracks_ecomap(
    point_geodataframe: Annotated[AnyGeoDataFrame, Field(description="Points geodataframe.", exclude=True)],
    tracks_geodataframe: Annotated[AnyGeoDataFrame, Field(description="Tracks geodataframe.", exclude=True)],
    params: PointTracksParams,
) -> Annotated[str, Field()]:
    """
    Generate point tracks ecomap with customizable visual settings.

    Parameters:
    -----------
    point_geodataframe : GeoDataFrame
        The GeoDataFrame containing point data.
    tracks_geodataframe : GeoDataFrame
        The GeoDataFrame containing track data.

    params : PointTracksParams
        Structured input parameters.

    Returns:
    --------
    str: A static HTML representation of the map.
    """
    try:
        if point_geodataframe.empty:
            raise ValueError("Point GeoDataFrame is empty.")

        if tracks_geodataframe.empty:
            raise ValueError("Tracks GeoDataFrame is empty.")

        if params.point_input_column_name not in point_geodataframe.columns:
            raise ValueError(f"Column '{params.point_input_column_name}' not found in GeoDataFrame.")

        if params.tracks_input_column_name not in tracks_geodataframe.columns:
            raise ValueError(f"Column '{params.tracks_input_column_name}' not found in GeoDataFrame.")

        
        point_cmap = params.point_cmap
        tracks_cmap = params.tracks_cmap


        point_gdf = apply_color_map(
            point_geodataframe.copy(),
            input_column_name=params.point_input_column_name,
            colormap=cmap,
            output_column_name="point_colors",
        )

        if point_gdf.crs is None:
            point_gdf = point_gdf.set_crs(epsg=4326)

        point_style = PointLayerStyle(
            get_radius=params.point_radius_size or 4,
            fill_color_column="point_colors",
            opacity=0.75,
            get_line_width=0.25,
        )

        unique_pairs = list(set(zip(point_gdf[params.point_label_column], point_gdf["point_colors"])))
        sorted_pairs = sorted(unique_pairs, key=lambda x: str(x[0]).lower())
        legend_labels = [pair[0] for pair in sorted_pairs]
        legend_colors = [pair[1] for pair in sorted_pairs]

        legend_definition = LegendDefinition(labels=legend_labels, colors=legend_colors)

        point_layer = create_point_layer(
            geodataframe=point_gdf, 
            layer_style=point_style, 
            legend=legend_definition, 
            zoom=True
        )

        #tracks
        tracks_gdf = apply_color_map(
            tracks_geodataframe.copy(),
            input_column_name=params.tracks_input_column_name,
            colormap=cmap,
            output_column_name="colors",
        )

        unique_pairs = set(zip(tracks_gdf[params.tracks_input_column_name], tracks_gdf["colors"]))
        valid_pairs = sorted(unique_pairs)

        density_values = [pair[0] for pair in valid_pairs]
        colors = [pair[1] for pair in valid_pairs]

        tracks_style = PolylineLayerStyle(
            color_column="colors",
            get_width=params.tracks_width or 3,
            width_units="pixels",
            opacity=0.5,
            pickable=True,
            auto_highlight=True,
            cap_rounded=True,
        )

        tracks_gdf = tracks_gdf[[params.tracks_input_column_name, "geometry", "colors"]]
        legend_definition = LegendDefinition(labels=density_values, colors=colors)

        tracks_layer = create_polyline_layer(
            geodataframe=tracks_gdf,
            layer_style=tracks_style,
            legend=legend_definition,
            zoom=True,
        )

        all_layers = params.map_layers + [point_layer,tracks_layer] if params.map_layers else [point_layer,tracks_layer]
        view_state = create_view_state_from_gdf(point_layer.geodataframe)
        if params.zoom:
            view_state.zoom = params.zoom

        tile_layers = params.tile_layers or [
            TileLayer(layer_name="USGS HILLSHADE", opacity=0.95),
            TileLayer(layer_name="TERRAIN", opacity=0.45),
        ]

        legend_style = params.legend_style or LegendStyle(placement="bottom-right", title=params.legend_title)
        north_arrow_style = params.north_arrow_style or NorthArrowStyle(
            placement="top-left", style={"transform": "scale(1.0)"}
        )

        return draw_ecomap(
            geo_layers=all_layers,
            tile_layers=tile_layers,
            title=params.title,
            legend_style=legend_style,
            north_arrow_style=north_arrow_style,
            static=params.static,
            view_state=view_state,
        )
    except Exception as e:
        logger.info(f"An error occurred when generating home range ecomap: {e}")
        return None

def generate_density_grid(
    features_gdf: AnyGeoDataFrame, cell_size_meters: int = 2000, geometry_type: Literal["point", "line"] = "point"
) -> AnyGeoDataFrame:
    """
    Generates a density grid based on point or line features within a defined area of interest.

    Args:
        features_gdf (AnyGeoDataFrame): The input GeoDataFrame containing features (points or lines).
        cell_size_meters (int): The size of each grid cell in meters. Default is 2000.
        geometry_type (Literal["point", "line"]): The geometry type of features to calculate density for.

    Returns:
        AnyGeoDataFrame: A filtered density grid (only cells with density > 0 and not NaN).
    """
    meshgrid_gdf = create_meshgrid(
        aoi=features_gdf, auto_scale_or_custom_cell_size=CustomGridCellSize(grid_cell_size=cell_size_meters)
    )

    density_grid = calculate_feature_density(
        geodataframe=features_gdf, meshgrid=meshgrid_gdf, geometry_type=geometry_type
    )

    density_grid = density_grid[(density_grid["density"].notna()) & (density_grid["density"] > 0)]
    return density_grid