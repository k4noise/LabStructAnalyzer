from typing import Self, Dict, Union, Sequence, Mapping, cast

from fastapi_hypermodel import HALHyperModel as HyperModel, FrozenDict
from fastapi_hypermodel.hal.hal_hypermodel import HALLinkType
from pydantic import model_validator, ConfigDict, Field, model_serializer


class HALHyperModel(HyperModel):
    """
    Небольшая кучка костылей, перезаписывающих удаление аттрибутов и настройки сериализации
    """
    embedded: Mapping[str, Union[Self, Sequence[Self]]] = Field(default=None, alias="_embedded")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def add_hypermodels_to_embedded(self: Self) -> Self:
        """Добавляем без удаления аттрибутов"""
        embedded = {}

        for name, field in self:
            if not isinstance(field, list):
                continue

            key = self.model_fields[name].alias or name
            embedded[key] = field

        self.embedded = embedded
        return self

    @model_validator(mode="after")
    def add_links(self: Self) -> Self:
        """Удаляются curies, если не были заданы"""
        links_key = "_links"

        validated_links: Dict[str, HALLinkType] = {}
        for name, value in self:
            alias = self.model_fields[name].alias or name

            if alias != links_key or not value:
                continue

            links = cast(Mapping[str, HALLinkType], value)
            for link_name, link_ in links.items():
                valid_links = self._validate_factory(link_, vars(self))

                if not valid_links:
                    continue

                first_link, *_ = valid_links
                validated_links[link_name] = (
                    valid_links if isinstance(link_, Sequence) else first_link
                )
            if HALHyperModel.curies():
                validated_links["curies"] = HALHyperModel.curies()  # type: ignore

            self.links = FrozenDict(validated_links)

        return self

    @model_serializer(mode='plain')
    def remove_extra(self):
        """Логика вместо удаления аттрибутов - удаление ненужного из сериализованных данных"""
        data = dict(self.__dict__)

        for field_name, field in self.model_fields.items():
            if field.exclude and field_name in data:
                del data[field_name]

        keys_to_remove = []
        for key, value in data.items():
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                keys_to_remove.append(key)

        for k in keys_to_remove:
            del data[k]

        if "_embedded" in data and data["_embedded"] is None:
            del data["_embedded"]

        return data
