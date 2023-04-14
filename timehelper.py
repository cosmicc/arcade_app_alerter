from datetime import datetime

def elapsed_time(start_time, append=None):
    """Convert string representation of datetime to elapsed time string representation
    Args:
        start_time (str): Start time in the format 'MM-DD-YYYY HH:MM'
        append (str, [Optional]): String to append to the end of the elapsed time
    Returns:
        str: Elapsed time string representation with a maximum of 2 values, e.g. '1 Hour, 45 Minutes'
    """
    datetime_format = '%m-%d-%Y %H:%M'
    start_time = datetime.strptime(start_time, datetime_format)
    current_time = datetime.now()
    seconds = int((current_time - start_time).total_seconds())
    intervals = (
        ('Year', 31536000),
        ('Month', 2592000),
        ('Week', 604800),
        ('Day', 86400),
        ('Hour', 3600),
        ('Minute', 60),
        ('Second', 1)
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

