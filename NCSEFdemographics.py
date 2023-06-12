import pandas as pd
pd.set_option('display.max_columns', 500)

def getfile(filename):
    df = pd.read_excel(filename)
    print(df.columns)
    print(df.shape)
    df.loc[df["IN PERSON"] == True, "IN PERSON"] = 'in-person'
    df.loc[df["IN PERSON"] == False, "IN PERSON"] = 'virtual'

    for attr in ['GENDER', 'RACE', 'IN PERSON', 'DIVISION', 'COUNTY']:
        print('-'*20)
        foo=df.groupby(by=[attr])[attr].count()
        print(foo)

    for attr in ['GENDER', 'RACE', 'IN PERSON', 'DIVISION']:
        print('-'*20)
        foo = df.groupby([attr, 'IN PERSON']).agg({attr: 'count'})

        print(foo)