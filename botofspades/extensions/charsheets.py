from io import TextIOWrapper
from pathlib import Path
from json import dump, load
from typing import Any, Optional, Type
import os.path as path

from discord.ext import commands

from botofspades.log import extension_loaded, extension_unloaded


TEMPLATE_EXTENSION: str = "cstemplate"
CHARSHEET_EXTENSION: str = "cscharsheet"

base_dir: Path = Path.cwd() / "charsheets"
templates_dir: Path = base_dir / "templates"
charsheets_dir: Path = base_dir / "sheets"


class Field:
    def __init__(self, value: Any) -> None:
        self._value: Any = value

    def __str__(self) -> str:
        return str(self._value)

    def validate(self, value: Any) -> bool:
        return False

    def to_python_obj(self) -> Any:
        return self._value


class Abacus(Field):
    def __init__(self, value: Any) -> None:
        self._value: int = int(value)

    def to_python_obj(self) -> int:
        return self._value


class Rational(Field):
    def __init__(self, value: Any) -> None:
        self._value: float = float(value)

    def to_python_obj(self) -> float:
        return self._value


class Lever(Field):
    def __init__(self, value: Any) -> None:
        value = value.lower()

        if value in ("on", "true", "1", 1):
            self._value: bool = True
        elif value in ("off", "false", "0", 0):
            self._value: bool = False
        else:
            raise ValueError(f"Invalid value '{value}' for Lever field")

    def __str__(self) -> str:
        return "on" if self._value else "off"

    def to_python_obj(self) -> bool:
        return self._value


class Scroll(Field):
    def __init__(self, value: Any) -> None:
        self._value: str = str(value)

    def to_python_obj(self) -> str:
        return self._value


class Gauge(Field):
    def __init__(self, value: Any) -> None:
        if isinstance(value, (list, tuple)):
            self._current: int = int(value[0])
            self._max: int = int(value[1])
        elif isinstance(value, str):
            gauge_sides: list[str] = value.split("/")
            self._current: int = int(gauge_sides[0])
            self._max: int = int(gauge_sides[1])
        else:
            raise TypeError(
                "Gauge() argument must be a string or a Sequence[int, int],"
                f" not '{type(value)}'"
            )

    def __str__(self) -> str:
        return f"{self._current}/{self._max}"

    def to_python_obj(self) -> tuple[int, int]:
        return (self._current, self._max)


FIELD_TYPES: dict[str, Type[Field]] = {
    "abacus": Abacus,
    "rational": Rational,
    "lever": Lever,
    "scroll": Scroll,
    "gauge": Gauge,
}


class JSONFileWrapperReadOnly:
    def __init__(self, path: Path) -> None:
        self._file: Optional[TextIOWrapper] = None
        self._path: Path = path

    def _open_json(self) -> None:
        self._file = self._path.open("r")

    def _close_json(self) -> None:
        if self._file:
            self._file.close()

    def __enter__(self):
        if not self._path.exists():
            raise FileNotFoundError(self._path.name)

        self._open_json()

        return (
            load(self._file) if self._file and path.getsize(self._path) else {}
        )

    def __exit__(self, exc_type, exc_value, trace) -> bool:
        self._close_json()

        return False

class JSONFileWrapperUpdate(JSONFileWrapperReadOnly):
    def __init__(self, path: Path) -> None:
        super().__init__(path)

        self._dict: dict

    def _open_json(self) -> None:
        self._file = self._path.open("r+")

    def _close_json(self) -> None:
        if self._file:
            self._file.seek(0)
            self._file.truncate(0)
            dump(self._dict, self._file, indent=2)
            self._file.close()

    def __enter__(self):
        self._dict = super().__enter__()
        return self._dict


def get_template_path(name: str) -> Path:
    return templates_dir / f"{name}.{TEMPLATE_EXTENSION}"


def get_sheet_path(name: str) -> Path:
    return charsheets_dir / f"{name}.{CHARSHEET_EXTENSION}"


def get_field_string(name: str, value: dict) -> str:
    return (
        f"**{name.title()}** ({value['type'].title()})"
        + (f" [default is {value['default']}]" if value["default"] else "")
    )


def get_sheet_string(name: str, template: str) -> str:
    return f"**{name.title()}** (from `{template}`)"


class Charsheets(commands.Cog):
    @classmethod
    async def _reply_no_subcommand(cls, ctx) -> None:
        await ctx.message.reply(
            "No valid subcommand provided. Available subcommands: "
            + (", ".join(
                [f"`{command.name}`" for command in ctx.command.commands]
            ))
            + "."
        )

    @classmethod
    async def _update_field(
        cls, ctx, sheet_name: str, field_name: str,
        sheet_path: Path, value: str
    ) -> None:
        with JSONFileWrapperUpdate(sheet_path) as sheet:
            template_path: Path = get_template_path(sheet["template"])

            if not template_path.exists():
                await ctx.message.reply(
                    f"Template `{sheet['template']}` not found."
                )
                return

            with JSONFileWrapperReadOnly(template_path) as template:
                type: str = template["fields"][field_name]["type"]

                try:
                    new_value: Any = FIELD_TYPES[type](value).to_python_obj()
                    sheet["fields"][field_name] = new_value

                    await ctx.message.reply(
                        f"Value of {sheet_name.title()}:"
                        f" {field_name.title()} set to"
                        f" {sheet['fields'][field_name]}."
                    )
                except Exception as e:
                    await ctx.message.reply(
                        f"Invalid value `{value}` for type {type.title()}."
                    )

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx, error: commands.CommandError
    ) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.reply(
                f"Missing argument `{error.param}`.\n"
                f"Usage: `{ctx.command.usage}`."
            )

    @commands.group(invoke_without_command=True, aliases=("cs",))
    async def charsheets(self, ctx) -> None:
        await self._reply_no_subcommand(ctx)

    @charsheets.group(invoke_without_command=True, aliases=("tp",))
    async def template(self, ctx) -> None:
        await self._reply_no_subcommand(ctx)

    @template.command(name="add", usage="charsheets template add <name>")
    async def template_add(self, ctx, name: str) -> None:
        name = name.lower()

        template_path: Path = get_template_path(name)

        try:
            template_path.touch()

            with JSONFileWrapperUpdate(template_path) as template:
                template["fields"] = {}

            await ctx.message.reply(f"Template `{name}` successfully created.")
        except FileExistsError:
            await ctx.message.reply("This template already exists.")

    @template.command(
        name="remove", aliases=("rm",),
        usage="charsheets template remove <name>*"
    )
    async def template_remove(self, ctx, *names: str) -> None:
        output_msg: str = ""
        for name in [name.lower() for name in names]:
            template_path: Path = get_template_path(name)

            try:
                template_path.unlink()
                output_msg += f"Template `{name}` successfully removed.\n"
            except FileNotFoundError:
                output_msg += f"Template `{name}` not found.\n"

        await ctx.message.reply(output_msg)

    @template.command(
        name="rename", aliases=("rn",),
        usage="charsheets template rename <old name> <new name>"
    )
    async def template_rename(self, ctx, old_name: str, new_name: str) -> None:
        old_name = old_name.lower()
        new_name = new_name.lower()

        template_path: Path = get_template_path(old_name)
        target_path: Path = get_template_path(new_name)

        if not template_path.exists():
            await ctx.message.reply(f"Template `{old_name}` not found.")
            return

        if target_path.exists():
            await ctx.message.reply(
                f"A template with the name `{new_name}` already exists."
            )
            return

        template_path.rename(target_path)
        await ctx.message.reply(
            f"Template `{old_name}` successfully renamed to `{new_name}`."
        )

    @template.command(
        name="list", aliases=("ls",), usage="charsheets template list"
    )
    async def template_list(self, ctx) -> None:
        template_names: list[str] = [
            template_path.stem.title() for template_path in
            templates_dir.glob(f"*.{TEMPLATE_EXTENSION}")
        ]

        await ctx.message.reply(
            ("Available templates:\n- " + "\n- ".join(template_names))
            if template_names else "No templates available."
        )

    @template.group(name="field", invoke_without_command=True, aliases=("fd",))
    async def template_field(self, ctx) -> None:
        await self._reply_no_subcommand(ctx)

    @template_field.command(
        name="add",
        usage=(
            "charsheets template field add"
            " <template> <field> <type> [default value]"
        )
    )
    async def template_field_add(
        self, ctx, template_name: str, field_name: str,
        type: str, default: str = ""
    ) -> None:
        template_name = template_name.lower()
        field_name = field_name.lower()
        type = type.lower()

        if type not in FIELD_TYPES:
            await ctx.message.reply(f"Invalid type `{type}`.")
            return

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await ctx.message.reply(f"Template `{template_name}` not found.")
            return

        default_value: Any = None
        if default:
            try:
                default_value = FIELD_TYPES[type](default).to_python_obj()
            except Exception as e:
                await ctx.message.reply(
                    f"Invalid default value `{default}` for type `{type}`."
                )
                print(e)
                return

        with JSONFileWrapperUpdate(template_path) as template:
            if field_name in template["fields"]:
                await ctx.message.reply(
                    f"Field `{field_name}` already exists."
                )
                return

            template["fields"][field_name] = {
                "type": type,
                "default": default_value
            }

            await ctx.message.reply(
                "Field "
                + get_field_string(field_name, template['fields'][field_name])
                + f" successfully added to template `{template_name}`."
            )

    @template_field.command(
        name="remove", aliases=("rm",),
        usage="charsheets template field remove <field>*"
    )
    async def template_field_remove(
        self, ctx, template_name: str, *field_names: str
    ) -> None:
        template_name = template_name.lower()

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await ctx.message.reply(f"Template `{template_name}` not found.")
            return

        output_msg: str = ""
        with JSONFileWrapperUpdate(template_path) as template:
            for field_name in [name.lower() for name in field_names]:
                if not field_name in template["fields"]:
                    output_msg += f"Field `{field_name}` not found."

                    continue

                del template["fields"][field_name]
                output_msg += (
                    f"Field `{field_name}"
                    f" ({template['fields'][field_name]['type']})`"
                )

        await ctx.message.reply(output_msg)

    @template_field.command(
        name="rename", aliases=("rn",),
        usage="charsheets template field rename <old name> <new name>"
    )
    async def template_field_rename(
        self, ctx, template_name: str, old_name: str, new_name: str
    ) -> None:
        template_name = template_name.lower()
        old_name = old_name.lower()
        new_name = new_name.lower()

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await ctx.message.reply(f"Template `{template_name}` not found.")
            return

        with JSONFileWrapperUpdate(template_path) as template:
            if not old_name in template["fields"]:
                await ctx.message.reply(f"Field `{old_name}` not found.")
                return

            if new_name in template["fields"]:
                await ctx.message.reply(f"Field `{new_name}` already exists.")
                return

            field: dict = template["fields"][old_name]
            del template["fields"][old_name]
            template[new_name] = field

            await ctx.message.reply(
                f"Field `{old_name} ({field['type']})`"
                f" renamed to `{new_name}`."
            )

    @template_field.command(
        name="list", aliases=("ls",),
        usage="charsheets template field list [type]"
    )
    async def template_field_list(
        self, ctx, template_name: str, type: str = "any"
    ) -> None:
        template_name = template_name.lower()
        type = type.lower()

        if type != "any" and type not in FIELD_TYPES:
            await ctx.message.reply(f"Invalid type `{type}`.")
            return

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await ctx.message.reply(f"Template `{template_name}` not found.")
            return

        output_msg: str = ""
        with template_path.open("r") as template_file:
            template = load(template_file)

            for name, value in template["fields"].items():
                if type != "any" and value["type"] != type:
                    continue

                output_msg += f"- {get_field_string(name, value)}\n"

        await ctx.message.reply(
            f"Fields in `{template_name}`:\n{output_msg}"
            if output_msg else "No fields found."
        )

    @template_field.command(
        name="edit", aliases=("ed",),
        usage=(
            "charsheets template field edit"
            " <template> <field> <new type> [new default]"
        )
    )
    async def template_field_edit(
        self, ctx, template_name: str, field_name: str,
        type: str, default: str = ""
    ) -> None:
        template_name = template_name.lower()
        field_name = field_name.lower()
        type = type.lower()

        if type not in FIELD_TYPES:
            await ctx.message.reply(f"Invalid type `{type}`.")
            return

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await ctx.message.reply(f"Template `{template_name}` not found.")
            return

        default_value: Any = None
        if default:
            try:
                default_value = FIELD_TYPES[type](default).to_python_obj()
            except Exception as e:
                await ctx.message.reply(
                    f"Invalid default value `{default}` for type `{type}`."
                )
                print(e)
                return

        # TODO: Update all sheets using this template if type changes

        with JSONFileWrapperUpdate(template_path) as template:
            if field_name not in template["fields"]:
                await ctx.message.reply(f"Field `{field_name}` not found.")
                return

            template["fields"][field_name] = {
                "type": type,
                "default": default_value
            }

            await ctx.message.reply(
                f"Field updated to "
                + get_field_string(field_name, template['fields'][field_name])
            )


    @charsheets.group(invoke_without_command=True, aliases=("sh",))
    async def sheet(self, ctx) -> None:
        await self._reply_no_subcommand(ctx)

    @sheet.command(name="add")
    async def sheet_add(
        self, ctx, template_name: str, sheet_name: str
    ) -> None:
        template_name = template_name.lower()
        sheet_name = sheet_name.lower()

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await ctx.message.reply(f"Template `{template_name}` not found.")
            return

        sheet_path: Path = get_sheet_path(sheet_name)

        try:
            sheet_path.touch()
            with (
                JSONFileWrapperReadOnly(template_path) as template,
                JSONFileWrapperUpdate(sheet_path) as sheet
            ):
                sheet["template"] = template_name
                sheet["fields"] = {
                    field: template["fields"][field]["default"]
                    for field in template["fields"]
                }

            await ctx.message.reply(
                f"Sheet `{sheet_name}` (from template `{template_name}`)"
                " sucessfully created."
            )
        except FileExistsError:
            await ctx.message.reply(f"Sheet `{sheet_name}` already exists.")

    @sheet.command(name="remove", aliases=("rm",))
    async def sheet_remove(self, ctx, *names: str) -> None:
        output_msg: str = ""
        for name in [name.lower() for name in names]:
            sheet_path: Path = get_sheet_path(name)

            try:
                sheet_path.unlink()
                output_msg += f"Sheet `{name}` succesfully removed.\n"
            except FileNotFoundError:
                output_msg += f"Sheet `{name}` not found.\n"

        await ctx.message.reply(output_msg)

    @sheet.command(name="rename", aliases=("rn",))
    async def sheet_rename(self, ctx, old_name: str, new_name: str) -> None:
        old_name = old_name.lower()
        new_name = new_name.lower()

        old_path: Path = get_sheet_path(old_name)

        if not old_path.exists():
            await ctx.message.reply(f"Sheet `{old_name}` not found.")
            return

        new_path: Path = get_sheet_path(new_name)

        if new_path.exists():
            await ctx.message.reply(f"Sheet `{new_name}` already exists.")
            return

        old_path.rename(new_path)
        await ctx.message.reply(
            f"Sheet `{old_name}` successfully renamed to `{new_name}`."
        )

    @sheet.command(name="list", aliases=("ls",))
    async def sheet_list(self, ctx, template: str = "") -> None:
        if template and not get_template_path(template).exists():
            await ctx.message.reply(f"Template `{template}` not found.")
            return

        sheet_list: list[str] = []
        for sheet_path in charsheets_dir.glob(f"*.{CHARSHEET_EXTENSION}"):
            with JSONFileWrapperReadOnly(sheet_path) as sheet:
                if not template or sheet["template"] == template:
                    sheet_list.append(get_sheet_string(
                        sheet_path.stem, sheet["template"]
                    ))

        await ctx.message.reply(
            ("Available sheets:\n- " + "\n- ".join(sheet_list))
            if sheet_list else "No sheets found."
        )

    @sheet.command(name="totext", aliases=("txt",))
    async def sheet_totext(self, ctx, name: str) -> None:
        name = name.lower()

        sheet_path: Path = get_sheet_path(name)

        if not sheet_path.exists():
            await ctx.message.reply(f"Sheet `{name}` not found.")
            return

        output_msg: str = f"```\n{name.upper()}\n"
        with JSONFileWrapperReadOnly(sheet_path) as sheet:
            template_path: Path = get_template_path(sheet["template"])

            if not template_path.exists():
                await ctx.message.send(
                    f"Template `{sheet['template']}` not found."
                )
                return

            with JSONFileWrapperReadOnly(template_path) as template:
                for field in sheet["fields"]:
                    output_msg += (
                        f"{4 * ' '}{field.title()}"
                        f" ({template['fields'][field]['type'].title()})"
                        f" is {sheet['fields'][field]}\n"
                    )

        output_msg += "```"

        await ctx.message.reply(output_msg)

    @sheet.command(name="field", aliases=("fd",))
    async def sheet_field(
        self, ctx, sheet_name: str, field_name: str, value: str = ""
    ) -> None:
        sheet_name = sheet_name.lower()
        field_name = field_name.lower()

        sheet_path: Path = get_sheet_path(sheet_name)

        if not sheet_path.exists():
            await ctx.message.reply(f"Sheet `{sheet_name}` not found.")
            return

        if value:
            await self._update_field(
                ctx, sheet_name, field_name, sheet_path, value
            )
        else:
            with JSONFileWrapperReadOnly(sheet_path) as sheet:
                if field_name not in sheet["fields"]:
                    await ctx.message.reply(f"Field `{field_name}` not found.")
                    return

                await ctx.message.reply(
                    f"{sheet_name.title()}: {field_name.title()} ="
                    f" {sheet['fields'][field_name]}"
                )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Charsheets())
    extension_loaded("Charsheets")


def teardown(bot: commands.Bot) -> None:
    bot.remove_cog("Charsheets")
    extension_unloaded("Charsheets")


# Ensure directory strucutre
for dir in (base_dir, templates_dir, charsheets_dir):
    dir.mkdir(exist_ok=True)
