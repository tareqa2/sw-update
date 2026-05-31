from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import csv_manager
from compare_versions import compare_versions
import time

app = Flask(__name__)
app.secret_key = 'sw-update-secret-key'

DEVICES = csv_manager.DEVICES

@app.route('/')
def index():
    device = request.args.get('device', 'lab1')
    details = csv_manager.load_installed_details(device)
    return render_template('index.html', details=details, device=device, devices=DEVICES)

@app.route('/update', methods=['GET', 'POST'])
def update():
    device = request.args.get('device', request.form.get('device', 'lab1'))
    installed = csv_manager.load_installed_versions(device)

    if request.method == 'POST':
        branch     = request.form.get('branch', 'manual')
        commit_id  = request.form.get('commit_id', '').strip()
        desired    = {}

        for component in installed:
            val = request.form.get(component, '').strip()
            desired[component] = val if val else installed[component]

        actions = compare_versions(installed, desired)

        if 'confirm' in request.form:
            previous = installed.copy()
            for key, action in actions.items():
                new_ver = desired[key]
                csv_manager.append_update_history(device, key, installed[key], new_ver, action, branch, commit_id)
                if action in ('upgrade', 'downgrade'):
                    installed[key] = new_ver
            csv_manager.save_versions(device, installed, is_initial=False, previous_versions=previous)
            flash(f'Updates applied to {device} successfully!', 'success')
            return redirect(url_for('index', device=device))

        return render_template('update.html',
            installed=installed, desired=desired, actions=actions,
            confirm=True, device=device, devices=DEVICES,
            branch=branch, commit_id=commit_id)

    return render_template('update.html',
        installed=installed, desired={}, actions={},
        confirm=False, device=device, devices=DEVICES,
        branch='manual', commit_id='')

@app.route('/history')
def history():
    device = request.args.get('device', 'lab1')
    records = csv_manager.get_version_history(device)
    return render_template('history.html', records=records, device=device, devices=DEVICES)

@app.route('/progress')
def progress():
    """Simulate progress for the update animation"""
    def generate():
        for i in range(0, 101, 10):
            yield f"data: {i}\n\n"
            time.sleep(0.3)
    from flask import Response
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)
