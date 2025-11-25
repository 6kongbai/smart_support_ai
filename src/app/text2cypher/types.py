from typing import List, Optional, Union, Literal

from pydantic import BaseModel, Field


class Property(BaseModel):
    """
    Represents a filter condition based on a specific node property in a graph in a Cypher statement.
    """

    node_label: str = Field(
        description="The label of the node to which this property belongs."
    )
    property_key: str = Field(description="The key of the property being filtered.")

    # 新增：捕获操作符
    operator: Literal["=", "<>", ">", "<", ">=", "<=", "CONTAINS", "STARTS WITH", "ENDS WITH", "IN"] = Field(
        description="The comparison operator used in the Cypher statement (e.g., =, >, CONTAINS, IN)."
    )

    property_value: Union[int, float, bool, str, List[Union[str, int, float]], None] = Field(
        description="The literal value found in the query. For 'IN' operator, this should be a list."
    )


class ValidateCypherOutput(BaseModel):
    """
    Represents the validation result of a Cypher query's output,
    including any errors and applied filters.
    """

    reasoning: Optional[str] = Field(
        description="A brief explanation of the validation result. If valid, explain why. If invalid, explain the error."
    )

    errors: Optional[List[str]] = Field(
        description="A list of syntax or semantical errors in the Cypher statement. Always explain the discrepancy between schema and Cypher statement"
    )
    filters: Optional[List[Property]] = Field(
        description="A list of property-based filters applied in the Cypher statement."
    )
