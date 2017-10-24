page_colors = {
    'page-background': '#FFFFFF',
    'axis-background': '#F2F7F9',
    'figure-background': '#E4EFF4',
    'text': '#102445',
}

tickfontsize = 10


def get_layout(**kwargs):
    """
    Convenience function to generate layout dict with a
    bunch of defaults.
    Uses a few nicknames like 'xticktext' for layout['xaxis']['ticktext']
    Everything else goes into the top level of the dict.
    """
    layout = {
        'titlefont': {'size': 14},
        'plot_bgcolor': page_colors['axis-background'],
        'paper_bgcolor': page_colors['figure-background'],
        'font': {'color': page_colors['text'], 'size': 10},
        'legend': {
            'x': 0,
            'y': 1,
            'bgcolor': page_colors['axis-background'],
            'bordercolor': '#FFFFFF'
        },
    }
    xaxis = {}
    yaxis = {}

    if 'fontsize' in kwargs.keys():
        layout['font']['size'] = kwargs.pop('fontsize')

    if 'xticktext' in kwargs.keys() and 'xtickvals' in kwargs.keys():
        xaxis.update({
            'ticktext': kwargs.pop('xticktext'),
            'tickvals': kwargs.pop('xtickvals'),
            'tickfont': {'size': tickfontsize},
        })

    if 'xtitle' in kwargs.keys():
        xaxis.update({'title': kwargs.pop('xtitle')})

    if 'ytitle' in kwargs.keys():
        yaxis.update({'title': kwargs.pop('ytitle')})

    layout['xaxis'] = xaxis
    layout['yaxis'] = yaxis
    layout.update(kwargs)
    return layout
