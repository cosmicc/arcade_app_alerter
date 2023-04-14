from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    # Read values from text files
    file0_path = './data/lastcheck'
    file1_path = './data/mame.ver'
    file2_path = './data/launchbox.ver'
    file3_path = './data/retroarch.ver'
    file4_path = './data/ledblinky.ver'

    
    with open(file1_path, 'r') as file1:
        file1_contents = file1.readlines()

    with open(file2_path, 'r') as file2:
        file2_contents = file2.readlines()

    with open(file3_path, 'r') as file3:
        file3_contents = file3.readlines()

    with open(file4_path, 'r') as file4:
        file4_contents = file4.readlines()

    with open(file0_path, 'r') as file0:
        file0_contents = file0.readlines()

    # Render the template with the values
    return render_template('index.html', file1_contents=file1_contents, file2_contents=file2_contents, file3_contents=file3_contents, file4_contents=file4_contents, file0_contents=file0_contents)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

