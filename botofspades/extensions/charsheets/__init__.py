from pathlib import Path
from typing import Any

from discord.ext import commands
from discord import app_commands as apc
from discord import Interaction

from utils import get_str_varargs
from botofspades import unicode
from botofspades.extensions.charsheets import types
from botofspades.log import extension_loaded, extension_unloaded
from botofspades.outmsg import out, botsend, send
from botofspades.jsonwrappers import (
    JSONFileWrapperReadOnly,
    JSONFileWrapperUpdate
)
from botofspades.slash import add_slash_command, remove_slash_command


EXTENSION_NAME: str = "Charsheets"

base_dir: Path = Path.cwd() / "charsheets"
templates_dir: Path = base_dir / "templates"
charsheets_dir: Path = base_dir / "sheets"


FIELD_TYPES: dict[str, type[types.Field]] = {
    "abacus": types.Abacus,
    "rational": types.Rational,
    "lever": types.Lever,
    "scroll": types.Scroll,
    "gauge": types.Gauge,
}


def get_template_path(name: str) -> Path:
    return templates_dir / f"{name}.json"


def get_sheet_path(name: str) -> Path:
    return charsheets_dir / f"{name}.json"


def get_all_template_paths():
    return templates_dir.glob("*.json")


def get_all_sheet_paths():
    return charsheets_dir.glob("*.json")


def get_template_sheet_str(template: str, sheet: str) -> str:
    return f"{template.title()} :: {sheet.title()}"


def get_template_field_str(
    template: str,
    field: str,
    type_name: str,
    default: str
) -> str:
    return (
        f"{template.title()} :: {field.title()} ({type_name.title()})"
        + (f" [Default is {default}]" if default else "")
    )


def get_sheet_field_sig_str(sheet: str, field: str) -> str:
    return f"{sheet.title()} :: {field.title()}"


def get_sheet_field_str(sheet: str, field: str, value: str) -> str:
    return f"{get_sheet_field_sig_str(sheet, field)} = {value}"


def get_sheet_str(name: str, template: str) -> str:
    return f"**{name.title()}** (from **{template.title()}**)"


async def _update_field(
    itr: Interaction,
    sheet_name: str,
    field_name: str,
    sheet_path: Path,
    value: str,
) -> None:
    with JSONFileWrapperUpdate(sheet_path) as sheet:
        template_path: Path = get_template_path(sheet["template"])

        if not template_path.exists():
            await send(
                itr, "TEMPLATE_NOT_FOUND", name=sheet["template"].title()
            )
            return

        with JSONFileWrapperReadOnly(template_path) as template:
            type_name: str = template["fields"][field_name]["type"]

            try:
                old_value: Any = sheet["fields"][field_name]
                new_value: Any = FIELD_TYPES[type_name].from_str(value)
                sheet["fields"][field_name] = new_value

                await send(
                    itr,
                    "FIELD_VALUE_SET",
                    field=get_sheet_field_sig_str(sheet_name, field_name),
                    value=FIELD_TYPES[type_name].to_str(new_value),
                )
            except:
                await send(
                    itr,
                    "INVALID_FIELD_VALUE",
                    value=value,
                    type=type_name.title(),
                )


class Charsheets(apc.Group): ...

class Template(apc.Group):
    @apc.command(description="Creates a template.")
    async def add(self, itr: Interaction, name: str) -> None:
        name = name.lower()

        template_path: Path = get_template_path(name)

        try:
            template_path.touch(exist_ok=False)

            with JSONFileWrapperUpdate(template_path) as template:
                template["fields"] = {}

            await send(itr, "TEMPLATE_CREATED", name=name.title())
        except FileExistsError:
            await send(itr, "TEMPLATE_ALREADY_EXISTS", name=name.title())

    @apc.command(description="Deletes a template.")
    async def remove(self, itr: Interaction, names: str) -> None:
        output_msg: str = ""

        name_list: list[str] = [
            name.lower() for name in get_str_varargs(names)
        ]

        for name in name_list:
            template_path: Path = get_template_path(name)

            try:
                template_path.unlink()
                output_msg += out("TEMPLATE_REMOVED", name=name.title())
            except FileNotFoundError:
                output_msg += out("TEMPLATE_NOT_FOUND", name=name.title())

        sheets_changed: int = 0
        for path in get_all_sheet_paths():
            with JSONFileWrapperReadOnly(path) as sheet:
                if sheet["template"] not in name_list:
                    continue

            path.unlink()
            sheets_changed += 1

        if sheets_changed:
            output_msg += out("SHEETS_REMOVED", amount=sheets_changed)

        await botsend(itr, output_msg)

    @apc.command(description="Renames a template.")
    async def rename(
        self,
        itr: Interaction,
        old_name: str,
        new_name: str
    ) -> None:
        old_name = old_name.lower()
        new_name = new_name.lower()

        template_path: Path = get_template_path(old_name)
        target_path: Path = get_template_path(new_name)

        if not template_path.exists():
            await send(itr, "TEMPLATE_NOT_FOUND", name=old_name.title())
            return

        if target_path.exists():
            await send(itr, "TEMPLATE_ALREADY_EXISTS", name=new_name.title())
            return

        template_path.rename(target_path)

        sheets_changed: int = 0
        for path in get_all_sheet_paths():
            with JSONFileWrapperUpdate(path) as sheet:
                if sheet["template"] == old_name:
                    sheet["template"] = new_name
                    sheets_changed += 1

        output_msg: str = out(
            "TEMPLATE_RENAMED", old=old_name.title(), new=new_name.title()
        ) + (
            out("SHEETS_UPDATED", amount=sheets_changed)
            if sheets_changed
            else ""
        )

        await botsend(itr, output_msg)

    @apc.command(description="Lists available templates.")
    async def list(self, itr: Interaction) -> None:
        template_names: list[str] = [
            template_path.stem.title()
            for template_path in get_all_template_paths()
        ]

        await botsend(
            itr,
            (
                out(
                    "AVAILABLE_TEMPLATES",
                    separator=" ",
                    templates=", ".join(
                        [f"**{name}**" for name in template_names]
                    ),
                    finaldot=".",
                )
            )
            if template_names
            else out("NO_TEMPLATES_AVAILABLE"),
        )

    @apc.command(description="Adds a template field.")
    async def field_add(
        self,
        itr: Interaction,
        template_name: str,
        field_name: str,
        type_name: str,
        default: str = "",
    ) -> None:
        template_name = template_name.lower()
        field_name = field_name.lower()
        type_name = type_name.lower()

        if type_name not in FIELD_TYPES:
            await send(itr, "INVALID_FIELD_TYPE", type=type_name.title())
            return

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await send(itr, "TEMPLATE_NOT_FOUND", name=template_name.title())
            return

        default_value: Any = None

        if default:
            if not FIELD_TYPES[type_name].validate(default):
                await send(
                    itr,
                    "INVALID_DEFAULT_FIELD_VALUE",
                    value=default,
                    type=type_name.title(),
                )
                return

            default_value = FIELD_TYPES[type_name].from_str(default)

        output_msg: str = ""
        with JSONFileWrapperUpdate(template_path) as template:
            if field_name in template["fields"]:
                await send(
                    itr, "FIELD_ALREADY_EXISTS", name=field_name.title()
                )
                return

            template["fields"][field_name] = {
                "type": type_name,
                "default": default_value,
            }

            output_msg += out(
                "FIELD_ADDED",
                field=get_template_field_str(
                    template_name,
                    field_name,
                    type_name,
                    FIELD_TYPES[type_name].to_str(default_value)
                    if default_value else ""
                ),
                template=template_name.title(),
            )

        sheets_changed: int = 0
        for path in get_all_sheet_paths():
            with JSONFileWrapperUpdate(path) as sheet:
                if sheet["template"] == template_name:
                    sheet["fields"][field_name] = default_value
                    sheets_changed += 1

        if sheets_changed:
            output_msg += out("SHEETS_UPDATED", amount=sheets_changed)

        await botsend(itr, output_msg)

    @apc.command(description="Removes a template field.")
    async def field_remove(
        self,
        itr: Interaction,
        template_name: str,
        field_names: str
    ) -> None:
        template_name = template_name.lower()

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await send(itr, "TEMPLATE_NOT_FOUND", name=template_name.title())
            return

        field_list: list[str] = [
            name.lower() for name in get_str_varargs(field_names)
        ]

        output_msg: str = ""
        with JSONFileWrapperUpdate(template_path) as template:
            for field_name in field_list.copy():
                if field_name not in template["fields"]:
                    output_msg += out(
                        "FIELD_NOT_FOUND", name=field_name.title()
                    )
                    field_list.remove(field_name)

                    continue

                output_msg += out(
                    "FIELD_REMOVED",
                    field=get_template_field_str(
                        template_name,
                        field_name,
                        template["fields"][field_name]["type"],
                        FIELD_TYPES[
                            template["fields"][field_name]["type"]
                        ].to_str(template["fields"][field_name]["default"])
                        if template["fields"][field_name]["default"] else ""
                    ),
                    template=template_name.title(),
                )

                del template["fields"][field_name]

        sheets_changed: int = 0
        for path in get_all_sheet_paths():
            with JSONFileWrapperUpdate(path) as sheet:
                if sheet["template"] == template_name:
                    for field_name in field_list:
                        del sheet["fields"][field_name]

                    sheets_changed += 1

        if sheets_changed:
            output_msg += out("SHEETS_UPDATED", amount=sheets_changed)

        await botsend(itr, output_msg)

    @apc.command(description="Renames a template field.")
    async def field_rename(
        self,
        itr: Interaction,
        template_name: str,
        old_name: str,
        new_name: str
    ) -> None:
        template_name = template_name.lower()
        old_name = old_name.lower()
        new_name = new_name.lower()

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await send(itr, "TEMPLATE_NOT_FOUND", name=template_name.title())
            return

        output_msg: str = ""
        with JSONFileWrapperUpdate(template_path) as template:
            if not old_name in template["fields"]:
                await send(itr, "FIELD_NOT_FOUND", name=old_name.title())
                return

            if new_name in template["fields"]:
                await send(itr, "FIELD_ALREADY_EXISTS", name=new_name.title())
                return

            field: dict = template["fields"][old_name]
            del template["fields"][old_name]
            template[new_name] = field

            output_msg += out(
                "FIELD_RENAMED",
                field=get_template_field_str(
                    template_name,
                    old_name,
                    template["fields"][new_name]["type"],
                    FIELD_TYPES[
                        template["fields"][new_name]["type"]
                    ].to_str(template["fields"][new_name]["default"])
                ),
                new=new_name.title(),
            )

        sheets_changed: int = 0
        for path in get_all_sheet_paths():
            with JSONFileWrapperUpdate(path) as sheet:
                if sheet["template"] == template_name:
                    field: dict = sheet["fields"][old_name]
                    del sheet["fields"][old_name]
                    sheet["fields"][new_name] = field

                    sheets_changed += 1

        if sheets_changed:
            output_msg += out("SHEETS_UPDATED", amount=sheets_changed)

        await botsend(itr, output_msg)

    @apc.command(description="Lists the fields in a template.")
    async def field_list(
        self,
        itr: Interaction,
        template_name: str,
        type_name: str = "any"
    ) -> None:
        template_name = template_name.lower()
        type_name = type_name.lower()

        # TODO: Add this as an outdef.
        if type_name != "any" and type_name not in FIELD_TYPES:
            await botsend(itr, f"Invalid type **{type_name}**.")
            return

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await send(itr, "TEMPLATE_NOT_FOUND", name=template_name.title())
            return

        listed_fields: str = "\n"
        with JSONFileWrapperReadOnly(template_path) as template:
            for name, value in template["fields"].items():
                if type_name != "any" and value["type"] != type_name:
                    continue

                listed_fields += (
                    f"\n{unicode.FIELD_ARROW} "
                    + get_template_field_str(
                        template_name,
                        name,
                        value["type"],
                        FIELD_TYPES[value["type"]].to_str(value["default"])
                        if value["default"] else ""
                    )
                )

        await botsend(
            itr,
            (
                out(
                    "FIELD_LIST",
                    template=template_name.title(),
                    fields=f"{listed_fields}",
                )
            )
            if listed_fields
            else out("NO_FIELDS", template=template_name),
        )

    @apc.command(description="Modifies a template field's signature.")
    async def field_edit(
        self,
        itr: Interaction,
        template_name: str,
        field_name: str,
        type_name: str,
        default: str = "",
    ) -> None:
        template_name = template_name.lower()
        field_name = field_name.lower()
        type_name = type_name.lower()

        if type_name not in FIELD_TYPES:
            await send(itr, "INVALID_FIELD_TYPE", type=type_name.title())
            return

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await send(itr, "TEMPLATE_NOT_FOUND", name=template_name.title())
            return

        default_value: Any = None
        if default:
            try:
                default_value = FIELD_TYPES[type_name].from_str(default)
            except Exception as e:
                await send(
                    itr,
                    "INVALID_DEFAULT_FIELD_VALUE",
                    value=default,
                    type=type_name.title(),
                )

                print(e)
                return

        output_msg: str = ""
        with JSONFileWrapperUpdate(template_path) as template:
            if field_name not in template["fields"]:
                await send(itr, "FIELD_NOT_FOUND", name=field_name.title())
                return

            template["fields"][field_name] = {
                "type": type_name,
                "default": default_value,
            }

            output_msg += out(
                "FIELD_UPDATED",
                old=field_name.title(),
                new=get_template_field_str(
                    template_name,
                    field_name,
                    template["fields"][field_name]["type"],
                    FIELD_TYPES[
                        template["fields"][field_name]["type"]
                    ].to_str(template["fields"][field_name]["default"])
                ),
            )

        sheets_changed: int = 0
        for path in get_all_sheet_paths():
            with JSONFileWrapperUpdate(path) as sheet:
                if sheet["template"] == template_name:
                    sheet["fields"][field_name] = default_value
                    sheets_changed += 1

        if sheets_changed:
            output_msg += out("SHEETS_UPDATED", amount=sheets_changed)

        await botsend(itr, output_msg)

class Sheet(apc.Group):
    @apc.command(description="Creates a sheet from a template.")
    async def add(
        self,
        itr: Interaction,
        sheet_name: str,
        template_name: str
    ) -> None:
        sheet_name = sheet_name.lower()
        template_name = template_name.lower()

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await send(itr, "TEMPLATE_NOT_FOUND", name=template_name.title())
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

            await send(
                itr,
                "SHEET_CREATED",
                name=get_template_sheet_str(template_name, sheet_name),
            )
        except FileExistsError:
            await send(itr, "SHEET_ALREADY_EXISTS", name=sheet_name.title())

    @apc.command(description="Deletes a sheet.")
    async def remove(self, itr: Interaction, names: str) -> None:
        output_msg: str = ""
        for name in [name.lower() for name in get_str_varargs(names)]:
            sheet_path: Path = get_sheet_path(name)

            try:
                sheet_path.unlink()
                output_msg += out("SHEET_REMOVED", name=name.title())
            except FileNotFoundError:
                output_msg += out("SHEET_NOT_FOUND", name=name.title())

        await botsend(itr, output_msg)

    @apc.command(description="Renames a sheet.")
    async def rename(
        self,
        itr: Interaction,
        old_name: str,
        new_name: str
    ) -> None:
        old_name = old_name.lower()
        new_name = new_name.lower()

        old_path: Path = get_sheet_path(old_name)

        if not old_path.exists():
            await send(itr, "SHEET_NOT_FOUND", name=old_name.title())
            return

        new_path: Path = get_sheet_path(new_name)

        if new_path.exists():
            await send(itr, "SHEET_ALREADY_EXISTS", name=new_name.title())
            return

        old_path.rename(new_path)
        await send(
            itr,
            "SHEET_RENAMED",
            old=old_name.title(),
            new=new_name.title()
        )

    @apc.command(
        description=(
            "Lists available sheets (optionally filtering by template)."
        )
    )
    async def list(self, itr: Interaction, template: str = "") -> None:
        template = template.lower()

        if template and not get_template_path(template).exists():
            await send(itr, "TEMPLATE_NOT_FOUND", name=template.title())
            return

        sheet_list: list[str] = []
        for sheet_path in get_all_sheet_paths():
            with JSONFileWrapperReadOnly(sheet_path) as sheet:
                if not template or sheet["template"] == template:
                    sheet_list.append(
                        get_sheet_str(sheet_path.stem, sheet["template"])
                    )

        await botsend(
            itr,
            out(
                "AVAILABLE_SHEETS",
                separator="",
                templates="".join([f"\n- {sheet}" for sheet in sheet_list]),
                finaldot="",
            )
            if sheet_list
            else out("NO_SHEETS_AVAILABLE")
        )

    @apc.command(description="Converts a sheet to text.")
    async def totext(self, itr: Interaction, name: str) -> None:
        name = name.lower()

        sheet_path: Path = get_sheet_path(name)

        if not sheet_path.exists():
            await send(itr, "SHEET_NOT_FOUND", name=name.title())
            return

        output_msg: str = f"```\n{name.upper()}\n"
        with JSONFileWrapperReadOnly(sheet_path) as sheet:
            template_path: Path = get_template_path(sheet["template"])

            if not template_path.exists():
                await send(
                    itr, "TEMPLATE_NOT_FOUND", name=sheet["template"].title()
                )
                return

            with JSONFileWrapperReadOnly(template_path) as template:
                for field in sheet["fields"]:
                    type: str = template["fields"][field]["type"]
                    output_msg += (
                        f"{4 * ' '}{field.title()} ({type.title()}) is "
                        f"{FIELD_TYPES[type].to_str(sheet['fields'][field])}\n"
                    )

        output_msg += "```"

        await botsend(itr, output_msg)

    @apc.command(description="Inspects a sheet field or changes its value.")
    async def field(
        self,
        itr: Interaction,
        sheet_name: str,
        field_name: str,
        value: str = ""
    ) -> None:
        sheet_name = sheet_name.lower()
        field_name = field_name.lower()

        sheet_path: Path = get_sheet_path(sheet_name)

        if not sheet_path.exists():
            await send(itr, "SHEET_NOT_FOUND", name=sheet_name.title())
            return

        if value:
            await _update_field(
                itr, sheet_name, field_name, sheet_path, value
            )
            return

        with JSONFileWrapperReadOnly(sheet_path) as sheet:
            if field_name not in sheet["fields"]:
                await send(itr, "FIELD_NOT_FOUND", name=field_name.title())
                return

            await send(
                itr,
                "FIELD_VALUE",
                field_str=get_sheet_field_str(
                    sheet_name,
                    field_name,
                    sheet["fields"][field_name]
                ),
            )

    @apc.command(description="Performs a method on a sheet field.")
    async def do(
        self,
        itr,
        sheet_name: str,
        field_name: str,
        method_name: str,
        args: str = "",
    ):
        sheet_name = sheet_name.lower()
        field_name = field_name.lower()
        method_name = method_name.lower()

        sheet_path: Path = get_sheet_path(sheet_name)

        if not sheet_path.exists():
            await send(itr, "SHEET_NOT_FOUND", name=sheet_name.title())
            return

        with JSONFileWrapperUpdate(sheet_path) as sheet:
            if field_name not in sheet["fields"]:
                await send(itr, "FIELD_NOT_FOUND", name=field_name.title())
                return

            if sheet["fields"][field_name] is None:
                await send(itr, "NULL_FIELD", name=field_name.title())
                return

            template_path: Path = get_template_path(sheet["template"])

            if not template_path.exists():
                await send(
                    itr, "TEMPLATE_NOT_FOUND", name=sheet["template"].title()
                )
                return

            with JSONFileWrapperReadOnly(template_path) as template:
                method = getattr(
                    FIELD_TYPES[template["fields"][field_name]["type"]],
                    f"method_{method_name}",
                    None,
                )

                if not method:
                    await send(
                        itr, "METHOD_NOT_FOUND", name=method_name.title()
                    )
                    return

                old_value: Any = sheet["fields"][field_name]

                sheet["fields"][field_name] = method(
                    old_value, get_str_varargs(args))

                await send(
                    itr,
                    "FIELD_UPDATED",
                    old=get_sheet_field_str(
                        sheet_name,
                        field_name,
                        FIELD_TYPES[
                            template["fields"][field_name]["type"]
                        ].to_str(old_value)
                    ),
                    new=FIELD_TYPES[
                        template["fields"][field_name]["type"]
                    ].to_str(sheet["fields"][field_name])
                )


async def setup(bot: commands.Bot) -> None:
    charsheets = Charsheets()
    template = Template(parent=charsheets)
    sheet = Sheet(parent=charsheets)

    add_slash_command(bot, charsheets)
    extension_loaded(EXTENSION_NAME)


async def teardown(bot: commands.Bot) -> None:
    remove_slash_command(bot, "charsheets")
    extension_unloaded(EXTENSION_NAME)


# Ensure directory structure's existence
for dir in (base_dir, templates_dir, charsheets_dir):
    dir.mkdir(exist_ok=True)
