import hashlib
import io
from typing import Annotated, Literal

from ecoscope_workflows_core.annotations import AnyDataFrame
from ecoscope_workflows_core.decorators import task
from ecoscope_workflows_core.serde import _persist_bytes, _persist_text
from pydantic import Field

FileType = Literal["csv", "gpkg", "geoparquet"]


@task
def save_dataframe(
    df: Annotated[AnyDataFrame, Field(description="Dataframe to persist")],
    root_path: Annotated[str, Field(description="Root path to persist data to")],
    filename: Annotated[
        str | None,
        Field(
            description="""\
            Optional filename to persist to within the `root_path`.
            If not provided, a filename will be generated based on a hash of the df content.
            """,
            exclude=True,
        ),
    ] = None,
    filetype: Annotated[FileType, Field(description="The output format")] = "csv",
) -> Annotated[str, Field(description="Path to persisted data")]:
    """Persist a dataframe to a file or cloud storage object."""
    import geopandas as gpd  # type: ignore[import-untyped]
    import pandas as pd

    if not filename:
        filename = hashlib.sha256(pd.util.hash_pandas_object(df).values).hexdigest()[:7]  # type: ignore[arg-type]

    if filetype == "csv":
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer)
        return _persist_text(csv_buffer.getvalue(), root_path, f"{filename}.csv")

    elif filetype == "gpkg":
        buffer = io.BytesIO()
        gdf = gpd.GeoDataFrame(df)
        gdf.to_file(buffer, driver="GPKG")
        return _persist_bytes(buffer.getvalue(), root_path, f"{filename}.gpkg")

    elif filetype == "geoparquet":
        buffer = io.BytesIO()
        gdf = gpd.GeoDataFrame(df)
        gdf.to_parquet(buffer, index=False)
        return _persist_bytes(buffer.getvalue(), root_path, f"{filename}.parquet")

    else:
        raise ValueError(f"Unsupported file type: {filetype}")
