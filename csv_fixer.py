import pandas as pd
from datetime import date, timedelta

csv_file_names = ["coldshower", "gratitude", "journal", "makebed",
                  "meditation", "personal", "reading", "alarm", "sunriser", "workout"]

def fix_csvs():
    for file_name in csv_file_names:
        fix_file(file_name)

def fix_file(file_name):
    record = pd.read_csv(f"cogs/Habits Record/{file_name}.csv")
    changed = False
    # start from the newest dates, go backwards, and if a date is missing, then add it and give everyone disciplines for that day
    for i in range(2, record.shape[1]-1):
        current_col = record.columns[i]
        try:
            current_col_as_date = date.fromisoformat(current_col)
            next_col_as_date = date.fromisoformat(record.columns[i+1])
            if next_col_as_date != current_col_as_date + timedelta(1):
                print('uh oh batman!:')
                print(file_name, current_col, next_col_as_date)
                missing_date = current_col_as_date + timedelta(1)
                print('missing date', missing_date)
                record.insert(i+1, str(missing_date), [1]*(record.shape[0]))
                changed = True
                # print(record[record.columns[i+1]])
            # print(file_name, current_col_as_date)
        except:
            print('oh shit')
            print(file_name)
            print(current_col)
    print("Now double checking !!")
    for i in range(2, record.shape[1]-1):
        current_col = record.columns[i]
        try:
            current_col_as_date = date.fromisoformat(current_col)
            next_col_as_date = date.fromisoformat(record.columns[i+1])
            if next_col_as_date != current_col_as_date + timedelta(1):
                print('ruh roh batman!:')
                print(file_name, current_col, next_col_as_date)
                missing_date = current_col_as_date + timedelta(1)
                print('missing date', missing_date)
                # record.insert(i+1, str(missing_date), [1]*(record.shape[0]))

            # print(file_name, current_col_as_date)
        except:
            print('oopsie poopsie')
            print(file_name)
            print(current_col)
            print(type(record.columns[i+1]))
    if changed is True:
        print("good job king, you fixed", file_name)
        record.to_csv(f"cogs/Habits Record/{file_name}.csv", index= False)
        print("saved")
        fix_file(file_name)