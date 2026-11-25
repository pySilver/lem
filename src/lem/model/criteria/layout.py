"""A text as the reader of the criteria takes it: its lines, those inside a code block, the
lines of the criteria's section, its charts, and How it works."""

from dataclasses import dataclass

from lem.model.criteria import fences, section


@dataclass(frozen=True, kw_only=True, slots=True)
class Layout:
    """The text `name`: its rows, the code lines, the section, its charts, How it works."""

    name: str
    rows: section.Rows
    code: section.Code
    bounds: range
    charts: section.Charts
    how: str | None

    def chart(self, index: int) -> str | None:
        """The text of the chart whose block opens at line `index`."""
        return section.chart_of(self.rows, self.charts[index])

    def where(self, index: int) -> str:
        """Line `index` as a refusal names it: `plan.md:12`."""
        number = index + 1
        return f"{self.name}:{number}"


def code_of(blocks: tuple[fences.Fence, ...]) -> section.Code:
    """The numbers of the lines inside a block, its fences too."""
    spans = (range(block.first, block.last + 1) for block in blocks)
    return frozenset(index for span in spans for index in span)


def layout_of(text: str, name: str) -> Layout:
    """The layout of `text`, the file `name`; a text with no section is refused."""
    rows = tuple(text.splitlines())
    blocks = fences.fences(list(rows))
    code = code_of(blocks)
    bounds = section.bounds(rows, code, name)
    return Layout(
        name=name,
        rows=rows,
        code=code,
        bounds=bounds,
        charts=section.charts(blocks, bounds),
        how=section.how_it_works(rows, code),
    )
