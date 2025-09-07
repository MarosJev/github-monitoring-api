from io import BytesIO

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg


def generate_counts_graph(dict_counts: dict[str, int], offset: int) -> BytesIO:
    """
    :param dict_counts: dictionary with GitHub event types and their counts since offset minutes
    :param offset: offset from current datetime in number of minutes
    :return: buffer with figure png data
    """
    # Sort bars by count desc
    labels = sorted(dict_counts.keys(), key=lambda k: dict_counts[k], reverse=True)
    values = [dict_counts[k] for k in labels]

    fig = Figure(figsize=(6, 3.5), dpi=140)
    ax = fig.add_subplot(1, 1, 1)
    ax.bar(labels, values)
    ax.set_title(f"GitHub events in last {offset} min")
    ax.set_xlabel("Event type")
    ax.set_ylabel("Count")
    fig.tight_layout()

    buf = BytesIO()
    FigureCanvasAgg(fig).print_png(buf)
    buf.seek(0)
    return buf
