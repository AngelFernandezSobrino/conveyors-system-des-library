from __future__ import annotations
from typing import TYPE_CHECKING

import openpyxl as xl  # type: ignore
import itertools

import pprint

pp = pprint.PrettyPrinter(depth=4)

if TYPE_CHECKING:
    from desim.objects.stopper.core import StopperDescription
    from desim.objects.system import SystemDescription


class ConfigParser:
    def __init__(self, file_directory) -> None:
        self.file_directory: str = file_directory
        self.config: SystemDescription = {}
        self.config_available = False

    def parse(self, sheet_name):
        wb = xl.load_workbook(self.file_directory, read_only=True, data_only=True)
        ws = wb[sheet_name]
        headers = next(ws.rows)
        if headers[0].value != "stopper_id":
            raise Exception(
                "Excel format not compatible, first column must be stopper indexes and be named index"
            )

        column_names = [str(column_name.value) for column_name in headers]

        conversions = next(itertools.islice(ws.rows, 1, None))

        conversion_types = [str(column_name.value) for column_name in conversions]

        for row in ws.rows:
            if row[0].row < 3:
                continue
            for i, cell in enumerate(row):
                if cell.value is None:
                    continue

                value = cell.value

                if conversion_types[i] == "str":
                    value = str(value)

                if str(row[0].value) not in self.config:
                    self.config[str(row[0].value)] = {}  # type: ignore

                if (i > 0 and column_names[i - 1] == column_names[i]) or (
                    i < len(row) - 1 and column_names[i + 1] == column_names[i]
                ):
                    if column_names[i] not in self.config[str(row[0].value)]:
                        self.config[str(row[0].value)][column_names[i]] = [value]  # type: ignore
                    else:
                        self.config[str(row[0].value)][column_names[i]] += [value]  # type: ignore
                else:
                    self.config[str(row[0].value)][column_names[i]] = value  # type: ignore

        self.config_available = True


if __name__ == "__main__":
    config = ConfigParser("../../../data/simulator_config.xlsx")

    config.parse("config_parser")

    print(config.config_available)
    pp.pprint(config.config)
