import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import time

class RealTimePlotter:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.data = pd.DataFrame(columns=['unit_name', 'current', 'min', 'max', 'time'])
        
        self.app = dash.Dash(__name__)
        self.app.layout = html.Div([
            dcc.Graph(id='live-graph', animate=True),
            dcc.Interval(
                id='graph-update',
                interval=1000,  # in milliseconds
                n_intervals=0
            )
        ])

        @self.app.callback(Output('live-graph', 'figure'),
                           [Input('graph-update', 'n_intervals')])
        def update_graph_scatter(n):
            self.update_data()
            fig = make_subplots(rows=1, cols=1, subplot_titles=['Real-time Data Visualization'])
            
            for unit in self.data['unit_name'].unique():
                unit_data = self.data[self.data['unit_name'] == unit]
                fig.add_trace(
                    go.Scatter(x=unit_data['time'], y=unit_data['current'],
                               mode='lines+markers',
                               name=f'{unit} (Current)'),
                    row=1, col=1
                )
                fig.add_trace(
                    go.Scatter(x=unit_data['time'], y=unit_data['min'],
                               mode='lines',
                               name=f'{unit} (Min)',
                               line=dict(dash='dash')),
                    row=1, col=1
                )
                fig.add_trace(
                    go.Scatter(x=unit_data['time'], y=unit_data['max'],
                               mode='lines',
                               name=f'{unit} (Max)',
                               line=dict(dash='dot')),
                    row=1, col=1
                )

            fig.update_layout(
                title='Real-time Data Visualization',
                xaxis_title='Time (s)',
                yaxis_title='Value',
                height=600
            )

            return fig

    def update_data(self):
        new_data = pd.read_csv(self.csv_file, header=None, names=['unit_name', 'current', 'min', 'max', 'time'])
        self.data = pd.concat([self.data, new_data], ignore_index=True)
        self.data = self.data.drop_duplicates(subset=['time'], keep='last')
        self.data = self.data.sort_values('time')
        
        # Converter valores para numéricos, tratando '0' como NaN
        for col in ['current', 'min', 'max']:
            self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
            self.data[col] = self.data[col].replace(0, pd.NA)
        
        # Preencher valores ausentes
        self.data = self.data.fillna(method='ffill')

    def run(self):
        self.app.run_server(debug=True)

if __name__ == "__main__":
    csv_file = "PULSE.csv"  # Substitua pelo nome do seu arquivo CSV
    plotter = RealTimePlotter(csv_file)
    plotter.run()