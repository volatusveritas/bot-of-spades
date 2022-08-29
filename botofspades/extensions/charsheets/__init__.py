from pathlib import Path
from typing import Any

from discord.ext import commands

from botofspades.outmsg import out, botsend, send
from botofspades.log import extension_loaded, extension_unloaded
from botofspades.jsonwrappers import *
from botofspades.extensions.charsheets.types import *
from botofspades import unicode


EXTENSION_NAME: str = "Charsheets"

base_dir: Path = Path.cwd() / "charsheets"
templates_dir: Path = base_dir / "templates"
charsheets_dir: Path = base_dir / "sheets"


FIELD_TYPES: dict[str, type[Field]] = {
    "abacus": Abacus,
    "rational": Rational,
    "lever": Lever,
    "scroll": Scroll,
    "gauge": Gauge,
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


def get_field_str(name: str, value: dict) -> str:
    return f"{name.title()} ({value['type'].title()})" + (
        f" [{value['default']}]" if value["default"] else ""
    )


def get_full_field_str(sheet: str, field: str, type: str, value: Any) -> str:
    return f"{sheet.title()} :: {field.title()} ({type.title()}) = {value}"


def get_sheet_field_str(sheet: str, field: str, value: dict) -> str:
    return f"{sheet.title()} :: " + get_field_str(field, value)


def get_sheet_str(name: str, template: str) -> str:
    return f"**{name.title()}** (from **{template.title()}**)"


class Charsheets(commands.Cog):
    @classmethod
    async def _reply_no_subcommand(cls, ctx) -> None:
        subcommands: str = ", ".join(
            [f"**{command.name}**" for command in ctx.command.commands]
        )

        await send(ctx, "NO_SUBCOMMAND", subcommands=subcommands)

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
                await send(
                    ctx, "TEMPLATE_NOT_FOUND", name=sheet["template"].title()
                )
                return

            with JSONFileWrapperReadOnly(template_path) as template:
                type_name: str = template["fields"][field_name]["type"]

                try:
                    new_value: Any = FIELD_TYPES[type_name].from_str(value)
                    sheet["fields"][field_name] = new_value

                    await send(
                        ctx,
                        "FIELD_VALUE_SET",
                        field=get_sheet_field_str(
                            sheet_name,
                            field_name,
                            template["fields"][field_name],
                        ),
                        value=sheet["fields"][field_name],
                    )
                except:
                    await send(
                        ctx,
                        "INVALID_FIELD_VALUE",
                        value=value,
                        type=type_name.title(),
                    )

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx, error: commands.CommandError
    ) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await send(
                ctx,
                "MISSING_ARGUMENT",
                param=error.param,
                usage=ctx.command.usage,
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
            template_path.touch(exist_ok=False)

            with JSONFileWrapperUpdate(template_path) as template:
                template["fields"] = {}

            await send(ctx, "TEMPLATE_CREATED", name=name.title())
        except FileExistsError:
            await send(ctx, "TEMPLATE_ALREADY_EXISTS", name=name.title())

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

        await botsend(ctx, output_msg)

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
            await send(ctx, "TEMPLATE_NOT_FOUND", name=old_name.title())
            return

        if target_path.exists():
            await send(ctx, "TEMPLATE_ALREADY_EXISTS", name=new_name.title())
            return

        template_path.rename(target_path)

        sheets_changed: int = 0
        for path in get_all_sheet_paths():
            with JSONFileWrapperUpdate(path) as sheet:
                if sheet["template"] == old_name:
                    sheet["template"] = new_name
                    sheets_changed += 1

        output_msg: str = out(
            "TEMPLATE_RENAMED", old=old_name, new=new_name
        ) + (
            out("SHEETS_UPDATED", amount=sheets_changed)
            if sheets_changed
            else ""
        )

        await botsend(ctx, output_msg)

    @template.command(
        name="list", aliases=("ls",), usage="charsheets template list"
    )
    async def template_list(self, ctx) -> None:
        template_names: list[str] = [
            template_path.stem.title()
            for template_path in get_all_template_paths()
        ]

        await botsend(
            ctx,
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
        type_name: str,
        default: str = "",
    ) -> None:
        template_name = template_name.lower()
        field_name = field_name.lower()
        type_name = type_name.lower()

        if type_name not in FIELD_TYPES:
            await send(ctx, "INVALID_FIELD_TYPE", type=type_name.title())
            return

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await send(ctx, "TEMPLATE_NOT_FOUND", name=template_name.title())
            return

        default_value: Any = None

        if default:
            if not FIELD_TYPES[type_name].validate(default):
                await send(
                    ctx,
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
                    ctx, "FIELD_ALREADY_EXISTS", name=field_name.title()
                )
                return

            template["fields"][field_name] = {
                "type": type_name,
                "default": default_value,
            }

            output_msg += out(
                "FIELD_ADDED",
                field=get_field_str(
                    field_name, template["fields"][field_name]
                ),
                template=template_name.title(),
            )

        sheets_changed: int = 0
        for path in get_all_sheet_paths():
            await botsend(ctx, "Here it does get.")
            with JSONFileWrapperUpdate(path) as sheet:
                if sheet["template"] == template_name:
                    sheet["fields"][field_name] = default_value
                    sheets_changed += 1

        if sheets_changed:
            output_msg += out("SHEETS_UPDATED", amount=sheets_changed)

        await botsend(ctx, output_msg)

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
            await send(ctx, "TEMPLATE_NOT_FOUND", name=template_name.title())
            return

        field_list: list[str] = [name.lower() for name in field_names]

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
                    field=get_field_str(
                        field_name, template["fields"][field_name]
                    ),
                    template=template_name,
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

        await botsend(ctx, output_msg)

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
            await send(ctx, "TEMPLATE_NOT_FOUND", name=template_name.title())
            return

        output_msg: str = ""
        with JSONFileWrapperUpdate(template_path) as template:
            if not old_name in template["fields"]:
                await send(ctx, "FIELD_NOT_FOUND", name=old_name.title())
                return

            if new_name in template["fields"]:
                await send(ctx, "FIELD_ALREADY_EXISTS", name=new_name.title())
                return

            field: dict = template["fields"][old_name]
            del template["fields"][old_name]
            template[new_name] = field

            output_msg += out(
                "FIELD_RENAMED",
                field=get_field_str(old_name, field),
                new=new_name,
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

        await botsend(ctx, output_msg)

    @template_field.command(
        name="list",
        aliases=("ls",),
        usage="charsheets template field list [type]",
    )
    async def template_field_list(
        self, ctx, template_name: str, type_name: str = "any"
    ) -> None:
        template_name = template_name.lower()
        type_name = type_name.lower()

        if type_name != "any" and type_name not in FIELD_TYPES:
            await ctx.message.reply(f"Invalid type **{type_name}**.")
            return

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await send(ctx, "TEMPLATE_NOT_FOUND", name=template_name.title())
            return

        listed_fields: str = "\n"
        with JSONFileWrapperReadOnly(template_path) as template:
            for name, value in template["fields"].items():
                if type_name != "any" and value["type"] != type_name:
                    continue

                listed_fields += (
                    f"\n{unicode.FIELD_ARROW} {get_field_str(name, value)}"
                )

        await botsend(
            ctx,
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
        type_name: str,
        default: str = "",
    ) -> None:
        template_name = template_name.lower()
        field_name = field_name.lower()
        type_name = type_name.lower()

        if type_name not in FIELD_TYPES:
            await send(ctx, "INVALID_FIELD_TYPE", type=type_name.title())
            return

        template_path: Path = get_template_path(template_name)

        if not template_path.exists():
            await send(ctx, "TEMPLATE_NOT_FOUND", name=template_name.title())
            return

        default_value: Any = None
        if default:
            try:
                default_value = FIELD_TYPES[type_name].from_str(default)
            except Exception as e:
                await send(
                    ctx,
                    "INVALID_DEFAULT_FIELD_VALUE",
                    value=default,
                    type=type_name.title(),
                )

                print(e)
                return

        output_msg: str = ""
        with JSONFileWrapperUpdate(template_path) as template:
            if field_name not in template["fields"]:
                await send(ctx, "FIELD_NOT_FOUND", name=field_name.title())
                return

            template["fields"][field_name] = {
                "type": type_name,
                "default": default_value,
            }

            output_msg += out(
                "FIELD_UPDATED",
                field=field_name,
                new=get_field_str(field_name, template["fields"][field_name]),
            )

        sheets_changed: int = 0
        for path in get_all_sheet_paths():
            with JSONFileWrapperUpdate(path) as sheet:
                if sheet["template"] == template_name:
                    sheet["fields"][field_name] = default_value
                    sheets_changed += 1

        if sheets_changed:
            output_msg += out("SHEETS_UPDATED", amount=sheets_changed)

        await botsend(ctx, output_msg)

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
            await send(ctx, "TEMPLATE_NOT_FOUND", name=template_name.title())
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
                ctx,
                "SHEET_CREATED",
                name=get_template_sheet_str(template_name, sheet_name),
            )
        except FileExistsError:
            await send(ctx, "SHEET_ALREADY_EXISTS", name=sheet_name.title())

    @sheet.command(
        name="remove", aliases=("rm",), usage="charsheets sheet remove <name>*"
    )
    async def sheet_remove(self, ctx, *names: str) -> None:
        output_msg: str = ""
        for name in [name.lower() for name in names]:
            sheet_path: Path = get_sheet_path(name)

            try:
                sheet_path.unlink()
                output_msg += out("SHEET_REMOVED", name=name.title())
            except FileNotFoundError:
                output_msg += out("SHEET_NOT_FOUND", name=name.title())

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
            await send(ctx, "SHEET_NOT_FOUND", name=old_name.title())
            return

        new_path: Path = get_sheet_path(new_name)

        if new_path.exists():
            await send(ctx, "SHEET_ALREADY_EXISTS", name=new_name.title())
            return

        old_path.rename(new_path)
        await send(ctx, "SHEET_RENAMED", old=old_name, new=new_name)

    @sheet.command(
        name="list", aliases=("ls",), usage="charsheets sheet list [template]"
    )
    async def sheet_list(self, ctx, template: str = "") -> None:
        template = template.lower()

        if template and not get_template_path(template).exists():
            await send(ctx, "TEMPLATE_NOT_FOUND", name=template.title())
            return

        sheet_list: list[str] = []
        for sheet_path in get_all_sheet_paths():
            with JSONFileWrapperReadOnly(sheet_path) as sheet:
                if not template or sheet["template"] == template:
                    sheet_list.append(
                        get_sheet_str(sheet_path.stem, sheet["template"])
                    )

        await botsend(
            ctx,
            out(
                "AVAILABLE_SHEETS",
                separator="",
                templates="".join([f"\n- {sheet}" for sheet in sheet_list]),
                finaldot="",
            )
            if sheet_list
            else out("NO_SHEETS_AVAILABLE")
        )

    @sheet.command(
        name="totext", aliases=("txt",), usage="charsheets sheet totext <name>"
    )
    async def sheet_totext(self, ctx, name: str) -> None:
        name = name.lower()

        sheet_path: Path = get_sheet_path(name)

        if not sheet_path.exists():
            await send(ctx, "SHEET_NOT_FOUND", name=name.title())
            return

        output_msg: str = f"```\n{name.upper()}\n"
        with JSONFileWrapperReadOnly(sheet_path) as sheet:
            template_path: Path = get_template_path(sheet["template"])

            if not template_path.exists():
                await send(
                    ctx, "TEMPLATE_NOT_FOUND", name=sheet["template"].title()
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
            await send(ctx, "SHEET_NOT_FOUND", name=sheet_name.title())
            return

        if value:
            await self._update_field(
                ctx, sheet_name, field_name, sheet_path, value
            )
            return

        with JSONFileWrapperReadOnly(sheet_path) as sheet:
            if field_name not in sheet["fields"]:
                await send(ctx, "FIELD_NOT_FOUND", name=field_name.title())
                return

            template_path: Path = get_template_path(sheet["template"])

            if not template_path.exists():
                await send(
                    ctx,
                    "INVALID_FIELD_TEMPLATE",
                    template=sheet["template"],
                    field=get_sheet_field_str(
                        sheet_name, field_name, sheet["fields"][field_name]
                    ),
                )
                return

            with JSONFileWrapperReadOnly(template_path) as template:
                await send(
                    ctx,
                    "FIELD_VALUE",
                    field_str=get_full_field_str(
                        sheet_name,
                        field_name,
                        template["fields"][field_name]["type"],
                        sheet["fields"][field_name],
                    ),
                )

    @sheet.command(
        name="do", usage="charsheets sheet do <sheet> <field> <method> <arg>*"
    )
    async def sheet_do(
        self,
        ctx,
        sheet_name: str,
        field_name: str,
        method_name: str,
        *args: str,
    ):
        sheet_name = sheet_name.lower()
        field_name = field_name.lower()
        method_name = method_name.lower()

        sheet_path: Path = get_sheet_path(sheet_name)

        if not sheet_path.exists():
            await send(ctx, "SHEET_NOT_FOUND", name=sheet_name.title())
            return

        with JSONFileWrapperUpdate(sheet_path) as sheet:
            if field_name not in sheet["fields"]:
                await send(ctx, "FIELD_NOT_FOUND", name=field_name.title())
                return

            if sheet["fields"][field_name] is None:
                await send(ctx, "NULL_FIELD", name=field_name.title())
                return

            template_path: Path = get_template_path(sheet["template"])

            if not template_path.exists():
                await send(
                    ctx, "TEMPLATE_NOT_FOUND", name=sheet["template"].title()
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
                        ctx, "METHOD_NOT_FOUND", name=method_name.title()
                    )
                    return

                old_value: Any = sheet["fields"][field_name]

                sheet["fields"][field_name] = method(old_value, args)

                await send(
                    ctx,
                    "FIELD_UPDATED",
                    old=get_sheet_field_str(
                        sheet_name, field_name, template["fields"][field_name]
                    ),
                    new=sheet["fields"][field_name],
                )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Charsheets())
    extension_loaded(EXTENSION_NAME)


async def teardown(bot: commands.Bot) -> None:
    await bot.remove_cog("Charsheets")
    extension_unloaded(EXTENSION_NAME)


# Ensure directory structure's existence
for dir in (base_dir, templates_dir, charsheets_dir):
    dir.mkdir(exist_ok=True)
