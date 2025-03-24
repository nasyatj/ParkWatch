from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('dashboard.html')


@app.route('/submit_report', methods=['POST'])
def submit_report():
    park = request.form.get('park')
    report_type = request.form.get('report_type')
    details = request.form.get('details')

    # Here, you can process the report (e.g., save to a database, log it, etc.)
    print(f"Report submitted: {park}, {report_type}, {details}")

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
