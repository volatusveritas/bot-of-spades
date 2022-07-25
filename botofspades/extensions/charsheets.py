from pathlib import Path
from json import dump, load
from typing import Any, Type
import os.path as path

from discord.ext import commands

from botofspades.log import extension_loaded, extension_unloaded


TEMPLATE_EXTENSION: str = "cstemplate"
CHARSHEET_EXTENSION: str = "cscharsheet"


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


class JSONFileWrapper:
    def __init__(self, path: Path) -> None:
        self._path: Path = path
        self._dict: dict = {"fields":{}}

    def __enter__(self):
        if not self._path.exists():
            raise FileNotFoundError(self._path.name)

        if path.getsize(self._path):
            with self._path.open('r') as file:
                self._dict = load(file)

        return self._dict

    def __exit__(self, exc_type, exc_value, trace) -> bool:
        with self._path.open('w') as file:
            dump(self._dict, file, indent=2)

        return False


class Charsheets(commands.Cog):
    base_dir: Path = Path.cwd() / "charsheets"
    templates_dir: Path = base_dir / "templates"
    charsheets_dir: Path = base_dir / "sheets"

    def __init__(self) -> None:
        for dir in (self.base_dir, self.templates_dir, self.charsheets_dir):
            dir.mkdir(exist_ok=True)

    @classmethod
    def get_template_path(cls, name: str) -> Path:
        return cls.templates_dir / f"{name}.{TEMPLATE_EXTENSION}"

    @classmethod
    def get_field_string(cls, name: str, value: dict) -> str:
        return (
            f"**{name.title()}** ({value['type'].title()})"
            + (f" [default is {value['default']}]") if value["default"] else ""
        )

    @classmethod
    async def reply_no_subcommand(cls, ctx) -> None:
        await ctx.message.reply(
            "No valid subcommand provided. Available subcommands: "
            + (", ".join(
                [f"`{command.name}`" for command in ctx.command.commands]
            ))
            + "."
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
        await self.reply_no_subcommand(ctx)

    @charsheets.group(invoke_without_command=True, aliases=("tp",))
    async def template(self, ctx) -> None:
        await self.reply_no_subcommand(ctx)

    @template.command(name="add", usage="charsheets template add <name>")
    async def template_add(self, ctx, name: str) -> None:
        name = name.lower()

        template_path: Path = self.get_template_path(name)

        try:
            template_path.touch()
            await ctx.message.reply(
                f"Template `{name}` successfully created."
            )
        except FileExistsError:
            await ctx.message.reply("This template already exists.")

    @template.command(
        name="remove", aliases=("rm",),
        usage="charsheets template remove <name>*"
    )
    async def template_remove(self, ctx, *names: str) -> None:
        output_msg: str = ""
        for name in [name.lower() for name in names]:
            template_path: Path = self.get_template_path(name)

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

        template_path: Path = self.get_template_path(old_name)
        target_path: Path = self.get_template_path(new_name)

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
            template_path.stem for template_path in
            self.templates_dir.glob(f"*.{TEMPLATE_EXTENSION}")
        ]

        if template_names:
            await ctx.message.reply(
                f"Available templates: {', '.join(template_names)}."
            )
        else:
            await ctx.message.reply("No templates available.")

    @template.group(name="field", invoke_without_command=True, aliases=("fd",))
    async def template_field(self, ctx) -> None:
        await self.reply_no_subcommand(ctx)

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

        template_path: Path = self.get_template_path(template_name)

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

        with JSONFileWrapper(template_path) as template:
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
            f"Field `{field_name} ({type})` successfully added to"
            f" template `{template_name}`."
        )

    @template_field.command(
        name="remove", aliases=("rm",),
        usage="charsheets template field remove <field>*"
    )
    async def template_field_remove(
        self, ctx, template_name: str, *field_names: str
    ) -> None:
        template_name = template_name.lower()

        template_path: Path = self.get_template_path(template_name)

        if not template_path.exists():
            await ctx.message.reply(f"Template `{template_name}` not found.")
            return

        output_msg: str = ""
        with JSONFileWrapper(template_path) as template:
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

        template_path: Path = self.get_template_path(template_name)

        if not template_path.exists():
            await ctx.message.reply(f"Template `{template_name}` not found.")
            return

        with JSONFileWrapper(template_path) as template:
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

        template_path: Path = self.get_template_path(template_name)

        if not template_path.exists():
            await ctx.message.reply(f"Template `{template_name}` not found.")
            return

        output_msg: str = ""
        with JSONFileWrapper(template_path) as template:
            for name, value in template["fields"].items():
                if type != "any" and value["type"] != type:
                    continue

                output_msg += f"- {self.get_field_string(name, value)}\n"

        await ctx.message.reply(
            f"Fields in `{template_name}`:\n"
            + output_msg if output_msg else "No fields found."
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

        template_path: Path = self.get_template_path(template_name)

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

        with JSONFileWrapper(template_path) as template:
            if field_name not in template["fields"]:
                await ctx.message.reply(f"Field `{field_name}` not found.")
                return

            template["fields"][field_name] = {
                "type": type,
                "default": default_value
            }

            await ctx.message.reply(
                f"Field updated to "
                + self.get_field_string(
                    field_name, template['fields'][field_name]
                )
            )


    @charsheets.group(invoke_without_command=True, aliases=("sh",))
    async def sheet(self, ctx) -> None:
        await self.reply_no_subcommand(ctx)

    @sheet.command(name="add")
    async def sheet_add(self, ctx) -> None:
        pass

    @sheet.command(name="remove", aliases=("rm",))
    async def sheet_remove(self, ctx) -> None:
        pass

    @sheet.command(name="rename", aliases=("rn",))
    async def sheet_rename(self, ctx) -> None:
        pass

    @sheet.command(name="list", aliases=("ls",))
    async def sheet_list(self, ctx) -> None:
        pass

    @sheet.command(name="totext", aliases=("txt",))
    async def sheet_totext(self, ctx) -> None:
        pass

    @sheet.command(name="field", aliases=("fd",))
    async def sheet_field(self, ctx) -> None:
        pass


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Charsheets())
    extension_loaded("Charsheets")


def teardown(bot: commands.Bot) -> None:
    bot.remove_cog("Charsheets")
    extension_unloaded("Charsheets")
