from pydantic import BaseModel, ConfigDict


class CodeShape(BaseModel):
    """How elaborate a candidate's source is.

    Measured over the ``transform`` function alone, docstring stripped, so that the
    seed's module docstring - which every candidate inherits verbatim - cannot make
    one program look heavier than another.
    """

    model_config = ConfigDict(frozen=True)

    node_count: int
    branch_count: int
    magic_constant_count: int
    table_element_count: int
    cost: int
