import io
import os, zipfile

from lxml import etree
from typing import Generator, List, Optional
from zipfile import ZipFile

from labstructanalyzer.utils.files.chain_storage import ChainStorage
from labstructanalyzer.utils.parser.common_elements import (
    ImageElement,
    TextElement,
    TableElement,
    CellElement, RowElement,
)

from labstructanalyzer.utils.parser.base_definitions import IParserElement

from labstructanalyzer.utils.parser.numbering_manager import (
    NumberingManager,
    NumberingItem,
    NumberingProps,
)

from labstructanalyzer.utils.parser.nesting_manager import NestingManager
from labstructanalyzer.utils.parser.structure.structure_manager import StructureManager


class DocxXmlManager:
    """Менеджер xml-файлов внутри документа docx.
    Сохраняет все необходимые для обработки docx xml-файлы в виде lxml дерева

    Attributes:
      NAMESPACES: Все используемые пространства имен внутри xml-файлов
      images_raw_data: Словарь взаимоотношений имени файла изображения к сырым данным изображения
      main_content_root: Корень xml файла с главным содержимым документа
      styles_root: Корень xml файла с содержимым стилей
      numberings_root: Корень xml файла с содержимым нумерации документа
      relations_root: Корень xml файла с содержимым файла отношений
    """

    NAMESPACES = {
        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        "r": "http://schemas.openxmlformats.org/package/2006/relationships",
        "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
        "odr": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }

    def __init__(self, document: bytes) -> None:
        """Инициализирует объект класса DocxXmlManager

        Arguments:
          document: Байты docx документа
        """
        with zipfile.ZipFile(io.BytesIO(document), "r") as template:
            self.load_template_files(template)
            self.images_raw_data = self.load_images(template, "word/media")

    def load_template_files(self, template: ZipFile) -> None:
        """Читает все необходимые для обработки docx документа xml-файлы в виде lxml деревьев

        Arguments:
          template: docx документ, открытый как zip-архив
        """
        self.main_content_root = self.file_to_etree(template, "word/document.xml")
        self.relations_root = self.file_to_etree(
            template, "word/_rels/document.xml.rels"
        )
        self.styles_root = self.file_to_etree(template, "word/styles.xml")
        self.numberings_root = self.file_to_etree(template, "word/numbering.xml")

    def load_images(self, template: ZipFile, media_folder: str) -> dict:
        """Читает все изображения из указанной папки как сырые данные

        Arguments:
          template: docx документ, открытый как zip-архив
          media_folder: Путь до папки с изображениями

        Returns:
          Словарь взаимоотношений имени файла изображения и сырых данных изображения
        """
        images = {}
        for filename in template.namelist():
            if not filename.startswith(media_folder):
                continue
            images[os.path.basename(filename)] = template.read(filename)
        return images

    @staticmethod
    def file_to_etree(template: ZipFile, file_path: str) -> Optional[etree.ElementTree]:
        """Метод для чтения xml файла и его преобразования в дерево lxml"""
        try:
            file = template.read(file_path)
            return etree.fromstring(file)
        except KeyError:
            print(f"Файл '{file_path}' не найден.")
            return None


class DocxParser:
    """Парсер содержимого документа docx.
    Конвертирует содержимое документа в массив структурных компонент согласно структуре

      Attributes:
        structure_manager: Инстанс класса StructureManager с методами для применения структуры к элементам документа
        xml_manager: Инстанс класса DocxXmlManager с изображениями и lxml деревьями основного содержимого, стилей, нумерации, связей документа
        image_parser: Инстанс класса ImageParser с методом для парсинга изображений
        table_parser: Инстанс класса TableParser с методом для парсинга таблиц
        text_parser: Инстанс класса TextParser с методом для парсинга текста
        numbering_manager: Инстанс класса NumberingManager с методами для работы с нумерацией внутри документа
        nesting_manager: Инстанс класса NestingManager с методами для вычисления уровня вложенности для каждого элемента
        style_id_to_numberings_data: Словарь взаимоотношений идентификатора стиля к данным нумерации - идентификатору и уровню нумерации
    """

    def __init__(self, document: bytes, structure: dict, image_save_prefix: str) -> None:
        """Инициализирует объект класса DocxParser

        Arguments:
          document: Байты docx документа
          structure: Словарь с данными структуры
          image_save_prefix: Подпапка для сохранения картинок
        """
        self.structure_manager = StructureManager(structure)
        self.xml_manager = DocxXmlManager(document)
        self.table_parser = TableParser(self.xml_manager, self.parse)
        self.image_parser = ImageParser(self.xml_manager, image_save_prefix)
        self.text_parser = TextParser(self.xml_manager)
        self.numbering_manager = NumberingManager()
        self.nesting_manager = NestingManager()
        self.style_id_to_numberings_data = self._parse_numbering_in_styles()

    def get_structure_components(self) -> List[dict]:
        """Получает список всех структурных компонент документа

        Returns:
          Список структурных компонент документа
        """
        return list(self.structure_manager.apply_structure(self.parse(self.xml_manager.main_content_root)))

    def parse(
            self, root_element: etree.Element
    ) -> Generator[IParserElement, None, None]:
        """Конвертирует содержимое элемента в JSON-объект и выполняет вычисление уровня вложенности каждого элемента

        Args:
          root_element: Элемент для парсинга

        Returns:
          Генератор JSON-объектов содержимого документа для последующего преобразования объектов к структуре
        """
        is_parse_cell_items = (
                root_element.tag == f'{{{self.xml_manager.NAMESPACES["w"]}}}tc'
        )

        exclude_ancestor_condition = (
            "" if is_parse_cell_items else "[not(ancestor::w:tbl)]"
        )
        iterator = root_element.xpath(
            f".//w:tbl | .//w:p{exclude_ancestor_condition}",
            namespaces=self.xml_manager.NAMESPACES,
        )

        for element in iterator:
            parsed_item = None
            if element.tag == f'{{{self.xml_manager.NAMESPACES["w"]}}}tbl':
                parsed_item = self.table_parser.parse(element)
            elif (
                    element.find(".//pic:blipFill", namespaces=self.xml_manager.NAMESPACES)
                    is not None
            ):
                parsed_item = self.image_parser.parse(element)
            else:
                parsed_item = self.text_parser.parse(element)

            if parsed_item is None:
                continue

            if is_parse_cell_items:
                parsed_item.is_cell_element = True

            if numbering_props := self._find_numbering(element):
                if not self.numbering_manager.has_numbering(
                        numbering_props.id, numbering_props.ilvl
                ):
                    numbering_data = self._get_numbering_data(numbering_props)
                    self.numbering_manager.add_numbering_data(
                        numbering_props.id, numbering_props.ilvl, numbering_data
                    )
                parsed_item.numbering_level = numbering_props.ilvl
                parsed_item.numbering_bullet_text = (
                    self.numbering_manager.get_next_point_text_value(
                        numbering_props.id, numbering_props.ilvl
                    )
                )

            parsed_item.nesting_level = self.nesting_manager.get_level(parsed_item)
            yield parsed_item

    def _find_numbering(self, element: etree.Element) -> Optional[NumberingProps]:
        """Исследует элемент на наличие в нем нумерации, при наличии возвращает свойства найденной нумерации.
        Обрабатывается 2 вида нумерации - вшитой в стиль и внешней, при наличии обоих одновременно приоритет всегда у внешней.
        Таблица - блочный элемент, не может быть элементом нумерации

        Args:
            element: Произвольный элемент документа - например, `<w:tc>`, `<pic:blipFill>`, `<w:p>` и так далее

        Returns:
            Свойства нумерации - id из тега `<w:numId>` и ilvl из тега `<w:ilvl>`
        """
        if element.tag == f'{{{self.xml_manager.NAMESPACES["w"]}}}tbl':
            return None

        numbering_element = element.find(
            ".//w:numPr", namespaces=self.xml_manager.NAMESPACES
        )
        if numbering_element is not None:
            numbering_data = self._parse_numbering_props(numbering_element)
            return numbering_data if numbering_data.id != "0" else None

        style_id = element.xpath(
            ".//w:pStyle/@w:val", namespaces=self.xml_manager.NAMESPACES
        )
        if style_id and self.style_id_to_numberings_data.get(style_id[0]):
            return self.style_id_to_numberings_data[style_id[0]]

        return None

    def _get_numbering_data(
            self, numbering_props: NumberingProps
    ) -> Optional[NumberingItem]:
        """Выполняет парсинг данных нумерации

        Args:
            numbering_props: Свойства нумерации - идентификатор и уровень

        Returns:
            Данные нумерации при существовании нумерации
        """
        if not numbering_props:
            return None
        numbering_element = self.xml_manager.numberings_root.xpath(
            f'.//w:num[@w:numId="{numbering_props.id}"]',
            namespaces=self.xml_manager.NAMESPACES,
        )
        if not numbering_element:
            return None

        numbering_data = self._parse_numbering_data(
            numbering_props.id, numbering_props.ilvl
        )

        if numbering_element[0].xpath(
                f'.//w:lvlOverride[@w:ilvl="{numbering_props.ilvl}"]',
                namespaces=self.xml_manager.NAMESPACES,
        ):
            overrided_numbering_data = self._parse_numbering_data(
                numbering_props.id,
                numbering_props.ilvl,
                True,
            )
            numbering_data = NumberingItem(
                format=overrided_numbering_data.format if overrided_numbering_data else numbering_data.format,
                startValue=overrided_numbering_data.startValue
                if overrided_numbering_data else numbering_data.startValue,
                text=overrided_numbering_data.text if overrided_numbering_data else numbering_data.text,
            )
        return numbering_data

    def _parse_numbering_props(self, element: etree.Element) -> NumberingProps:
        """Парсит свойства нумерации - идентификатор и уровень

        Args:
          element: Произвольный элемент документа - например, `<w:tc>`, `<pic:blipFill>`, `<w:p>` и так далее

        Returns:
          Свойства нумерации
        """
        numbering_id = element.xpath(
            "./w:numId/@w:val", namespaces=self.xml_manager.NAMESPACES
        )
        numbering_level = element.xpath(
            "./w:ilvl/@w:val", namespaces=self.xml_manager.NAMESPACES
        )
        numbering_level = int(numbering_level[0]) if numbering_level else 0
        return NumberingProps(id=numbering_id[0] if numbering_id else None, ilvl=numbering_level)

    def _parse_numbering_data(
            self,
            numbering_id: int,
            ilvl: int,
            for_overriding: bool = False,
    ) -> Optional[NumberingItem]:
        """Парсит данные нумерации

        Args:
          numbering_id: Идентификатор нумерации
          ilvl: Уровень нумерации
          for_overriding [optional]: Флаг, извлекать данные нумерации для перезаписи или нет

        Returns:
          Данные нумерации
        """
        level_element = None
        if for_overriding:
            level_element = self.xml_manager.numberings_root.xpath(
                f".//w:num[@w:numId='{numbering_id}']/w:lvlOverride[@w:ilvl='{ilvl}']/w:lvl",
                namespaces=self.xml_manager.NAMESPACES,
            )
        else:
            abstract_numbering_id = self.xml_manager.numberings_root.xpath(
                f".//w:num[@w:numId='{numbering_id}']/w:abstractNumId/@w:val",
                namespaces=self.xml_manager.NAMESPACES,
            )
            level_element = self.xml_manager.numberings_root.xpath(
                f".//w:abstractNum[@w:abstractNumId='{abstract_numbering_id[0]}']/w:lvl[@w:ilvl='{ilvl}']",
                namespaces=self.xml_manager.NAMESPACES,
            )

        if not level_element:
            return None

        numbering_format = level_element[0].xpath(
            ".//w:numFmt/@w:val", namespaces=self.xml_manager.NAMESPACES
        )
        if not numbering_format or numbering_format[0] == "none":
            return None

        numbering_text = level_element[0].xpath(
            ".//w:lvlText/@w:val", namespaces=self.xml_manager.NAMESPACES
        )
        numbering_start_value = level_element[0].xpath(
            ".//w:start/@w:val", namespaces=self.xml_manager.NAMESPACES
        )

        return NumberingItem(
            format=numbering_format[0],
            startValue=int(numbering_start_value[0]),
            text=numbering_text[0] if numbering_text else "",
        )

    def _parse_numbering_in_styles(self) -> dict[str, NumberingProps]:
        """Выполняет предобработку данных стилей с вложенной нумерацией

        Returns:
          Словарь взаимоотношений идентификатора стиля и данных нумерации
        """

        style_id_to_numberings_data = {}
        for style_with_numbering in self.xml_manager.styles_root.xpath(
                ".//w:style[.//w:numPr]", namespaces=self.xml_manager.NAMESPACES
        ):
            style_id = style_with_numbering.get(
                f"{{{self.xml_manager.NAMESPACES['w']}}}styleId"
            )
            numbering_element = style_with_numbering.find(
                ".//w:numPr", namespaces=self.xml_manager.NAMESPACES
            )
            numbering_props = self._parse_numbering_props(numbering_element)
            numbering_data = self._get_numbering_data(numbering_props)
            if numbering_data:
                style_id_to_numberings_data[style_id] = numbering_props
        return style_id_to_numberings_data


class ImageParser:
    """Парсер изображений из документа docx.
    Обработка изображений производится согласно отношениям медиа файлов.

    Attributes:
      xml_manager: Инстанс класса DocxXmlManager
      images_dir: Директория для сохранения изображений
    """

    def __init__(self, xml_manager: DocxXmlManager, images_dir: str) -> None:
        """Инициализирует объект класса ImageParser

        Args:
          xml_manager: Инстанс класса DocxXmlManager
          images_dir: Директория для сохранения изображений
        """
        self.xml_manager = xml_manager
        self.images_dir = images_dir

    def parse(self, image_element: etree.Element) -> Optional[ImageElement]:
        """Выполняет парсинг и сохранение изображения

        Args:
          image_element: Элемент `<w:p>`, содержащий внешнее изображение `<pic:blipFill>`

        Returns:
          JSON-объект данных изображения, если изображение существует, иначе None
        """
        embed_id = self._get_embed_id(image_element)
        if not embed_id:
            return None

        image_path = self._get_internal_file_path(embed_id)
        if not image_path:
            return None

        if image_data := self.xml_manager.images_raw_data.get(
                os.path.basename(image_path)
        ):
            image_extension = os.path.splitext(image_path)[1]
            return ImageElement(
                data=ChainStorage.get_default().save(self.images_dir, image_data, image_extension)
            )

        return None

    def _get_embed_id(self, element: etree.Element) -> Optional[str]:
        """Получает идентификатор отношения из элемента

        Args:
          element: Элемент `<w:p>`, содержащий внешнее изображение `<pic:blipFill>`

        Returns:
          Идентификатор найденного отношения, если оно присутствует
        """
        embed = element.xpath(".//@odr:embed", namespaces=self.xml_manager.NAMESPACES)
        return embed[0] if embed else None

    def _get_internal_file_path(self, embed_id: str) -> Optional[str]:
        """Получает путь до изображения по embed ID через отношения

        Args:
          embed_id: Идентификатор отношения

        Returns:
          Путь до изображения, если изображение с указанным идентификатором существует
        """
        image_path = self.xml_manager.relations_root.xpath(
            f'.//r:Relationship[@Id="{embed_id}"]/@Target',
            namespaces=self.xml_manager.NAMESPACES,
        )
        return image_path[0] if image_path else None


class TableParser:
    """Парсер таблиц в docx.

    Attributes:
      parser: Метод для обработки содержимого ячейки
      xml_manager: Инстанс класса DocxXmlManager
    """

    def __init__(self, xml_manager: DocxXmlManager, parser) -> None:
        """Инициализирует объект класса ImageParser

        Args:
          parser: Метод для обработки содержимого ячейки
        """
        self.parser = parser
        self.xml_manager = xml_manager

    def parse(self, element: etree.Element) -> TableElement:
        """Выполняет парсинг данных каждой ячейки таблицы и их преобразование

        Args:
          element: Элемент-таблица `<w:tbl>`

        Returns:
          JSON-объект табличных данных
        """
        table_data = []
        row_elements = element.findall(
            ".//w:tr", namespaces=self.xml_manager.NAMESPACES
        )

        for row_index, row_element in enumerate(row_elements):
            row_data = []

            for cell_element in row_element.findall(
                    ".//w:tc", namespaces=self.xml_manager.NAMESPACES
            ):
                if self._is_merged(cell_element):
                    continue

                cell_width = self._get_cell_width(cell_element)
                cell_height = self._get_cell_height(
                    row_elements, row_index, cell_element
                )
                cell_data = CellElement(
                    data=list(self.parser(cell_element)),
                    rows=cell_width,
                    cols=cell_height,
                )
                row_data.append(cell_data)
            table_data.append(RowElement(data=row_data))

        return TableElement(data=table_data)

    def _is_merged(self, cell: etree.Element):
        """Проверяет, объединена ли ячейка вертикально

        Args:
          cell: Элемент-ячейка `<w:tc>`

        Returns:
          Результат проверки на вертикальное объединение
        """
        merge_element = cell.find(
            ".//w:tcPr/w:vMerge", namespaces=self.xml_manager.NAMESPACES
        )

        if merge_element is None:
            return False

        merge_value = merge_element.get(f"{{{self.xml_manager.NAMESPACES['w']}}}val")
        if not merge_value or merge_value == 'continue':
            return True
        return False

    def _get_cell_width(self, cell: etree.Element) -> int:
        """Вычисляет ширину ячейки таблицы

        Args:
          cell: Ячейка таблицы `<w:tc>`

        Returns:
          Ширина ячейки
        """
        cell_gridspan = cell.xpath(
            ".//w:tcPr/w:gridSpan/@w:val", namespaces=self.xml_manager.NAMESPACES
        )
        return int(cell_gridspan[0]) if cell_gridspan else 1

    def _get_cell_height(
            self, rows: List[etree.Element], cell_row_index: int, cell: etree.Element
    ) -> int:
        """Вычисляет высоту ячейки таблицы.
        Ширина каждой ячейки вычисляется для корректной обработки объединенных по горизонтали ячеек

        Args:
          rows: Все строки таблицы `<w:tr>`
          cell: Ячейка таблицы `<w:tc>`
          cell_row_index: Индекс строки таблицы с ячейкой

        Returns:
          Высота ячейки таблицы
        """
        cell_height = 1
        merge_element = cell.find(
            ".//w:tcPr/w:vMerge", namespaces=self.xml_manager.NAMESPACES
        )
        if merge_element is None or not merge_element.get(
                f"{{{self.xml_manager.NAMESPACES['w']}}}val"
        ):
            return cell_height

        col_index = self._calc_cell_col_index(rows[cell_row_index], cell)
        for row_elements in rows[cell_row_index + 1::]:
            current_cell_index = -1

            for cell_element in row_elements.findall(
                    ".//w:tc", namespaces=self.xml_manager.NAMESPACES
            ):
                current_cell_index += self._get_cell_width(cell_element)
                if current_cell_index != col_index:
                    continue
                vertical_merge_element = cell_element.find(
                    ".//w:tcPr/w:vMerge", namespaces=self.xml_manager.NAMESPACES
                )
                if vertical_merge_element is None:
                    break

                vertical_merged = vertical_merge_element.get(
                    f'{{{self.xml_manager.NAMESPACES["w"]}}}val'
                )
                if vertical_merged == 'restart':
                    return cell_height
                elif not vertical_merged or vertical_merged == "continue":
                    cell_height += 1

        return cell_height

    def _calc_cell_col_index(
            self, row: etree.Element, cell: etree.Element
    ) -> int:
        """Вычисляет точный индекс колонки, содержащей ячейку
          Нужен для корректного учета ячеек, занимающих более одной колонки в ширину и находящихся перед искомой

          Args:
          row: Строка, содержащая ячейку `<w:tr>`
          cell: Ячейка таблицы `<w:tc>`

        Returns:
          Индекс колонки в таблице
        """
        col_index = -1

        for cell_element in row.xpath(
                ".//w:tc", namespaces=self.xml_manager.NAMESPACES
        ):
            col_index += self._get_cell_width(cell_element)
            if cell_element == cell:
                break
        return col_index


class TextParser:
    """Парсер текстового содержимого (параграф/заголовок/элемент списка) внутри документа docx.

    Attributes:
      xml_manager: Инстанс класса DocxXmlManager
      style_id_to_heading_level: Словарь взаимоотношений идентификатора стиля и уровня заголовка
    """

    def __init__(self, xml_manager: DocxXmlManager) -> None:
        """Инициализирует объект класса TextParser и выполняет необходимые предобработки

        Args:
          xml_manager: Инстанс класса DocxXmlManager
        """
        self.xml_manager = xml_manager
        self.style_id_to_heading_level = self._parse_header_levels()

    def parse(self, element: etree.Element) -> Optional[TextElement]:
        """Преобразует параграф в JSON-объект текстовых данных
        Если параграф имеет два вида нумерации - в стиле и в самом параграфе непосредственно, то приоритет отдается нумерации в параграфе, нумерация в стиле игнорируется

        Args:
          element: Элемент-абзац `<w:p>` с элементами `<w:t>`

        Returns:
          JSON-объект текстовых данных
        """
        paragraph_text = self._extract_paragraph_text(element)

        if not paragraph_text:
            return None

        paragraph_data = TextElement(data=paragraph_text)
        style_id = element.xpath(
            ".//w:pStyle/@w:val", namespaces=self.xml_manager.NAMESPACES
        )

        if style_id:
            style_id = style_id[0]
            paragraph_data.style_id = style_id
            paragraph_data.header_level = self.style_id_to_heading_level.get(style_id)

        return paragraph_data

    def _extract_paragraph_text(self, element: etree.Element) -> str:
        """Собирает все фрагменты текста в единое целое и корректно обрабатывает новые строки

        Args:
          element: Элемент `<w:p>` с элементами `<w:t>`

        Returns:
          Текст элемента
        """
        text_parts = []
        for node in element.xpath(
                ".//w:t | .//w:br", namespaces=self.xml_manager.NAMESPACES
        ):
            if node.tag == f'{{{self.xml_manager.NAMESPACES["w"]}}}br':
                text_parts.append("\n")
            elif node.text:
                text_parts.append(node.text)
        return "".join(text_parts).strip()

    def _parse_header_levels(self) -> dict[str, int]:
        """Парсит стили заголовков и запоминает их уровни.
        При обработке учитывает наличие пользовательских стилей заголовков, основанных на стандартных

        Returns:
          Словарь взаимоотношений идентификатора стиля и уровня заголовка
        """
        style_id_to_heading_level = {}
        header_level_shift = 1
        main_title = self.xml_manager.styles_root.xpath(
            './/w:style[w:name/@w:val="Title"]',
            namespaces=self.xml_manager.NAMESPACES,
        )
        if main_title:
            style_id_to_heading_level[
                main_title[0].get(f"{{{self.xml_manager.NAMESPACES['w']}}}styleId")
            ] = 1
            header_level_shift += 1

        for header_style in self.xml_manager.styles_root.xpath(
                ".//w:style[.//w:outlineLvl]", namespaces=self.xml_manager.NAMESPACES
        ):
            style_id = header_style.get(
                f"{{{self.xml_manager.NAMESPACES['w']}}}styleId"
            )
            header_level = int(
                header_style.xpath(
                    ".//w:outlineLvl/@w:val", namespaces=self.xml_manager.NAMESPACES
                )[0]
            )
            style_id_to_heading_level[style_id] = header_level + header_level_shift

            based_headers_ids = self.xml_manager.styles_root.xpath(
                f'.//w:style[w:basedOn/@w:val="{style_id}"]/@w:styleId',
                namespaces=self.xml_manager.NAMESPACES,
            )
            for based_header_id in based_headers_ids:
                style_id_to_heading_level[based_header_id] = header_level

        return style_id_to_heading_level
