import re
from pathlib import Path
from dataclasses import dataclass


DEF_INDENT_LEVEL: int = 4
ESCAPE_SEQUENCES: dict[str, str] = {"\\n": "\n"}


outdefs_path: Path = Path.cwd() / "botofspades/outdefs.outlang"
defbank: dict[str, str] = {}

defend_re = re.compile(r"^\n")
defname_re = re.compile(r"^\w{1,}\n")
defdesc_re = re.compile(rf"^\s{{{DEF_INDENT_LEVEL}}}.*\n")


@dataclass
class Emoji:
    SUCCESS: str = ":star2:"
    INFO: str = ":bell:"
    ERROR: str = ":small_red_triangle_down:"


async def send(ctx, defname: str, **replacements) -> None:
    await botsend(ctx, out(defname, **replacements))


async def botsend(ctx, msg: str) -> None:
    await ctx.message.reply(msg)


def out(defname: str, **replacements) -> str:
    return defbank[defname].format_map(
        ESCAPE_SEQUENCES | {"Emoji": Emoji} | replacements
    )


def format_defdesc(desc: str) -> str:
    return " ".join(desc.strip().split()) + "\n"


def update_defbank() -> None:
    global defbank

    defbank = {}

    defname: str = ""
    defdesc: str = ""

    with outdefs_path.open() as f:
        for line in f.readlines():
            if line.lstrip().startswith("#"):
                continue

            if defend_re.match(line) and defname and defdesc:
                defbank[defname] = format_defdesc(defdesc)
                defname = defdesc = ""
                continue

            if defname_re.match(line):
                defname = line[:-1]
                continue

            if defdesc_re.match(line):
                defdesc += line[:-1]

        if defname and defdesc:
            defbank[defname] = format_defdesc(defdesc)
