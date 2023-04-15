from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

from datetime import datetime, timedelta

def elapsed_time(start_time, withsecs=True, append=None):
    """Convert string representation of datetime to elapsed time string representation
    Args:
        start_time (str): Start time in the format 'MM-DD-YYYY HH:MM'
        withsecs (bool, optional): Whether to include seconds in the elapsed time. Default is True.
        append (str, optional): String to append to the end of the elapsed time. Default is None.
    Returns:
        str: Elapsed time string representation with a maximum of 2 values, e.g. '1 Hour, 45 Minutes'
    """
    if withsecs:
        datetime_format = '%m-%d-%Y %H:%M'
    else:
        datetime_format = '%m-%d-%Y'
    start_time = datetime.strptime(start_time, datetime_format)
    current_time = datetime.now()

    if not withsecs:
        # Check if the date only of start_time is the same as current_time
        if start_time.date() == current_time.date():
            return "Today"
        # Check if the date only of start_time is 1 day behind current_time
        elif start_time.date() == current_time.date() - timedelta(days=1):
            return "Yesterday"

    seconds = int((current_time - start_time).total_seconds())
    intervals = (
        ('Years', 31536000),
        ('Months', 2592000),
        ('Weeks', 604800),
        ('Days', 86400),
        ('Hours', 3600),
        ('Minutes', 60),
        ('Seconds', 1)
    )
    result = []
    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip("s")
            result.append(f"{int(value)} {name}")
            if len(result) == 2:
                break
    if append:
        return ", ".join(result) + f" {append}"
    else:
        return ", ".join(result)

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
        mamever = file1_contents[0]
        mamedate = file1_contents[1]
        mameelapsed = elapsed_time(file1_contents[1].strip(), withsecs=False, append="ago")

    with open(file2_path, 'r') as file2:
        file2_contents = file2.readlines()
        launchboxver = file2_contents[0]
        launchboxdate = file2_contents[1]
        launchboxelapsed = elapsed_time(file2_contents[1].strip(), withsecs=False, append="ago")

    with open(file3_path, 'r') as file3:
        file3_contents = file3.readlines()
        retroarchver = file3_contents[0]
        retroarchdate = file3_contents[1]
        retroarchelapsed = elapsed_time(file3_contents[1].strip(), withsecs=False, append="ago")

    with open(file4_path, 'r') as file4:
        file4_contents = file4.readlines()
        ledblinkyver = file4_contents[0]
        ledblinkydate = file4_contents[1]
        ledblinkyelapsed = elapsed_time(file4_contents[1].strip(), withsecs=False, append="ago")

    with open(file0_path, 'r') as file0:
        file0_contents = file0.readlines()
        lastcheckdate = file0_contents[0]
        lastcheckapp = file0_contents[1]
        lastcheckelapsed = elapsed_time(file0_contents[0].strip(), withsecs=True, append="ago")

    # Render the template with the values
    return render_template('index.html', lastcheckdate=lastcheckdate, lastcheckapp=lastcheckapp, lastcheckelapsed=lastcheckelapsed, mamever=mamever, mamedate=mamedate, mameelapsed=mameelapsed, launchboxver=launchboxver, launchboxdate=launchboxdate, launchboxelapsed=launchboxelapsed, retroarchver=retroarchver, retroarchdate=retroarchdate, retroarchelapsed=retroarchelapsed, ledblinkyver=ledblinkyver, ledblinkydate=ledblinkydate, ledblinkyelapsed=ledblinkyelapsed)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

