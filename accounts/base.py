from accounts.models import Account

from panda.debug import debug, pm, pp

def get_account(slug_or_id, stdout=None):
    try:
        account = Account.objects.get(slug=slug_or_id)
        # TODO: allow lookup by id? probably not a good idea because the command will be opaque...
    except Account.DoesNotExist as e:
        lookup_success = False
    else:
        lookup_success = True

    if lookup_success:
        return account

    if not stdout:
        return

    stdout.write('must specify account. available accounts:')
    accounts = Account.objects.all()
    for account in accounts:
        print('%d. %s (%s)' % (account.id, account, account.slug))
