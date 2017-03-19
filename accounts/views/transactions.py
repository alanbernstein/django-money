from django.shortcuts import render
from django.http import HttpResponse

from accounts.models import (Transaction,
                             MerchantTable,
                             TransactionTable,
                             )

from accounts.helpers import (get_transaction_info,
                              get_merchant_info,
                              get_compare_data,
                              )

from panda.debug import debug


def transaction_list_table(request):
    all_tx = Transaction.objects.all()
    Nt = len(all_tx)
    tx = all_tx[Nt - 30:Nt - 1]

    rows = get_transaction_info(tx)
    print(rows[0])
    table = TransactionTable(rows)
    # return render(request, 'datatable-basic.html', {'table': table})
    return render(request, 'datatable.html',
                  {'table': table, 'resource': 'transaction'})


def transaction_list_simple(request):
    resp = ''

    resp += '<h2>all transactions</h2>'
    for t in Transaction.objects.all():
        resp += t.as_link()

    return HttpResponse(resp)


transaction_list = transaction_list_table


def transaction_detail(request, *args, **kwargs):
    tid = kwargs['transaction_id']

    t = Transaction.objects.get(id=tid)
    row = get_transaction_info(t)
    table0 = TransactionTable(row)

    tx = Transaction.objects.filter(merchant_id=t.merchant.id)
    rows = get_transaction_info(tx)
    table1 = TransactionTable(rows)

    # m = get_merchants_with_similar_tags(t.tags.all())
    m = [t.merchant]
    rows = get_merchant_info(m)
    table2 = MerchantTable(rows)

    return render(request, 'transaction-detail.html', {
        'merchant_summary': t.merchant.get_summary(),
        'table0': table0,
        'table1': table1,
        'table2': table2,
    })


def transactions_untagged(request, sort=False):
    # TODO: sort by frequency
    # sorted_items = profile.ItemList.annotate(itemcount=Count('name'))
    # sorted_items = sorted_items.order_by('-itemcount')

    tx = Transaction.objects.filter(tags__isnull=True, merchant__tags__isnull=True)
    rows = get_transaction_info(tx)
    rows2 = [row for row in rows if not row['tags']]  # TODO: why is this necessary
    table = TransactionTable(rows2)
    # return render(request, 'datatable-basic.html', {'table': table})
    return render(request, 'datatable.html',
                  {'table': table, 'resource': 'transaction'})


def transactions_unnamed(request, *args, **kwargs):
    # this doesnt make sense right?
    return ''


def transactions_compare(request, tags):
    # TODO: this should render a template which hits an api for data
    taglist = tags.split('+')
    data = ''
    data += 'tags: %s' % ', '.join(taglist)
    chart_data = get_compare_data(taglist)
    return HttpResponse(data)


def transactions_subdivide(request, tags):
    # TODO: this should render a template which hits an api for data
    taglist = tags.split('+')
    data = ''
    data += 'tags: %s' % ', '.join(taglist)
    chart_data = get_subdivide_data(taglist)
    return HttpResponse(data)
