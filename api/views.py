from accounts.search import search_tags, search_merchants, search_transactions


def search(*args, **kwargs):
    print(args)
    print(kwargs)
    tags = search_tags(kwargs['keyword'])

    return ''


def trends(*args, **kwargs):
    return ''
