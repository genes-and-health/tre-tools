"""
This module contains utility functions for the report transformers.
"""

def logs_to_markdown_table(logs):
    """
    Convert a list of log entries to a Markdown table.
    Each log entry is assumed to be in the format 'YYYY-MM-DD HH:MM:SS.ssssss: Message'.
    We format the timestamp to 'YYYY-MM-DD HH:MM' and separate the message.

    Args:
        logs (List[str]): A list of log entries.

    Returns:
        str: A Markdown table containing the logs.
    """
    markdown = "| Date | Message |\n| --- | --- |\n"

    for log in logs:
        # Split the log entry into timestamp and message
        timestamp, message = log.split(": ", 1)
        # Format the timestamp to 'YYYY-MM-DD HH:MM'
        timestamp = timestamp.split(".")[0]
        # Add the row to the table
        markdown += f"| {timestamp} | {message} |\n"

    return markdown

def codelist_to_markdown_table(codes):
    """
    Convert a list of codes to a Markdown table.

    Args:
        codes (List[str]): A list of codes.

    Returns:
        str: A Markdown table containing the codes.
    """
    markdown = "| Code |\n| --- |\n"  # Table header
    for code in codes:
        markdown += f"| {code} |\n"  # Table rows
    return markdown
