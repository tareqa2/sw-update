from flask import Flask, render_template, request, redirect, url_for, flash
import csv_manager
from compare_versions import compare_versions

app = Flask(__name__)
app.secret_key = 'sw-update-secret-key'


@app.route('/')
def index():
    details = csv_manager.load_installed_details()
    return render_template('index.html', details=details)


@app.route('/update', methods=['GET', 'POST'])
def update():
    installed = csv_manager.load_installed_versions()

    if request.method == 'POST':
        desired = {}
        for component in installed:
            val = request.form.get(component, '').strip()
            desired[component] = val if val else installed[component]

        actions = compare_versions(installed, desired)

        if 'confirm' in request.form:
            previous = installed.copy()
            for key, action in actions.items():
                if action in ('upgrade', 'downgrade'):
                    csv_manager.append_update_history(key, installed[key], desired[key], action)
                    installed[key] = desired[key]
                else:
                    csv_manager.append_update_history(key, installed[key], installed[key], action)
            csv_manager.save_versions(installed, is_initial=False, previous_versions=previous)
            flash('Updates applied successfully!', 'success')
            return redirect(url_for('index'))

        return render_template('update.html', installed=installed, desired=desired, actions=actions, confirm=True)

    return render_template('update.html', installed=installed, desired={}, actions={}, confirm=False)


@app.route('/history')
def history():
    records = csv_manager.get_version_history()
    return render_template('history.html', records=records)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
