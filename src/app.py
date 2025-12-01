import os
from flask import Flask, render_template, request, redirect, url_for, flash
from varasto import Varasto


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-for-development')

# In-memory storage for warehouses
# Each warehouse has a name and a Varasto instance
warehouses = {}


def get_warehouse_id():
    """Generate a unique warehouse ID."""
    if not warehouses:
        return 1
    return max(warehouses.keys()) + 1


def parse_create_form():
    """Parse and validate create warehouse form data."""
    name = request.form.get('name', '').strip()
    capacity = float(request.form.get('capacity', 0))
    initial_balance = float(request.form.get('initial_balance', 0))
    return name, capacity, initial_balance


def validate_warehouse_form(name, capacity):
    """Validate warehouse form data. Returns error message or None."""
    if not name:
        return 'Nimi on pakollinen.'
    if capacity <= 0:
        return 'Tilavuuden on oltava positiivinen.'
    return None


def parse_amount():
    """Parse and validate amount from form."""
    return float(request.form.get('amount', 0))


@app.route('/')
def index():
    """Display all warehouses."""
    return render_template('index.html', warehouses=warehouses)


def store_new_warehouse(name, capacity, initial_balance):
    """Store a new warehouse and return success message."""
    warehouse_id = get_warehouse_id()
    warehouses[warehouse_id] = {
        'name': name,
        'varasto': Varasto(capacity, initial_balance)
    }
    return f'Varasto "{name}" luotu onnistuneesti!'


def handle_create_post():
    """Handle POST request for create warehouse."""
    try:
        name, capacity, initial_balance = parse_create_form()
    except ValueError:
        flash('Virheelliset arvot. Syötä numeroita.', 'error')
        return render_template('create_warehouse.html')

    error = validate_warehouse_form(name, capacity)
    if error:
        flash(error, 'error')
        return render_template('create_warehouse.html')

    msg = store_new_warehouse(name, capacity, initial_balance)
    flash(msg, 'success')
    return redirect(url_for('index'))


@app.route('/warehouse/create', methods=['GET', 'POST'])
def create_warehouse():
    """Create a new warehouse."""
    if request.method == 'POST':
        return handle_create_post()
    return render_template('create_warehouse.html')


@app.route('/warehouse/<int:warehouse_id>')
def view_warehouse(warehouse_id):
    """View a specific warehouse."""
    warehouse = warehouses.get(warehouse_id)
    if not warehouse:
        flash('Varastoa ei löytynyt.', 'error')
        return redirect(url_for('index'))
    return render_template(
        'view_warehouse.html',
        warehouse_id=warehouse_id,
        warehouse=warehouse
    )


def render_edit_template(warehouse_id, warehouse):
    """Render the edit warehouse template."""
    return render_template(
        'edit_warehouse.html',
        warehouse_id=warehouse_id,
        warehouse=warehouse
    )


def update_warehouse(warehouse, name, capacity):
    """Update warehouse with new values."""
    current_balance = warehouse['varasto'].saldo
    warehouse['name'] = name
    warehouse['varasto'] = Varasto(capacity, min(current_balance, capacity))


def parse_edit_form():
    """Parse edit form data."""
    name = request.form.get('name', '').strip()
    capacity = float(request.form.get('capacity', 0))
    return name, capacity


def handle_edit_post(warehouse_id, warehouse):
    """Handle POST request for edit warehouse."""
    try:
        name, capacity = parse_edit_form()
    except ValueError:
        flash('Virheellinen tilavuus.', 'error')
        return render_edit_template(warehouse_id, warehouse)

    error = validate_warehouse_form(name, capacity)
    if error:
        flash(error, 'error')
        return render_edit_template(warehouse_id, warehouse)

    update_warehouse(warehouse, name, capacity)
    flash(f'Varasto "{name}" päivitetty!', 'success')
    return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))


@app.route('/warehouse/<int:warehouse_id>/edit', methods=['GET', 'POST'])
def edit_warehouse(warehouse_id):
    """Edit a warehouse."""
    warehouse = warehouses.get(warehouse_id)
    if not warehouse:
        flash('Varastoa ei löytynyt.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        return handle_edit_post(warehouse_id, warehouse)

    return render_edit_template(warehouse_id, warehouse)


@app.route('/warehouse/<int:warehouse_id>/delete', methods=['POST'])
def delete_warehouse(warehouse_id):
    """Delete a warehouse."""
    warehouse = warehouses.pop(warehouse_id, None)
    if warehouse:
        flash(f'Varasto "{warehouse["name"]}" poistettu.', 'success')
    else:
        flash('Varastoa ei löytynyt.', 'error')
    return redirect(url_for('index'))


def validate_amount(amount):
    """Validate amount is positive."""
    if amount <= 0:
        return 'Määrän on oltava positiivinen.'
    return None


def redirect_to_warehouse(warehouse_id):
    """Redirect to warehouse view."""
    return redirect(url_for('view_warehouse', warehouse_id=warehouse_id))


def get_warehouse_or_redirect(warehouse_id):
    """Get warehouse or redirect to index if not found."""
    warehouse = warehouses.get(warehouse_id)
    if not warehouse:
        flash('Varastoa ei löytynyt.', 'error')
    return warehouse


def process_add(warehouse, amount, warehouse_id):
    """Process adding items to warehouse."""
    available_space = warehouse['varasto'].paljonko_mahtuu()
    if amount > available_space:
        msg = f'Ei tarpeeksi tilaa. Tilaa jäljellä: {available_space:.1f}'
        flash(msg, 'error')
        return redirect_to_warehouse(warehouse_id)

    warehouse['varasto'].lisaa_varastoon(amount)
    flash(f'Lisätty {amount:.1f} varastoon.', 'success')
    return redirect_to_warehouse(warehouse_id)


@app.route('/warehouse/<int:warehouse_id>/add', methods=['POST'])
def add_to_warehouse(warehouse_id):
    """Add items to a warehouse."""
    warehouse = get_warehouse_or_redirect(warehouse_id)
    if not warehouse:
        return redirect(url_for('index'))

    try:
        amount = parse_amount()
    except ValueError:
        flash('Virheellinen määrä.', 'error')
        return redirect_to_warehouse(warehouse_id)

    error = validate_amount(amount)
    if error:
        flash(error, 'error')
        return redirect_to_warehouse(warehouse_id)

    return process_add(warehouse, amount, warehouse_id)


def process_remove(warehouse, amount, warehouse_id):
    """Process removing items from warehouse."""
    current_balance = warehouse['varasto'].saldo
    if amount > current_balance:
        flash(f'Ei tarpeeksi tavaraa. Saldo: {current_balance:.1f}', 'error')
        return redirect_to_warehouse(warehouse_id)

    warehouse['varasto'].ota_varastosta(amount)
    flash(f'Poistettu {amount:.1f} varastosta.', 'success')
    return redirect_to_warehouse(warehouse_id)


@app.route('/warehouse/<int:warehouse_id>/remove', methods=['POST'])
def remove_from_warehouse(warehouse_id):
    """Remove items from a warehouse."""
    warehouse = get_warehouse_or_redirect(warehouse_id)
    if not warehouse:
        return redirect(url_for('index'))

    try:
        amount = parse_amount()
    except ValueError:
        flash('Virheellinen määrä.', 'error')
        return redirect_to_warehouse(warehouse_id)

    error = validate_amount(amount)
    if error:
        flash(error, 'error')
        return redirect_to_warehouse(warehouse_id)

    return process_remove(warehouse, amount, warehouse_id)


if __name__ == '__main__':
    app.run(debug=True)
