import re
from typing import List

# Your long list
icon_list = ['action_123_materialicons_20px', 'action_123_materialicons_24px',
             'action_3d_rotation_materialicons_24pxons_24px',
             'av_closed_caption_materialicons_24px',
             'av_closed_caption_off_materialicons_24px',
             # ... (rest of your list)
             ]


def search_icons(query: str, icons: List[str], regex: bool = True) -> List[str]:
    """
    Search for icons in the list.

    :param query: Substring or regex pattern to search for
    :param icons: List of icon names
    :param regex: If True, treat query as regex
    :return: List of matching icon names
    """
    query = query.replace(' ', '_')
    if regex:
        pattern = re.compile(query)
        return [icon for icon in icons if pattern.search(icon)]
    else:
        return [icon for icon in icons if query in icon]


# Examples:
matches_substring = search_icons("caption off", icon_list)
matches_regex = search_icons(r"av_pause.*24px$", icon_list, regex=True)

print("Substring matches:", matches_substring)
print("Regex matches:", matches_regex)
