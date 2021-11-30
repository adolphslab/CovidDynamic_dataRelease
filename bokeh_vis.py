#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 17 11:24:59 2020

@author: yantinghan
"""

# try to visualize the studies 

import numpy as np
import pandas as pd
import cairosvg
from bokeh.io import output_notebook, show, export_png, export_svgs,  output_file
from bokeh.plotting import figure
from bokeh.models import HoverTool, ColumnDataSource




np.random.seed(81920)

raw = pd.read_csv('study_summary/summary of covid studies_full_8_19.csv')

# selected the included only
data = raw.groupby(['Included']).get_group(1) 
data = data.reset_index (drop = True)

# calculate #domains, #tasks by addings columns up
data['n_domains'] = data['DB'] + data['DLI'] +data['AB'] + data['EM'] + data['PH']\
                    + data['SB']+ data['DMT'] + data['IAT'] 
domains = []
for i in range(len(data)):
    domain = ''
    domain_short = ['DB','DLI','AB','EM','PH', 'SB','DMT','IAT' ]
    domain_name = ["Demographics & background,", "Daily life impact,", "Attitudes & beliefs,", \
                   "Emotion & mental health,", "Physical health,", "Social behaviors,",\
                   "Decision making, ", "Implicit attitude"]
    for j in range(len(domain_short)):
        if  data[domain_short[j]][i]>0:
             domain += domain_name[j]
    domains.append(domain)

data['domains']  =  np.array(domains)
data['tasks'] = data['DMT'] + data['IAT'] + data['OT']

# recode the freq values
freq_dict = {"cross-sectional": 1,"6-monthly":2, "4-monthly":3, "3-monthly":4,"bi-monthly":5,\
             "monthly":6 , "3-weekly":7, "bi-weekly":8, "weekly":9, "daily":10} ## needs to update
data['average_freq'] = data['average_freq'].replace(freq_dict)

# sample size will be represented using circle size, take log because of the range
data['size']= 1.2*np.log(data['SS']) # adjust parameter later
# only us study will be in orange, others will be in grey
data["color"] = np.where(data["US"] > 0, "orange", "grey")
# only study with tasks have solid color
data["alpha"] = np.where(data["tasks"] > 0, 0.9, 0.1)

# add random noise to x, y values to have some jitter 
# adjust parameter later
data["x_pos"] = data['n_domains'] + np.random.normal(0,0.2,len(data['n_domains']))
data["y_pos"] = data['average_freq'] + np.random.normal(0,0.2,len(data['average_freq']))

source = ColumnDataSource(data)
hover = HoverTool(
        tooltips=[
            ("study name", "@{Study name (link)}"), 
            ("follow-up freq", "@{Duration/frequency}"),             
            ("sample size", "@SS"),   
            ("domains", "@domains")

        ]
    )

p = figure(plot_width=1200, plot_height=700, x_range=(1,8), title="Summary of COVID-related Psychological Studies", tools=[hover, 'wheel_zoom','pan'],)

p.title.text_font_size = '25pt'
p.title.text_font_style = "normal"
p.title.text_font = "times"

p.xaxis.axis_label = 'Number of domains assessed'
p.xaxis.axis_label_text_font_style = "normal"
p.xaxis.axis_label_text_font = "times"
p.xaxis.major_label_text_font = "times"
p.xaxis.axis_label_text_font_size = "20pt"
p.xaxis.major_label_text_font_size = "15pt"

p.yaxis.axis_label = 'Average follow-up frequency'
p.yaxis.axis_label_text_font_style = "normal"
p.yaxis.axis_label_text_font = "times"
p.yaxis.major_label_text_font = "times"
p.yaxis.axis_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "15pt"

p.xaxis.ticker = [1,2,3,4,5,6,7,8]
p.yaxis.ticker = [1,2,3,4,5,6,7,8,9,10]
p.yaxis.major_label_overrides = {1: "cross-sectional", 2: "6-monthly", 3: "4-monthly", 4: "3-monthly", 5: "bi-monthly", 6: "monthly", \
                                 7: "3-weekly",8: "bi-weekly", 9: "weekly", 10: "daily"}## needs to update


 
# add a circle renderer with x and y coordinates, size, color, and alpha
r = p.circle(x="n_domains", y="average_freq", source=source, size="size", color="color",  fill_alpha="alpha")
# =============================================================================
# r = p.circle(x="x_pos", y="y_pos", source=source, size="size", color="color",  fill_alpha="alpha")
# p.output_backend = "svg"
# export_svgs(p, filename="summary_jittered_check.svg")
# =============================================================================
#export_png(p, filename="summary_jittered.png",height=1200, width=1200)

#cairosvg.svg2pdf(url="summary_jittered.svg",dpi=200,write_to="summary_jittered.pdf")
show(p)
output_file("summary_jittered.html")
#export_png(r, filename="summary_jittered.png")
#show(p) # show the results



















