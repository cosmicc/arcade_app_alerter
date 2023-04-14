from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    # Read values from text files
    file1_path = './mame.ver'
    file2_path = './launchbox.ver'
    file3_path = './retroarch.ver'
    file4_path = './ledblinky.ver'
    
    with open(file1_path, 'r') as file1:
        file1_contents = file1.readlines()

    with open(file2_path, 'r') as file2:
        file2_contents = file2.readlines()

    with open(file3_path, 'r') as file3:
        file3_contents = file3.readlines()

    with open(file4_path, 'r') as file4:
        file4_contents = file4.readlines()

    # Render the template with the values
    return render_template('index.html', file1_contents=file1_contents, file2_contents=file2_contents, file3_contents=file3_contents, file4_contents=file4_contents,)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

