import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output
from dash.dependencies import State
import dash_auth
import gunicorn

# Read the data from the CSV file
df = pd.read_excel('Total_Field.xlsx')
# Define valid username and password
VALID_USERNAME_PASSWORD_PAIRS = {'admin': 'AdminDashPass'}
# Get all unique ID# values from the original dataset
all_ids = df['ID#'].unique()

# Drop missing values for "Nitrate (mg N/L)", "Soil Type", "Tillage", and "Crops" in the filtered data
df.dropna(subset=['Nitrate (mg N/L)', 'Soil Type', 'Tillage', 'Crops'], inplace=True)

# Define the custom order for Soil Type
custom_order = ['Silt', 'Loam/Silt', 'Loam', 'Clay/loam', 'Clay']

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server
# Enable authentication
auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)

# Define the available crop options
crop_options = [{'label': crop, 'value': crop} for crop in df['Crops'].unique()]

# Define the available ID options (All IDs pre-selected)
id_options = [{'label': id, 'value': id} for id in all_ids]

# Define the available variable options for Y-axis
variable_options = [
    {'label': 'Average Nitrate Concentration (mg N/L)', 'value': 'Nitrate (mg N/L)'},
    {'label': 'Total Instantaneous Nitrate Load (lb/day)', 'value': 'Instantaneous Nitrate Load (lb/day)'},
    {'label': 'Volume (L)', 'value': 'Volume (L)'},
    {'label': 'Time (seconds)', 'value': 'Time (seconds)'},
    {'label': 'Discharge (L/s)', 'value': 'Discharge (L/s)'},
    {'label': 'Drainage Area (acres)', 'value': 'Drainage Area (acres)'},
]

# Define the available X-axis options
x_axis_options = [
    {'label': 'Soil Type', 'value': 'Soil Type'},
    {'label': 'Sample Date', 'value': 'Sample Date'},
    {'label': 'Depth Buried', 'value': 'Depth Buried'},
    {'label': 'Discharge (L/s)', 'value': 'Discharge (L/s)'},
    {'label': 'Drainage Area (acres)', 'value': 'Drainage Area (acres)'},
    {'label': 'Cover crop or no', 'value': 'Cover crop or no'},
    {'label': 'Cover Crop planted before season?', 'value': 'Cover Crop planted before season?'}
]

# Define the layout of the app
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

page1_layout = html.Div([
    html.H1("Field Analysis"),
    html.Label("Select Crop:"),
    dcc.Dropdown(
        id='crop-dropdown',
        options=crop_options,
        value=crop_options[0]['value'],  # Set the default selected crop
    ),
    html.Label("Select ID(s):"),
    dcc.Dropdown(
        id='id-dropdown',
        options=id_options,
        value=all_ids,  # Set all IDs as pre-selected
        multi=True  # Allow multiple selections
    ),
    html.Label("Select Variable for Y-axis:"),
    dcc.Dropdown(
        id='variable-dropdown',
        options=variable_options,
        value=variable_options[0]['value'],  # Set the default selected variable
    ),
    html.Label("Select X-axis:"),
    dcc.Dropdown(
        id='x-axis-dropdown',
        options=x_axis_options,
        value=x_axis_options[0]['value'],  # Set the default selected X-axis
    ),
    dcc.Graph(id='nitrate-plot'),
    html.H5(
        "Note to Viewers:  When selecting a different variable, please ensure to revisit the ID dropdown menu.\n Some IDs might be initially missing from the dropdown list due to the presence of missing data in certain columns, such as 'Soil Type'.\n To include all available IDs, \n select the ID option and include any missing IDs manually.   "),

    html.H6(
        "Note to Viewers:When selecting the Sample Date variable for the X-axis, please note that it will only work with 'Nitrate' and 'Load' variables. In this case, the chart type will automatically switch to a bar chart, providing a clear representation of the data."),
    ])
# dcc.Link(html.Button('Go to Page 2'), href='/page-2')

# Page 2 layout
# Page 2 layout
page2_layout = html.Div([
    html.H1("Instantaneous Nitrate Flux by Tillage"),
    dcc.Graph(id='page-2-graph'),  # Use the `fig` variable here
    dcc.Link(html.Button('Go to Page 1'), href='/page-1'),
])


# Callback to update the plot for Page 1 based on selected X-axis variable
@app.callback(
    Output('nitrate-plot', 'figure'),
    Input('crop-dropdown', 'value'),
    Input('id-dropdown', 'value'),
    Input('variable-dropdown', 'value'),
    Input('x-axis-dropdown', 'value'),
)
def update_plot(selected_crop, selected_ids, selected_variable, selected_x_axis):
    # Filter data based on selected crop, IDs
    filtered_df = df[(df['Crops'] == selected_crop) & (df['ID#'].isin(selected_ids))]

    # Determine the chart type based on the selected X-axis variable
    if selected_x_axis == 'Sample Date':
        chart_type = 'bar'
    else:
        chart_type = 'violin'

    # Create bar chart if Sample Date is selected as X-axis variable
    if chart_type == 'bar':
        # Calculate average nitrate concentration for each sample date
        avg_nitrate_df = filtered_df.groupby([selected_x_axis, 'Tillage'])[selected_variable].mean().reset_index()
        fig = px.bar(
            avg_nitrate_df,
            x=selected_x_axis,
            y=selected_variable,
            text=selected_variable,
            color='Tillage',  # Color-coded by Tillage
            title=f'Average {selected_variable} for {selected_crop} by {selected_x_axis}',
            labels={selected_x_axis: selected_x_axis, selected_variable: selected_variable},
        )
        fig.update_traces(textposition='outside', opacity=1)
    else:
        # Create violin plot for other X-axis variables
        fig = px.violin(
            filtered_df,
            x=selected_x_axis,
            y=selected_variable,
            category_orders={'Soil Type': custom_order},
            box=True,
            points='all',
            title=f'{selected_variable} for {selected_crop} by {selected_x_axis}',
            labels={selected_x_axis: selected_x_axis, selected_variable: selected_variable}
        )

        # Create scatter plot
        scatter_fig = px.scatter(
            filtered_df,
            x=selected_x_axis,
            y=selected_variable,
            symbol='Tillage',
            symbol_sequence=['x', 'diamond', 'square'],
            color_discrete_sequence=['orange', 'green', 'brown'],
            color='Tillage',  # Color-coded by Tillage
            title=f'{selected_variable} for {selected_crop} by {selected_x_axis}',
            labels={selected_x_axis: selected_x_axis, selected_variable: selected_variable},
        )

        # Define the separation factor for jitter
        separation_factor = -1  # Adjust as needed

        # Adjust x-values for scatter points to place them beside the violins
        for trace in scatter_fig.data:
            if trace.name != 'Tillage':
                continue
            trace.x = [x + separation_factor for x in trace.x]  # Shift x-values
        fig.add_traces(scatter_fig.data)

    return fig


# Callback to display the bubble chart
def display_bubble_chart():
    # Read data and create bubble chart
    df_bubble = pd.read_csv('total_lit.csv').dropna(subset=['ID#', 'Tillage', 'Instantaneous Nitrate Flux (lb/day/acre)'])
    id_0_df = df_bubble[(df_bubble['ID#'] == 0) & (df_bubble['Instantaneous Nitrate Flux (lb/day/acre)'] >= 0.01) &
                        (df_bubble['Instantaneous Nitrate Flux (lb/day/acre)'] <= 0.4)]

    other_ids_df = df_bubble[(df_bubble['ID#'] != 0) & (df_bubble['Instantaneous Nitrate Flux (lb/day/acre)'] >= 0.01) &
                             (df_bubble['Instantaneous Nitrate Flux (lb/day/acre)'] <= 0.4)]

    bubble_fig = px.scatter(other_ids_df, x='Tillage', y='Instantaneous Nitrate Flux (lb/day/acre)',
                            size='Instantaneous Nitrate Flux (lb/day/acre)', color='Tillage',
                            symbol='Tillage', symbol_sequence=['hourglass', 'x', 'diamond', 'square'],
                            color_discrete_sequence=['blue', 'orange', 'green', 'brown'],
                            labels={'Instantaneous Nitrate Flux (lb/day/acre)': 'Flux (lb/day/acre)',
                                    'Tillage': 'Tillage'},
                            title='Instantaneous Nitrate Flux by Tillage ',
                            category_orders={'Tillage': sorted(other_ids_df['Tillage'].unique())},
                            opacity=0.9, size_max=10)

    bubble_fig.add_trace(px.scatter(id_0_df, x='Tillage', y='Instantaneous Nitrate Flux (lb/day/acre)',
                                    size='Instantaneous Nitrate Flux (lb/day/acre)',
                                    color_discrete_sequence=['grey'],
                                    opacity=0.7, size_max=10).data[0])

    bubble_fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode='markers',
        marker=dict(size=10, color='grey'),
        name='Other Farms'
    ))

    bubble_fig.update_traces(marker_size=10, marker=dict(line=dict(width=2, color='DarkSlateGrey')))
    bubble_fig.update_layout(scattermode="group", scattergap=0.45)

    return html.Div([html.H1("Instantaneous Nitrate Flux Analysis"),
                     dcc.Graph(figure=bubble_fig)])


# Define the app's callback to switch between pages
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
# Callback to update the plot for Page 2
@app.callback(
    Output('page-2-graph', 'figure'),
    Input('some-input', 'value'))
def display_page(pathname):
    if pathname == '/page-2':
        return page2_layout
    else:
        return page1_layout


if __name__ == '__main__':
    app.run_server(debug=False)