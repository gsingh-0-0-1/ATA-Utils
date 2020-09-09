#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from flask import Flask
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input,Output

import numpy as np
import pandas as pd
import time

#from simulator import ata_snap_fengine
from ata_snap import ata_snap_fengine
from ATATools import ata_control
import casperfpga
from threading import Thread
import atexit


BW = 900 #MHz

snaps = ['frb-snap1-pi', 'frb-snap2-pi', 
        'frb-snap3-pi', 'frb-snap4-pi',
        'frb-snap5-pi', 'frb-snap6-pi',
        'frb-snap7-pi', 'frb-snap8-pi',
        'frb-snap9-pi', 'frb-snap10-pi',
        ]

snap_table = "/home/obsuser/share/ata_snap.tab"
snap_ant = np.loadtxt(snap_table, dtype=str, usecols=(0,1))
#ata_snap_tab = pd.read


class cfreqThread(Thread):
    def __init__(self, *args, **kwargs):
        super(cfreqThread,self).__init__(*args, **kwargs)
        self.cfreq = ata_control.get_sky_freq()

    def run(self):
        #self.cfreq = ata_control.get_sky_freq()
        while True:
            time.sleep(20)
            self.cfreq = ata_control.get_sky_freq()


cfreq_thread = cfreqThread()
cfreq_thread.daemon = True
cfreq_thread.start()


fengs = [ata_snap_fengine.AtaSnapFengine(snap, 
    transport=casperfpga.KatcpTransport) 
        for snap in snaps]
for feng in fengs:
    feng.fpga.get_system_information(
            "/home/obsuser/snap_adc5g_feng_rpi_2020-07-06_1146.fpg")


FIGS = {}
for snap in fengs:
    fig = make_subplots(rows=1, cols=2, 
            column_widths=[0.8, 0.2], horizontal_spacing=0.05,
            #column_titles=['Spectra', 'ADC values'],
            )

    cfreq = cfreq_thread.cfreq
    xx,yy = snap.spec_read()
    adc_x, adc_y = snap.adc_get_samples()
    x = np.linspace(cfreq - BW/2, cfreq + BW/2, len(xx))

    fig.append_trace({
	    'x': x,
	    'y': 10*np.log(xx+0.1),
	    'name': 'X-pol',
	    'mode': 'lines',
	    'type': 'scatter'
	}, 1, 1)
    fig.append_trace({
	    'x': x,
	    'y': 10*np.log(yy+0.1),
	    'name': 'Y-pol',
	    'mode': 'lines',
	    'type': 'scatter'
	}, 1, 1)

    fig.append_trace(
            go.Histogram(x=adc_x, name='RMS_x: %.2f' %np.std(adc_x), 
                marker_color='blue'), 
            1, 2)
    fig.append_trace(
            go.Histogram(x=adc_y, name='RMS_y: %.2f' %np.std(adc_y), 
                marker_color='red'), 
            1, 2)

    ind = np.where(snap_ant[:,0] == snap.host)[0]
    ant_name = snap_ant[ind,1][0]

    fig.update_layout(
            title="<b>Snap:</b> %s --- <b>Antenna:</b> %s" 
              %(snap.host, ant_name),
            xaxis_title = 'Frequency (MHz)',
            yaxis_title = 'Power (dB)',
            xaxis2_title = 'ADC values',
            margin=dict(l=30, r=30, b=50, t=50),
            font = dict(family='Times new roman', size=20),
            #annotations = dict(size=60)
            )

    FIGS[snap.host] = fig


graphs = [dcc.Graph(figure=FIGS[snap_name], id=snap_name) for snap_name in snaps]
FIGS_HTML = html.Div(graphs, id='figs_html')

app = dash.Dash()
#app = Flask(__name__)
app.layout = html.Div(
    [html.H1('ATA snap monitor')] +
    [html.Br()]*3 + 
    [FIGS_HTML] + 
    [dcc.Interval(
        id='plot-update',
        interval = 10*1000,
        n_intervals = 0)]
    )


@app.callback(
        [Output("figs_html", "children")],
        [Input("plot-update", "n_intervals")])
def gen_bp(interval=None):
    cfreq = cfreq_thread.cfreq
    for i,snap in enumerate(fengs):
        xx,yy = snap.spec_read()
        adc_x, adc_y = snap.adc_get_samples()
        x = np.linspace(cfreq - BW/2, cfreq + BW/2, len(xx))
        FIGS_HTML.children[i].figure.data[0].y = 10*np.log10(xx + 0.1)
        FIGS_HTML.children[i].figure.data[0].x = x
        FIGS_HTML.children[i].figure.data[1].y = 10*np.log10(yy + 0.1)
        FIGS_HTML.children[i].figure.data[1].x = x

        FIGS_HTML.children[i].figure.data[2].x = adc_x
        FIGS_HTML.children[i].figure.data[2].name = 'RMS_x: %.2f' %np.std(adc_x)
        FIGS_HTML.children[i].figure.data[3].x = adc_y
        FIGS_HTML.children[i].figure.data[3].name = 'RMS_y: %.2f' %np.std(adc_y)

    return [FIGS_HTML.children]


HOST = "10.10.1.151"
PORT = 8787
if __name__ == "__main__":
    #from waitress import serve
    #serve(app, host=HOST, port = PORT)
    app.run_server(port=PORT, host=HOST)
