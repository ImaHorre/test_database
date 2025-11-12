import panel as pn
import pandas as pd
import hvplot.pandas
import sys

pn.extension()

# Load data (from command line arg or default)
if len(sys.argv) > 1:
    csv_file = sys.argv[1]
else:
     csv_file = r'data\test_database.csv'  # Updated path

df = pd.read_csv(csv_file)

# Create widgets for column selection
x_col = pn.widgets.Select(name='X-axis', options=list(df.columns), value=df.columns[0])
y_col = pn.widgets.Select(name='Y-axis', options=list(df.columns), value=df.columns[1] if len(df.columns) > 1 else df.columns[0])

# Function to create plot based on selections
@pn.depends(x_col, y_col)
def create_plot(x, y):
    return df.hvplot.scatter(x=x, y=y, width=600, height=400)

# Layout
layout = pn.Row(
    pn.Column('## Plot Controls', x_col, y_col, width=200),
    create_plot
)

# Serve
layout.servable()
pn.serve(layout, show=True, port=5006)