# `imperial-painter`

A way of generating prototype cards for testing tabletop games!

Creates printable HTML pages using Django and a bit of CSS.

Named for the Magic deck, [Imperial Painter](http://www.mtgtop8.com/event?e=6724&d=238610).

## Running the test app

The test app is a basic Django app that allows you to see `imperial-painter` in action. To install it, use the same steps you would for a normal Django project:

* Create a Python 3 virtual environment [using the instructions here](https://docs.python.org/3/library/venv.html).
* Activate it with `source bin/activate`.
* Install requirements using `pip install -r requirements.txt`.
* Ensure Postgres is running ([instructions are here](https://www.postgresql.org/) if you need to set it up).
* Create a database in `psql` with `create database painter;`.
* Run migrations with `python manage.py migrate`.

Once it's set up, you can run it using `make paint` or `python manage.py runserver`.

Go to `127.0.0.1:8000` in your browser, and you should see some very rudimentary cards! Hit Print in your browser to turn them into real-life prototypes.

## Using Painter yourself

There are several components to Painter's API. Broadly, you need to:

* Create one or more Excel files (`.xlsx`) that contain your card data. This should follow a specific format expected by the importer.
* Add `painter` to your Django app's `INSTALLED_APPS`.
* Set the `IP_IMPORTER` and `IP_DATA_FILES` settings in your `settings.py`.
* Add `painter.urls` to a URLconf somewhere in your project.
* Add one or more [Less files](http://lesscss.org/) (normal CSS files with a .less extension are also valid) to a static folder. Painter expects an entry point file under `styles/custom.less`; this should import any other Less files you've written.
* Add one or more Django templates under `templates/custom`.

The `test_app` is a small example of all of these steps - poking through that should help my explanations make sense.

### Excel API

This varies based on the importer. The base `import_cards` expects a single table, filling an entire sheet, with the following columns:

* `Name` - the name of a card. Uniqueness of names is not enforced.
* `Template` - the name of a Django template file, without the `.html` or the file path leading up to it. For instance, a `Template` entry of `base` would resolve to `templates/custom/base.html`.
    * You can include multiple template names this way, comma-separated - e.g. `character,items`.
    * Any whitespace around template names is removed.
* `Quantity` - optional. This allows you to print a card multiple times.
* Any other columns you wish. These will be converted into variables (see the "Django template API" section).
    * The first blank column header will be taken as the end of the sheet, so your table must be contiguous.
    * Any column name preceded by an asterisk (`*`) will be treated as a _list_ variable. List entries are separated by newlines (Alt+Enter in Excel, and I think Ctrl+Enter in LibreOffice).

Multiple files can be input, and each file can have any number of sheets.

As an example, see [Test Cards.xlsx](https://github.com/adam-thomas/imperial-painter/blob/master/Test%20Cards.xlsx).

### Django settings API

Imperial Painter needs two variables to be set in your Django settings:

* `IP_DATA_FILES` - a list of absolute paths to `.xlsx` files to import.
* `IP_IMPORTER` - an import path to a management command that will load the `.xlsx` files in question.

The example from `test_app` is:

```python
IP_DATA_FILES = [
    os.path.join(BASE_DIR, 'Test Cards.xlsx'),
    os.path.join(BASE_DIR, 'Test Cards.xlsx'),
]
IP_IMPORTER = 'painter.management.commands.import_cards'
```

### Less/CSS API

Add a `styles/custom.less` file to a static files directory.

The contents of each card are wrapped in a `<div class="full-card">`. All of your styles should be applied within that class.

Less allows you to import other Less files, so you can split your styles across multiple files if you need despite the singular entry point. If you're unfamiliar with Less, raw CSS is perfectly valid Less, so you can use that too (just make sure it has the `.less` file extension).

### Django template API

Your templates should contain only the contents of each card. This will be `{% include %}`d into the page template, directly within the `<div class="full-card">` from the previous section.

Within the template, the parameters on each card are available as Django template variables:

* Name: `{{ name }}`
* Template: Unavailable
* Quantity: Unavailable
* Other columns: `{{ c.column_name }}`

Column headings are converted to variable names as follows:

* The name is converted to lowercase.
* Spaces are replaced with underscores.
* Characters other than alphanumerics and underscores are stripped out.

This makes a column called `Rules Text (Full)` into `rules_text_full`, which is then available in the template as `{{ c.rules_text_full }}`.
