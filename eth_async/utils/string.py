def text_between(text: str, begin: str = '', end: str = ''):
    try:
        if begin:
            start = text.index(begin) + len(begin)
        else:
            start = 0
    except:
        start = 0

    try:
        if end:
            end = text.index(end, start)
        else:
            end = len(text)
    except:
        end = len(text)

    excerpt = text[start:end]
    if excerpt == text:
        return ''

    return excerpt
