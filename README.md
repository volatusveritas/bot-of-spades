<h1 align="center">Bot of Spades</h1>
<p align="center">A bot for all things TTRPG!</p>

## Modules

Bot of Spades consists of many **modules**. Below is a list of the currently
available modules and a description of their purpose. You can see further
details for them in the subtopics below the list or by click a module's title
in the list.

- [**botcontrol**](#bot-control): commands and utilities to control the bot
  itself. Commands to reload, activate, and deactivate modules, change the
  bot's global settings, or stop the bot's execution live here.
- [**intotheodd**](#into-the-odd): commands and utilities for the [Into the
  Odd](https://freeleaguepublishing.com/en/store/?product_id=7749919539458) RPG
  system live here.
- [**charsheets**](#charsheets): commands and utilities for creating,
  inspecting, manipulating and deleting character sheets and character sheet
  templates live here. That's one of the bot's greatest features so far!

Next, details about the commands available for each module are provided. Refer
to the [**command idiom**](#command-idiom) to understand the command
documentation syntax and avoid confusion.

### Bot Control

Commands and utilities to control the bot itself.

- `reload`: reloads all extensions (including this one).

### Into the Odd

Commands and utilities for the [Into the
Odd](https://freeleaguepublishing.com/en/store/?product_id=7749919539458) RPG
system.

- `roll`: performs a standard roll and displays the result.

- `rollattributes`: rolls the initial attribute values for a new character.

### Charsheets

Commands and utilities for creating, inspecting, manipulating and deleting
character sheets and character sheet templates.

- `charsheets template add <name>`: creates a new template called **name**.

- `charsheets template list`: lists the templates available.

- `charsheets template rename <old_name> <new_name>`: renames a template from
  **old_name** to **new_name**.

- `charsheets template remove <name>*`: removes each template **name**.

- `charsheets template field add <template_name> <field_name> <type>
  [default]`: creates a new field in template **template_name** called
  **field_name** with type **type** and default value **default** if provided.

- `charsheets template field edit <template_name> <field_name> <type>
  [default]`: modifies a field in template **template_name** called
  **field_name** to have type **type** and default value **default** if
  provided.

- `charsheets template field list <template_name> [type]`: lists the fields in
  template **template_name**. If **type** is provided, only shows fields with
  type **type**.

- `charsheets template field remove <template_name> <field_name>*`: deletes
  each field **field_name** from template **template_name**.

- `charsheets template field rename <template_name> <old_name> <new_name>`:
  renames a field in template **template_name** from **old_name** to
  **new_name**.

- `charsheets sheet add <sheet_name> <template_name>`: creates a new sheet from
  template **template_name** called **sheet_name**.

- `charsheets sheet field <sheet_name> <field_name> [value]`: inspects the
  value of field **field_name** from sheet **sheet_name**. If **value** is
  provided, sets the value of the field to that.

- `charsheets sheet list [template]`: lists sheets. If **template** is
  provided, only shows sheets created from template **template**.

- `charsheets sheet remove <name>*`: removes each sheet **name**.

- `charsheets sheet rename <old_name> <new_name>`: renames a sheet from
  **old_name** to **new_name**.

- `charsheets sheet totext <name>`: provides a formatted textual version of
  sheet **name**.

## Examples

### Creating a template

Creates a template called `bananakorn`:
```
charsheets template add bananakorn
```

Creates a field called `peels` in template `bananakorn` of type `Abacus` and a
default value of `7`.
```
charsheets template field add bananakorn peels Abacus 7
```

Creates a character sheet called `Carlsen` from template `bananakorn`.
```
charsheets sheet add Carlsen bananakorn
```

Inspects the value of `peels` in sheet `Carlsen`.
```
charsheets sheet field Carlsen peels
```

Sets the value of `peels` in sheet `Carlsen` to 12.
```
charsheets sheet field Carlsen peels 12
```

Provides a formatted textual version of sheet `Carlsen`.
```
charsheets sheet totext Carlsen
```

## Command Idiom

Command usage is documented using the command idiom specified below.

- `word`: indicates one is to literally type **word**.
- `<parameter>`: indicates one is to provide an argument for parameter
  **parameter**.
- `[optional]`: indicates that providing an argument for parameter **optional**
  is optional.
- `<parameter>*` or `[optional]*`: indicates that multiple arguments can be
  provided for parameter **parameter** or optionally for parameter
  **optional**.

Note: all parameters are case insensitive, with the exception of those that
expect specific strings. Therefore, creating a template "bogus" and creating a
template "Bogus" are effectively the same.

## JSON Specifications

Both templates and sheets (from the [charsheets](#charsheets) module) are saved
as JSON files. This section specifies these files' structures.

### Template Structure

```json
{
    "fields": {
        "name*": {
            "type": "type_name",
            "default": null
        }
    }
}
```

#### Explanation

A template starts with the root object `{}`; contains:

- `fields`: an object; stores the template's fields; contains:
    - `name*`: an object; the key is the field's name; contains:
        - `type`: a string; specifies the field's type, tipically entirely
          lowercase;
        - `default`: any type (including `null`); specifies the field's
          default value;

Note: `name*` indicates there can be any amount of this object inside the
containing object (including zero).

### Sheet Structure

```json
{
    "template": "template_name",
    "fields": {
        "name*": "value"
    }
}
```

#### Explanation

A sheet starts with the root object `{}`; contains:

- `template`: a string; specifies the template from which this sheet comes
  from;
- `fields`: an object; stores the sheet's fields; contains:
    - `name*`: any type (including `null`); the key is the field's name;
      specifies the field's value (starts at the template's `default`);

Note: `name*` indicates there can be any amount of this object inside the
containing object (including zero).
