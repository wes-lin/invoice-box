import re
import pdfplumber
from typing import List, Tuple
from abc import abstractmethod
from datetime import datetime
import ast


class BasicConvert:

    def __init__(self, re) -> None:
        self.re = re

    def getValue(self, context):
        searchObj = re.search(
            self.re,
            context,
            re.M | re.I,
        )
        if searchObj:
            return self.convert(searchObj.group(1))
        return None

    @abstractmethod
    def convert(self, value):
        return value


class DateConvert(BasicConvert):
    def convert(self, value):
        value = re.sub(r"\s+|-|年|月|日|:", "", value)
        return datetime.strptime(value, "%Y%m%d")


class DateTimeConvert(BasicConvert):
    def convert(self, value):
        value = re.sub(r"\s+|-|年|月|日|:", "", value)
        return datetime.strptime(value, "%Y%m%d%H%M%S")


class MoneyConvert(BasicConvert):
    def convert(self, value):
        return "%.2f" % ast.literal_eval(value)


DATA: List[Tuple[str, BasicConvert]] = [
    (
        "order_date",
        DateTimeConvert(
            "下单时间.*([0-9]{4}-[0-9]{1,2}-[0-9]{1,2}[ ]{0,}[0-9]{2}:[0-9]{2}:[0-9]{2})",
        ),
    ),
    (
        "order_money",
        MoneyConvert(
            "总计[ ]{0,}(([0-9]+|[0-9]{0,})(.[0-9]{1,2}))",
        ),
    ),
    (
        "order_money",
        MoneyConvert(
            "合计[ ]{0,}(([0-9]+|[0-9]{0,})(.[0-9]{1,2}))",
        ),
    ),
    (
        "order_money",
        MoneyConvert(
            "实付款[ ]{0,}(([0-9]+|[0-9]{0,})(.[0-9]{1,2}))",
        ),
    ),
    (
        "invoice_date",
        DateConvert("开票日期:.*([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日)"),
    ),
    (
        "invoice_money",
        MoneyConvert("（小写）(([0-9]+|[0-9]{0,})(.[0-9]{1,2}))"),
    ),
    (
        "invoice_money",
        MoneyConvert("（ 小 写 ）(([0-9]+|[0-9]{0,})(.[0-9]{1,2}))"),
    ),
    (
        "trip_date",
        DateConvert("行程起止日期[^0-9]+([0-9]{4}-[0-9]{1,2}-[0-9]{1,2})"),
    ),
    (
        "trip_money",
        MoneyConvert("合计(([0-9]+|[0-9]{0,})(.[0-9]{1,2}))元"),
    ),
    (
        "filed_date",
        DateConvert("申请日期[^0-9]+([0-9]{4}-[0-9]{1,2}-[0-9]{1,2})"),
    ),
]


class Bill:
    def __init__(self, context):
        self.context = re.sub(r"￥|¥|\n|\r|<br />", "", context)

    def extract(self):
        data = {}
        for key, convert in DATA:
            value = convert.getValue(self.context)
            if value:
                data[key] = convert.getValue(self.context)
        return data

    def get_context(self):
        return self.context


class PDFBill(Bill):
    def __init__(self, pdf):
        self.pdf = pdfplumber.open(pdf)
        context = ""
        for page in self.pdf.pages:
            context += page.extract_text()
        super().__init__(context)

    def __del__(self):
        self.pdf.close()
