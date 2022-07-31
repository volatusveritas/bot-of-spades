from io import TextIOWrapper
from pathlib import Path
from json import dump, load
from typing import Any, Optional
import os.path as path

from discord.ext import commands

from botofspades.log import extension_loaded, extension_unloaded


EXTENSION_NAME: str = "Charsheets"
TEMPLATE_EXTENSION: str = "cstemplate"
CHARSHEET_EXTENSION: str = "cscharsheet"
SUCCESS_EMOJI: str = ":star2:"
INFO_EMOJI: str = ":notepad_spiral:"
ERROR_EMOJI: str = ":loudspeaker:"

base_dir: Path = Path.cwd() / "charsheets"
templates_dir: Path = base_dir / "templates"
charsheets_dir: Path = base_dir / "sheets"


class Field:
    def __init__(self, value: Any) -> None:
        self._value: Any = value

    def __str__(self) -> str:
        return str(self._value)

    @staticmethod
    def validate(value: Any) -> bool:
        return False

    def to_python_obj(self) -> Any:
        return self._value


class Abacus(Field):
    def __init__(self, value: Any) -> None:
        self._value: int = int(value)

    @staticmethod
    def validate(value: Any) -> bool:
        try:
            int(value)
        except:
            return False

        return True

    def to_python_obj(self) -> int:
        return self._value


class Rational(Field):
    def __init__(self, value: Any) -> None:
        self._value: float = float(value)

    @staticmethod
    def validate(value: Any) -> bool:
        try:
            float(value)
        except:
            return False

        return True

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


FIELD_TYPES: dict[str, type[Field]] = {
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


class OutputMessage:
    @staticmethod
    def not_found(what: str, detail: str) -> str:
        return f"{ERROR_EMOJI} {what.title()} **{detail}** not found."

    @staticmethod
    def none_found(what: str) -> str:
        return f"{ERROR_EMOJI} No {what} found."


def get_template_path(name: str) -> Path:
    return templates_dir / f"{name}.{TEMPLATE_EXTENSION}"


def get_sheet_path(name: str) -> Path:
    return charsheets_dir / f"{name}.{CHARSHEET_EXTENSION}"


def get_field_string(name: str, value: dict) -> str:
    return f"**{name.title()}** ({value['type'].title()})" + (
        f" [default is {value['default']}]" if value["default"] else ""
    )


def get_sheet_string(name: str, template: str) -> str:
    return f"**{name.title()}** (from **{template.title()}**)"


class Charsheets(commands.Cog):
    @classmethod
    async def _reply_no_subcommand(cls, ctx) -> None:
        await ctx.message.reply(
            f"{ERROR_EMOJI} "
            + "No valid subcommand provided. Available subcommands: "
            + (
                ", ".join(
                    [f"`{command.name}`" for command in ctx.command.commands]
                )
            )
            + "."
        )

    @classmethod
    async def _update_field(
        cls,
        ctx,
        sheet_name: str,
        field_name: str,
        sheet_path: Path,
        value: str,
    ) -> None:
        with JSONFileWrapperUpdate(sheet_path) as sheet:
            template_path: Path = get_template_path(sheet["template"])

            if not template_path.exists():
                await ctx.message.reply(
                    OutputMessage.not_found("template", sheet["template"])
                )
                return

            with JSONFileWrapperReadOnly(template_path) as template:
                type: str = template["fields"][field_name]["type"]

                try:
                    new_value: Any = FIELD_TYPES[type](value).to_python_obj()
                    sheet["fields"][field_name] = new_value

                    await ctx.message.reply(
                        f"{SUCCESS_EMOJI} "
                        f"Value of {sheet_name.title()}:"
                        f" {field_name.title()} set to"
                        f" {sheet['fields'][field_name]}."
                    )
                except Exception as e:
                    await ctx.message.reply(
                        f"{ERROR_EMOJI} "
                        f"Invalid value `{value}` for type {type.title()}."
                    )

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx, error: commands.CommandError
    ) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.reply(
                f"{ERROR_EMOJI} "
                f"Missing argument `{error.param}`\n"
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

            await ctx.message.reply(
                f"{SUCCESS_EMOJI} Template **{name}** successfully created."
            )
        except FileExistsError:
            await ctx.message.reply(
                f"{ERROR_EMOJI} This template already exists."
            )

    @template.command(
        name="remove",
        aliases=("rm",),
        usage="charsheets template remove <name>*",
    )
    async def template_remove(self, ctx, *names: str) -> None:
        output_msg: str = ""
        name_list: list[str] = [name.lower() for name in names]
        for name in name_list:
            template_path: Path = get_template_path(name)

            try:
                template_path.unlink()
                output_msg += (
                    f"{SUCCESS_EMOJI} "
                    f"Template **{name}** successfully removed.\n"
                )
            except FileNotFoundError:
                output_msg += OutputMessage.not_found("template", name) + "\n"

        sheets_changed: int = 0
        for path in charsheets_dir.glob(f"*.{CHARSHEET_EXTENSION}"):
            remove_sheet: bool = False
            with JSONFileWrapperReadOnly(path) as sheet:
                if sheet["template"] in name_list:
                    remove_sheet = True

            if remove_sheet:
                path.unlink()
                sheets_changed += 1

        output_msg += f"{INFO_EMOJI} {sheets_changed} sheets removed."

        await ctx.message.reply(output_msg)

    @template.command(
        name="rename",
        aliases=("rn",),
        usage="charsheets template rename <old name> <new name>",
    )
    async def template_rename(self, ctx, old_name: str, new_name: str) -> None:
        old_name = old_name.lower()
        new_name = new_name.lower()

        template_path: Path = get_template_path(old_name)
        target_path: Path = get_template_path(new_name)

        if not template_path.exists():
            await ctx.message.reply(
                OutputMessage.not_found("template", old_name)
            )
            return

        if target_path.exists():
            await ctx.message.reply(
                f"{ERROR_EMOJI} "
                f"A template with the name **{new_name}** already exists."
            )
            return

        template_path.rename(target_path)

        sheets_changed: int = 0
        for path in charsheets_dir.glob(f"*.{CHARSHEET_EXTENSION}"):
            with JSONFileWrapperUpdate(path) as sheet:
                if sheet["template"] == old_name:
                    sheet["template"] = new_name
                    sheets_changed += 1

        await ctx.message.reply(
            f"{SUCCESS_EMOJI} "
            f"Template **{old_name}** successfully renamed to"
            f" **{new_name}**.\n"
            f"{sheets_changed} sheets updated."
        )

    @template.command(
        name="list", aliases=("ls",), usage="charsheets template list"
    )
    async def template_list(self, ctx) -> None:
        template_names: list[str] = [
            template_path.stem.title()
            for template_path in templates_dir.glob(f"*.{TEMPLATE_EXTENSION}")
        ]

        await ctx.message.reply(
            (
                f"{INFO_EMOJI} "
                "Available templates:\n- " + "\n- ".join(template_names)
            ) if template_names
            else f"{ERROR_EMOJI} No templates available."
        )

    @template.group(name="field", invoke_without_command=True, aliases=("fd",))
    async def template_field(self, ctx) -> None:
        await self._reply_no_subcommand(ctx)

    @template_field.command(
        name="add",
        usage=(
            "charsheets template field add"
            " <template> <field> <type> [default value]"
        ),
    )
    async def template_field_add(
        self,
        ctx,
        template_name: str,
        field_name: str,
        type: str,
        default: str = "",
    ) -> None:
        template_name = template_name.lower()
        field_name = field_name.lower()
        type = type.lower()

        if type not in FIELD_TYPES:
            await ctx.message.reply(f"{ERROR_EMOJI} Invalid type **{type}**.")
            return

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await ctx.message.reply(
                OutputMessage.not_found("template", template_name)
            )
            return

        default_value: Any = None
        if default:
            try:
                default_value = FIELD_TYPES[type](default).to_python_obj()
            except Exception as e:
                await ctx.message.reply(
                    f"{ERROR_EMOJI} "
                    f"Invalid default value **{default}** for type **{type}**."
                )
                print(e)
                return

        output_msg: str = ""
        with JSONFileWrapperUpdate(template_path) as template:
            if field_name in template["fields"]:
                await ctx.message.reply(
                    f"{ERROR_EMOJI} Field **{field_name}** already exists."
                )
                return

            template["fields"][field_name] = {
                "type": type,
                "default": default_value,
            }

            output_msg += (
                f"{SUCCESS_EMOJI} Field "
                + get_field_string(field_name, template["fields"][field_name])
                + f" successfully added to template **{template_name}**.\n"
            )

        sheets_changed: int = 0
        for path in charsheets_dir.glob(f"*.{CHARSHEET_EXTENSION}"):
            with JSONFileWrapperUpdate(path) as sheet:
                if sheet["template"] == template_name:
                    sheet["fields"][field_name] = default_value
                    sheets_changed += 1

        output_msg += f"{INFO_EMOJI} {sheets_changed} sheets updated."

        await ctx.message.reply(output_msg)

    @template_field.command(
        name="remove",
        aliases=("rm",),
        usage="charsheets template field remove <field>*",
    )
    async def template_field_remove(
        self, ctx, template_name: str, *field_names: str
    ) -> None:
        template_name = template_name.lower()

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await ctx.message.reply(
                OutputMessage.not_found("template", template_name)
            )
            return

        field_list: list[str] = [name.lower() for name in field_names]

        output_msg: str = ""
        with JSONFileWrapperUpdate(template_path) as template:
            for field_name in field_list.copy():
                if field_name not in template["fields"]:
                    output_msg += (
                        OutputMessage.not_found("field", field_name) + "\n"
                    )
                    field_list.remove(field_name)

                    continue

                output_msg += (
                    f"{SUCCESS_EMOJI} Field **{field_name}**"
                    f" ({template['fields'][field_name]['type']}) removed.\n"
                )
                del template["fields"][field_name]

        sheets_changed: int = 0
        for path in charsheets_dir.glob(f"*.{CHARSHEET_EXTENSION}"):
            with JSONFileWrapperUpdate(path) as sheet:
                if sheet["template"] == template_name:
                    for field_name in field_list:
                        del sheet["fields"][field_name]

                    sheets_changed += 1

        output_msg += f"{INFO_EMOJI} {sheets_changed} sheets updated."

        await ctx.message.reply(output_msg)

    @template_field.command(
        name="rename",
        aliases=("rn",),
        usage="charsheets template field rename <old name> <new name>",
    )
    async def template_field_rename(
        self, ctx, template_name: str, old_name: str, new_name: str
    ) -> None:
        template_name = template_name.lower()
        old_name = old_name.lower()
        new_name = new_name.lower()

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await ctx.message.reply(
                OutputMessage.not_found("template", template_name)
            )
            return

        output_msg: str = ""
        with JSONFileWrapperUpdate(template_path) as template:
            if not old_name in template["fields"]:
                await ctx.message.reply(
                    OutputMessage.not_found("field", old_name)
                )
                return

            if new_name in template["fields"]:
                await ctx.message.reply(
                    f"{ERROR_EMOJI} Field **{new_name}** already exists."
                )
                return

            field: dict = template["fields"][old_name]
            del template["fields"][old_name]
            template[new_name] = field

            output_msg += (
                f"{SUCCESS_EMOJI} Field {get_field_string(old_name, field)}"
                f" successfully renamed to **{new_name}**.\n"
            )

        sheets_changed: int = 0
        for path in charsheets_dir.glob(f"*.{CHARSHEET_EXTENSION}"):
            with JSONFileWrapperUpdate(path) as sheet:
                if sheet["template"] == template_name:
                    field: dict = sheet["fields"][old_name]
                    del sheet["fields"][old_name]
                    sheet["fields"][new_name] = field

                    sheets_changed += 1

        output_msg += f"{INFO_EMOJI} {sheets_changed} sheets updated."

        await ctx.message.reply(output_msg)

    @template_field.command(
        name="list",
        aliases=("ls",),
        usage="charsheets template field list [type]",
    )
    async def template_field_list(
        self, ctx, template_name: str, type: str = "any"
    ) -> None:
        template_name = template_name.lower()
        type = type.lower()

        if type != "any" and type not in FIELD_TYPES:
            await ctx.message.reply(f"Invalid type **{type}**.")
            return

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await ctx.message.reply(
                OutputMessage.not_found("template", template_name)
            )
            return

        listed_fields: str = ""
        with template_path.open("r") as template_file:
            template = load(template_file)

            for name, value in template["fields"].items():
                if type != "any" and value["type"] != type:
                    continue

                listed_fields += f"- {get_field_string(name, value)}\n"

        await ctx.message.reply(
            f"{INFO_EMOJI} Fields in **{template_name}**:\n{listed_fields}"
            if listed_fields
            else OutputMessage.none_found("fields")
        )

    @template_field.command(
        name="edit",
        aliases=("ed",),
        usage=(
            "charsheets template field edit"
            " <template> <field> <new type> [new default]"
        ),
    )
    async def template_field_edit(
        self,
        ctx,
        template_name: str,
        field_name: str,
        type: str,
        default: str = "",
    ) -> None:
        template_name = template_name.lower()
        field_name = field_name.lower()
        type = type.lower()

        if type not in FIELD_TYPES:
            await ctx.message.reply(f"{ERROR_EMOJI} Invalid type **{type}**.")
            return

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await ctx.message.reply(
                OutputMessage.not_found("template", template_name)
            )
            return

        default_value: Any = None
        if default:
            try:
                default_value = FIELD_TYPES[type](default).to_python_obj()
            except Exception as e:
                await ctx.message.reply(
                    f"{ERROR_EMOJI} "
                    f"Invalid default value **{default}** for type **{type}**."
                )
                print(e)
                return

        output_msg: str = ""
        with JSONFileWrapperUpdate(template_path) as template:
            if field_name not in template["fields"]:
                await ctx.message.reply(
                    OutputMessage.not_found("field", field_name)
                )
                return

            template["fields"][field_name] = {
                "type": type,
                "default": default_value,
            }

            output_msg += (
                f"Field updated to "
                + get_field_string(field_name, template["fields"][field_name])
                + ".\n"
            )

        sheets_changed: int = 0
        for path in charsheets_dir.glob(f"*.{CHARSHEET_EXTENSION}"):
            with JSONFileWrapperUpdate(path) as sheet:
                if sheet["template"] == template_name:
                    sheet["fields"][field_name] = default_value
                    sheets_changed += 1

        output_msg += f"{INFO_EMOJI} {sheets_changed} sheets updated."

        await ctx.message.reply(output_msg)

    @charsheets.group(invoke_without_command=True, aliases=("sh",))
    async def sheet(self, ctx) -> None:
        await self._reply_no_subcommand(ctx)

    @sheet.command(name="add", usage="charsheets sheet add <name> <template>")
    async def sheet_add(
        self, ctx, sheet_name: str, template_name: str
    ) -> None:
        sheet_name = sheet_name.lower()
        template_name = template_name.lower()

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await ctx.message.reply(
                OutputMessage.not_found("template", template_name)
            )
            return

        sheet_path: Path = get_sheet_path(sheet_name)

        try:
            sheet_path.touch()
            with (
                JSONFileWrapperReadOnly(template_path) as template,
                JSONFileWrapperUpdate(sheet_path) as sheet,
            ):
                sheet["template"] = template_name
                sheet["fields"] = {
                    field: template["fields"][field]["default"]
                    for field in template["fields"]
                }

            await ctx.message.reply(
                f"{SUCCESS_EMOJI} "
                f"Sheet **{sheet_name}** (from template **{template_name}**)"
                " sucessfully created."
            )
        except FileExistsError:
            await ctx.message.reply(
                f"{ERROR_EMOJI} Sheet **{sheet_name}** already exists."
            )

    @sheet.command(
        name="remove", aliases=("rm",), usage="charsheets sheet remove <name>*"
    )
    async def sheet_remove(self, ctx, *names: str) -> None:
        output_msg: str = ""
        for name in [name.lower() for name in names]:
            sheet_path: Path = get_sheet_path(name)

            try:
                sheet_path.unlink()
                output_msg += (
                    f"{SUCCESS_EMOJI} Sheet **{name}** succesfully removed.\n"
                )
            except FileNotFoundError:
                output_msg += f"{ERROR_EMOJI} Sheet **{name}** not found.\n"

        await ctx.message.reply(output_msg)

    @sheet.command(
        name="rename",
        aliases=("rn",),
        usage="charsheets sheet rename <old name> <new name>",
    )
    async def sheet_rename(self, ctx, old_name: str, new_name: str) -> None:
        old_name = old_name.lower()
        new_name = new_name.lower()

        old_path: Path = get_sheet_path(old_name)

        if not old_path.exists():
            await ctx.message.reply(OutputMessage.not_found("sheet", old_name))
            return

        new_path: Path = get_sheet_path(new_name)

        if new_path.exists():
            await ctx.message.reply(
                f"{ERROR_EMOJI} Sheet **{new_name}** already exists."
            )
            return

        old_path.rename(new_path)
        await ctx.message.reply(
            f"{SUCCESS_EMOJI} "
            f"Sheet **{old_name.title()}** successfully renamed to"
            f" **{new_name.title()}**."
        )

    @sheet.command(
        name="list", aliases=("ls",), usage="charsheets sheet list [template]"
    )
    async def sheet_list(self, ctx, template: str = "") -> None:
        if template and not get_template_path(template).exists():
            await ctx.message.reply(
                OutputMessage.not_found("template", template)
            )
            return

        sheet_list: list[str] = []
        for sheet_path in charsheets_dir.glob(f"*.{CHARSHEET_EXTENSION}"):
            with JSONFileWrapperReadOnly(sheet_path) as sheet:
                if not template or sheet["template"] == template:
                    sheet_list.append(
                        get_sheet_string(sheet_path.stem, sheet["template"])
                    )

        await ctx.message.reply(
            (f"{INFO_EMOJI} Available sheets:\n- " + "\n- ".join(sheet_list))
            if sheet_list
            else OutputMessage.none_found("sheets")
        )

    @sheet.command(
        name="totext", aliases=("txt",), usage="charsheets sheet totext <name>"
    )
    async def sheet_totext(self, ctx, name: str) -> None:
        name = name.lower()

        sheet_path: Path = get_sheet_path(name)

        if not sheet_path.exists():
            await ctx.message.reply(OutputMessage.not_found("sheet", name))
            return

        output_msg: str = f"```\n{name.upper()}\n"
        with JSONFileWrapperReadOnly(sheet_path) as sheet:
            template_path: Path = get_template_path(sheet["template"])

            if not template_path.exists():
                await ctx.message.send(
                    OutputMessage.not_found("template", sheet["template"])
                )
                return

            with JSONFileWrapperReadOnly(template_path) as template:
                for field in sheet["fields"]:
                    type: str = template['fields'][field]['type']
                    output_msg += (
                        f"{4 * ' '}{field.title()} ({type.title()})"
                        f" is {FIELD_TYPES[type](sheet['fields'][field])}\n"
                    )

        output_msg += "```"

        await ctx.message.reply(output_msg)

    @sheet.command(
        name="field",
        aliases=("fd",),
        usage="charsheets sheet field <sheet> <field> [new value]",
    )
    async def sheet_field(
        self, ctx, sheet_name: str, field_name: str, value: str = ""
    ) -> None:
        sheet_name = sheet_name.lower()
        field_name = field_name.lower()

        sheet_path: Path = get_sheet_path(sheet_name)

        if not sheet_path.exists():
            await ctx.message.reply(
                OutputMessage.not_found("sheet", sheet_name)
            )
            return

        if value:
            await self._update_field(
                ctx, sheet_name, field_name, sheet_path, value
            )
        else:
            with JSONFileWrapperReadOnly(sheet_path) as sheet:
                if field_name not in sheet["fields"]:
                    await ctx.message.reply(
                        OutputMessage.not_found("field", field_name)
                    )
                    return

                await ctx.message.reply(
                    f"{INFO_EMOJI} "
                    f"{sheet_name.title()}: {field_name.title()} ="
                    f" {sheet['fields'][field_name]}."
                )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Charsheets())
    extension_loaded(EXTENSION_NAME)


def teardown(bot: commands.Bot) -> None:
    bot.remove_cog("Charsheets")
    extension_unloaded(EXTENSION_NAME)


# Ensure directory strucutre
for dir in (base_dir, templates_dir, charsheets_dir):
    dir.mkdir(exist_ok=True)
