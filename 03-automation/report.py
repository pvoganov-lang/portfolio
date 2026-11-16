"""Отчёт по продажам: CSV → Excel с формулами, сводками и графиками.

Запуск:
    python report.py --input data/sales.csv --output output/sales_report.xlsx

Что делает:
    1. читает выгрузку заказов из CSV;
    2. считает ключевые метрики, разбивки по категориям, месяцам и каналам;
    3. собирает Excel-файл: сводка, динамика, топ товаров, каналы;
    4. рисует графики прямо в Excel (их можно двигать и обновлять).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------
# Оформление
# --------------------------------------------------------------------------

COLOR_DARK = "#1F2933"
COLOR_ACCENT = "#C8602F"
COLOR_SOFT = "#F3ECE4"
COLOR_MUTED = "#7A6A5D"


def build_formats(workbook) -> dict[str, object]:
    return {
        "title": workbook.add_format(
            {"bold": True, "font_size": 16, "font_color": COLOR_DARK}
        ),
        "subtitle": workbook.add_format(
            {"font_size": 11, "font_color": COLOR_MUTED}
        ),
        "header": workbook.add_format(
            {
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": COLOR_DARK,
                "align": "center",
                "valign": "vcenter",
                "border": 0,
            }
        ),
        "text": workbook.add_format({"border": 1, "border_color": "#DDD5CC"}),
        "money": workbook.add_format(
            {"num_format": '#,##0 ₽', "border": 1, "border_color": "#DDD5CC"}
        ),
        "int": workbook.add_format(
            {"num_format": "#,##0", "border": 1, "border_color": "#DDD5CC"}
        ),
        "percent": workbook.add_format(
            {"num_format": "0.0%", "border": 1, "border_color": "#DDD5CC"}
        ),
        "metric_value": workbook.add_format(
            {"bold": True, "font_size": 18, "font_color": COLOR_ACCENT}
        ),
        "metric_money": workbook.add_format(
            {
                "bold": True,
                "font_size": 18,
                "font_color": COLOR_ACCENT,
                "num_format": '#,##0 ₽',
            }
        ),
        "metric_label": workbook.add_format({"font_size": 10, "font_color": COLOR_MUTED}),
        "total_row": workbook.add_format(
            {"bold": True, "bg_color": COLOR_SOFT, "num_format": '#,##0 ₽'}
        ),
    }


# --------------------------------------------------------------------------
# Данные
# --------------------------------------------------------------------------

def load_sales(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"date", "order_id", "category", "product", "qty", "price", "channel"}

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"В файле нет колонок: {', '.join(sorted(missing))}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).copy()
    df["revenue"] = df["qty"] * df["price"]
    df["month"] = df["date"].dt.to_period("M").astype(str)
    return df


def build_summary(df: pd.DataFrame) -> dict[str, object]:
    revenue = float(df["revenue"].sum())
    orders = int(df["order_id"].nunique())
    avg_check = revenue / orders if orders else 0.0
    items = int(df["qty"].sum())

    by_category = (
        df.groupby("category", as_index=False)
        .agg(revenue=("revenue", "sum"), orders=("order_id", "nunique"))
        .sort_values("revenue", ascending=False)
    )
    by_category["share"] = by_category["revenue"] / revenue if revenue else 0.0

    by_month = (
        df.groupby("month", as_index=False)["revenue"].sum().sort_values("month")
    )

    top_products = (
        df.groupby("product", as_index=False)
        .agg(revenue=("revenue", "sum"), qty=("qty", "sum"))
        .sort_values("revenue", ascending=False)
        .head(10)
    )

    by_channel = (
        df.groupby("channel", as_index=False)["revenue"].sum()
        .sort_values("revenue", ascending=False)
    )

    return {
        "revenue": revenue,
        "orders": orders,
        "avg_check": avg_check,
        "items": items,
        "by_category": by_category,
        "by_month": by_month,
        "top_products": top_products,
        "by_channel": by_channel,
        "period_start": df["date"].min().date(),
        "period_end": df["date"].max().date(),
    }


# --------------------------------------------------------------------------
# Excel
# --------------------------------------------------------------------------

def write_summary_sheet(writer, df: pd.DataFrame, summary: dict, fmt: dict) -> None:
    wb = writer.book
    ws = wb.add_worksheet("Сводка")
    writer.sheets["Сводка"] = ws

    ws.set_column("A:A", 3)
    ws.set_column("B:C", 28)
    ws.set_column("D:F", 18)

    ws.write("B2", "Отчёт по продажам", fmt["title"])
    ws.write(
        "B3",
        f"Период: {summary['period_start']} — {summary['period_end']}",
        fmt["subtitle"],
    )

    # ключевые метрики
    metrics = [
        ("Выручка", summary["revenue"], "money"),
        ("Заказов", summary["orders"], "int"),
        ("Средний чек", summary["avg_check"], "money"),
        ("Продано единиц", summary["items"], "int"),
    ]

    row = 5
    for label, value, kind in metrics:
        ws.write(row, 1, label, fmt["metric_label"])
        ws.write(row, 2, value, fmt["metric_money"] if kind == "money" else fmt["metric_value"])
        row += 1

    # таблица категорий
    start_row = 11
    ws.write(start_row, 1, "Категория", fmt["header"])
    ws.write(start_row, 2, "Заказов", fmt["header"])
    ws.write(start_row, 3, "Выручка", fmt["header"])
    ws.write(start_row, 4, "Доля", fmt["header"])

    cat = summary["by_category"]
    for i, rec in enumerate(cat.itertuples(index=False), start=start_row + 1):
        ws.write(i, 1, rec.category, fmt["text"])
        ws.write_number(i, 2, int(rec.orders), fmt["int"])
        ws.write_number(i, 3, float(rec.revenue), fmt["money"])
        ws.write_number(i, 4, float(rec.share), fmt["percent"])

    last_row = start_row + len(cat)
    ws.write(last_row + 1, 1, "Итого", fmt["total_row"])
    ws.write_formula(
        last_row + 1,
        3,
        f"=SUM(D{start_row + 2}:D{last_row + 1})",
        fmt["total_row"],
        summary["revenue"],
    )

    # график по категориям
    chart = wb.add_chart({"type": "bar"})
    chart.add_series(
        {
            "name": "Выручка по категориям",
            "categories": ["Сводка", start_row + 1, 1, last_row, 1],
            "values": ["Сводка", start_row + 1, 3, last_row, 3],
            "fill": {"color": COLOR_ACCENT},
            "border": {"none": True},
            "data_labels": {"value": True, "num_format": "#,##0"},
        }
    )
    chart.set_title({"name": "Выручка по категориям"})
    chart.set_legend({"none": True})
    chart.set_size({"width": 620, "height": 300})
    chart.set_style(2)
    ws.insert_chart("B" + str(last_row + 4), chart)


def write_dynamics_sheet(writer, summary: dict, fmt: dict) -> None:
    wb = writer.book
    ws = wb.add_worksheet("Динамика")
    writer.sheets["Динамика"] = ws

    ws.set_column("B:B", 16)
    ws.set_column("C:C", 18)

    ws.write("B2", "Выручка по месяцам", fmt["title"])
    ws.write("B4", "Месяц", fmt["header"])
    ws.write("C4", "Выручка", fmt["header"])

    months = summary["by_month"]
    for i, rec in enumerate(months.itertuples(index=False), start=4):
        ws.write(i, 1, rec.month, fmt["text"])
        ws.write_number(i, 2, float(rec.revenue), fmt["money"])

    last = 4 + len(months)
    chart = wb.add_chart({"type": "line"})
    chart.add_series(
        {
            "name": "Выручка",
            "categories": ["Динамика", 4, 1, last - 1, 1],
            "values": ["Динамика", 4, 2, last - 1, 2],
            "line": {"color": COLOR_ACCENT, "width": 2.5},
            "marker": {"type": "circle", "size": 6, "fill": {"color": COLOR_ACCENT}},
            "data_labels": {"value": True, "num_format": "#,##0"},
        }
    )
    chart.set_title({"name": "Динамика выручки"})
    chart.set_legend({"none": True})
    chart.set_size({"width": 680, "height": 320})
    ws.insert_chart("B" + str(last + 2), chart)


def write_products_sheet(writer, summary: dict, fmt: dict) -> None:
    wb = writer.book
    ws = wb.add_worksheet("Топ товаров")
    writer.sheets["Топ товаров"] = ws

    ws.set_column("B:B", 34)
    ws.set_column("C:D", 16)
    ws.set_column("E:E", 14)

    ws.write("B2", "Топ-10 товаров по выручке", fmt["title"])
    headers = ["Товар", "Продано, шт", "Выручка", "Доля в выручке"]
    for col, title in enumerate(headers, start=1):
        ws.write(3, col, title, fmt["header"])

    total = summary["revenue"] or 1
    for row, rec in enumerate(summary["top_products"].itertuples(index=False), start=4):
        ws.write(row, 1, rec.product, fmt["text"])
        ws.write_number(row, 2, int(rec.qty), fmt["int"])
        ws.write_number(row, 3, float(rec.revenue), fmt["money"])
        ws.write_number(row, 4, float(rec.revenue) / total, fmt["percent"])


def write_channels_sheet(writer, summary: dict, fmt: dict) -> None:
    wb = writer.book
    ws = wb.add_worksheet("Каналы")
    writer.sheets["Каналы"] = ws

    ws.set_column("B:B", 22)
    ws.set_column("C:D", 16)

    ws.write("B2", "Продажи по каналам", fmt["title"])
    ws.write("B4", "Канал", fmt["header"])
    ws.write("C4", "Выручка", fmt["header"])
    ws.write("D4", "Доля", fmt["header"])

    channels = summary["by_channel"]
    total = summary["revenue"] or 1

    for row, rec in enumerate(channels.itertuples(index=False), start=4):
        ws.write(row, 1, rec.channel, fmt["text"])
        ws.write_number(row, 2, float(rec.revenue), fmt["money"])
        ws.write_number(row, 3, float(rec.revenue) / total, fmt["percent"])

    last = 4 + len(channels)
    chart = wb.add_chart({"type": "pie"})
    chart.add_series(
        {
            "name": "Каналы",
            "categories": ["Каналы", 4, 1, last - 1, 1],
            "values": ["Каналы", 4, 2, last - 1, 2],
            "data_labels": {"percentage": True},
        }
    )
    chart.set_title({"name": "Доля каналов"})
    chart.set_size({"width": 520, "height": 320})
    ws.insert_chart("B" + str(last + 2), chart)


def build_report(df: pd.DataFrame, output: Path) -> dict[str, object]:
    summary = build_summary(df)
    output.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        fmt = build_formats(writer.book)
        write_summary_sheet(writer, df, summary, fmt)
        write_dynamics_sheet(writer, summary, fmt)
        write_products_sheet(writer, summary, fmt)
        write_channels_sheet(writer, summary, fmt)

    return summary


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Собрать Excel-отчёт по продажам")
    parser.add_argument("--input", default="data/sales.csv", type=Path)
    parser.add_argument("--output", default="output/sales_report.xlsx", type=Path)
    args = parser.parse_args()

    df = load_sales(args.input)
    summary = build_report(df, args.output)

    print(f"Готово: {args.output}")
    print(f"  выручка:      {summary['revenue']:,.0f} ₽".replace(",", " "))
    print(f"  заказов:      {summary['orders']}")
    print(f"  средний чек:  {summary['avg_check']:,.0f} ₽".replace(",", " "))
    print(f"  период:       {summary['period_start']} — {summary['period_end']}")


if __name__ == "__main__":
    main()
