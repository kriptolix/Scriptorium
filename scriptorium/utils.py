from gi.repository import Gtk
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


def html_to_buffer(html_content: str, buffer: Gtk.TextBuffer):
    """
    Turn the content of an HTML payload into TextBuffer content with tags
    """

    # Process the lines and populate the buffer
    soup = BeautifulSoup(html_content, 'html.parser')
    paragraphs = soup.find_all('p')
    for paragraph in paragraphs:
        for child in paragraph.children:
            text = child.get_text()
            if len(text) > 1:
                start = buffer.get_end_iter()
                if child.name:
                    buffer.insert_with_tags_by_name(start, text, child.name)
                else:
                    buffer.insert(start, text)
        start = buffer.get_end_iter()
        buffer.insert(start, "\n\n")

    # Place the cursor at the start of the buffer
    start = buffer.get_start_iter()
    buffer.place_cursor(start)


def buffer_to_html(buffer: Gtk.TextBuffer):
    """
    Turn the content of a TextBuffer content with tags into a HTML payload
    """

    html_content = []

    # Extract all the text
    iterator = buffer.get_start_iter()
    end_iter = buffer.get_end_iter()
    while not iterator.equal(end_iter):
        # Find the next tag
        next_toggle = iterator.copy()
        if not next_toggle.forward_to_tag_toggle():
            next_toggle = end_iter.copy()

        # Extract the current text
        segment_text = buffer.get_text(iterator, next_toggle, True)

        # Apply tags
        segment_html = segment_text
        tags = iterator.get_tags()
        for tag in tags:
            tag_id = tag.get_property('name')
            segment_html = f"<{tag_id}>{segment_html}</{tag_id}>"

        # Append that piece of text
        html_content.append(segment_html)

        # Move on
        iterator = next_toggle.copy()

    # Split according to paragraphs
    paragraphs = ''.join(html_content).split('\n\n')
    html_content = [f'<p>{paragraph}</p>' for paragraph in paragraphs if len(paragraph) > 1]

    return '\n'.join(html_content)


def get_child_at(widget, position):
    # In the special case we ask for -1 return None
    if position < 0:
        return None

    # Iterate until the desired position, or running out of children
    index = 0
    child = widget.get_first_child()
    while index != position and child is not None:
        child = child.get_next_sibling()
        index += 1

    # We reached the end of the list, return the last child
    if child is None:
        widget.get_last_child()

    return child

