"""Portable SVG Pareto scatter plots, with no plotting dependency."""

from html import escape


def pareto_svg(series, title):
    """Plot labelled sets on shared raw-cost axes; callers define the pooling rule."""
    points = [p for values in series.values() for p in values]
    if not points:
        raise ValueError("Cannot plot an empty approximation set.")
    xmin, xmax = min(p[0] for p in points), max(p[0] for p in points)
    ymin, ymax = min(p[1] for p in points), max(p[1] for p in points)
    dx, dy = max(xmax - xmin, 1), max(ymax - ymin, 1)
    xmin, xmax = xmin - .05 * dx, xmax + .05 * dx
    ymin, ymax = ymin - .05 * dy, ymax + .05 * dy
    sx = lambda x: 100 + 620 * (x - xmin) / (xmax - xmin)
    sy = lambda y: 430 - 340 * (y - ymin) / (ymax - ymin)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="800" height="560" viewBox="0 0 800 560">',
             '<rect width="800" height="560" fill="white"/>',
             '<g font-family="sans-serif" font-size="12" fill="#222">',
             f'<text x="400" y="28" text-anchor="middle">{escape(title)}</text>']
    for k in range(6):
        x, y = xmin + k * (xmax-xmin)/5, ymin + k*(ymax-ymin)/5
        parts += [f'<path d="M {sx(x)} 90 V 430 M 100 {sy(y)} H 720" stroke="#ddd"/>',
                  f'<text x="{sx(x)}" y="450" text-anchor="middle">{x:.4g}</text>',
                  f'<text x="90" y="{sy(y)+4}" text-anchor="end">{y:.4g}</text>']
    parts += ['<text x="400" y="480" text-anchor="middle">Facility opening cost (f1)</text>',
              '<text transform="translate(20 260) rotate(-90)" text-anchor="middle">Customer allocation cost (f2)</text>']
    for index, (label, values) in enumerate(series.items()):
        color = ['#2563eb', '#dc2626', '#15803d', '#9333ea'][index % 4]
        for x,y in values:
            parts.append(f'<circle cx="{sx(x)}" cy="{sy(y)}" r="4" fill="{color}" fill-opacity="0.7"/>')
        parts.append(f'<text x="{100+index*180}" y="515" fill="{color}">{escape(label)}</text>')
    return ''.join(parts) + '</g></svg>'
