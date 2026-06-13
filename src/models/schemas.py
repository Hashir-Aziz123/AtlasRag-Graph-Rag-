from pydantic import BaseModel, Field
from typing import List, Optional

class Entity(BaseModel):
    """A node in the Knowledge Graph."""
    name: str = Field(
        description="The canonical name of the entity. Capitalize properly and resolve abbreviations if obvious (e.g., 'CNN' -> 'Convolutional Neural Network')."
    )
    label: str = Field(
        description="Must be exactly one of: Person, Organization, Method, Metric, Dataset, Topic."
    )
    description: Optional[str] = Field(
        default=None, 
        description="A brief, one-sentence summary of the entity based ONLY on the text."
    )

class Relationship(BaseModel):
    """An edge connecting two entities in the Knowledge Graph."""
    source_entity: str = Field(
        description="The exact 'name' of the source entity."
    )
    target_entity: str = Field(
        description="The exact 'name' of the target entity."
    )
    relation_type: str = Field(
        description="Must be exactly one of: USES, IMPROVES, CITES, BELONGS_TO, EVALUATED_ON, AUTHORED, COMPARES_TO."
    )
    description: Optional[str] = Field(
        default=None, 
        description="Brief explanation of how or why they are related in this context."
    )

class GraphExtraction(BaseModel):
    """The root schema passed to the LLM for structured JSON generation."""
    entities: List[Entity] = Field(
        description="List of all unique entities found in the text chunk."
    )
    relationships: List[Relationship] = Field(
        description="List of all logical connections between the extracted entities."
    )