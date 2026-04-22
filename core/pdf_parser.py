import pdfplumber, re, datetime
from decimal import Decimal

CATEGORY_KEYWORDS = {
    'Food & Dining':     ['swiggy', 'zomato', 'blinkit', 'zepto', 'zeptoonline', 'zepto mark'],
    'Investments':       ['indianesign', 'indmoney', 'zerodha', 'groww', 'indstocks', 'smallcase', 'sip'],
    'Transport':         ['uber', 'ola', 'rapido', 'irctc', 'redbus'],
    'Shopping':          ['amazon', 'flipkart', 'myntra', 'ajio', 'meesho'],
    'Entertainment':     ['netflix', 'spotify', 'hotstar', 'prime video', 'youtube', 'googleplay', 'pvr', 'inox', 'apple medi', 'appleservices'],
    'Utilities':         ['airtel', 'jio', 'vodafone', 'broadband', 'bsnl', 'cc billpay', 'bil/inft', 'electricity'],
    'Health':            ['pharmacy', 'apollo', 'medplus', 'netmeds', '1mg', 'practo', 'gym'],
    'Personal Transfer': ['gurvinder', 'himanshu', 'shaheed', 'nitul', 'deepak', 'khuranabek'],
}

def guess_category_name(desc):
    dl = desc.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(kw in dl for kw in kws):
            return cat
    return None

def guess_category(desc, categories_qs):
    name = guess_category_name(desc)
    if not name:
        return None
    for cat in categories_qs:
        if cat.name.lower() == name.lower():
            return cat
    return None

def guess_transaction_type(desc, is_withdrawal):
    if not is_withdrawal:
        return 'income'
    dl = desc.lower()
    if any(k in dl for k in ['indianesign', 'indmoney', 'zerodha', 'sip', 'indstocks', 'mutual fund']):
        return 'investment'
    return 'expense'

def clean_description(raw):
    raw = re.sub(r'\s+', ' ', raw).strip()
    if not raw:
        return 'Unknown'
    # Strip trailing/leading hash codes (long hex strings, PTM codes etc)
    raw = re.sub(r'\b[A-Z]{2,4}[0-9A-Fa-f]{8,}\b', '', raw)
    raw = re.sub(r'\b[0-9A-Fa-f]{16,}\b', '', raw)
    raw = re.sub(r'\s+', ' ', raw).strip().strip('/')

    if re.search(r'BIL/INFT.*CC BillPay', raw, re.IGNORECASE):
        return 'Credit Card Bill Payment'
    if 'INDIANESIGN' in raw.upper() or re.match(r'ACH/TP ACH', raw, re.IGNORECASE):
        return 'SIP / Mutual Fund Investment'
    neft = re.search(r'NEFT-\w+-(.+?)-(?:SALARY|NEFT\s|[A-Z]{4}\d|DSCNB)', raw, re.IGNORECASE)
    if neft:
        name = neft.group(1).strip().title()
        return f"{name} — Salary" if 'salary' in raw.lower() else name
    # NEFT credit without above pattern
    neft2 = re.search(r'NEFT-\w+-(.+?)(?:\s*$|-\d{4,})', raw, re.IGNORECASE)
    if neft2:
        name = neft2.group(1).strip().title()
        return f"{name} — Salary" if 'salary' in raw.lower() else name
    upi = re.search(r'UPI/([^/@\s]+)', raw, re.IGNORECASE)
    if upi:
        merchant = upi.group(1).strip()
        merchant = re.sub(r'(Ltd|Pvt|Mark|Medi|Corp)$', '', merchant, flags=re.IGNORECASE).strip()
        return merchant.title()
    msi = re.match(r'MSI/(\w+)', raw, re.IGNORECASE)
    if msi:
        return msi.group(1).replace('GOOGLEPLAY', 'Google Play').title()
    # Last resort: take first meaningful chunk
    return raw[:60].strip()


def parse_bank_statement(pdf_path):
    all_text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                all_text += t + '\n'

    lines = [l.strip() for l in all_text.split('\n')]
    main_re   = re.compile(r'^(\d{1,3})\s+(\d{2}\.\d{2}\.\d{4})\s*(.*)')
    date_re   = re.compile(r'\d{2}\.\d{2}\.\d{4}')
    amt_re    = re.compile(r'\b(\d[\d,]*\.\d{2})\b')
    upi_re    = re.compile(r'^(UPI|NEFT|ACH|BIL|MSI|IMPS|RCHG)', re.IGNORECASE)

    noise_kw = ['www.icici', 'never share', 'sincerely', 'team icici', 'legends',
                'dial your', 'please call', 'statement of transactions',
                'gaur green', 'indirapuram', 'your base branch',
                'withdrawal amount', 'deposit amount', 'cheque number',
                'balance (inr)', 'transaction remarks', 'amount (inr)',
                'transaction\ndate', 's no.', 'branch,']

    def is_noise(l):
        ll = l.lower()
        return any(k in ll for k in noise_kw) or not l

    main_idxs = [i for i, l in enumerate(lines) if main_re.match(l)]

    rows = []
    for ki, idx in enumerate(main_idxs):
        m      = main_re.match(lines[idx])
        sno    = int(m.group(1))
        date_s = m.group(2)
        inline = m.group(3).strip()

        # Extract amounts from main line (strip date first to avoid date-fragment matches)
        clean_line = date_re.sub('', lines[idx])
        clean_line = re.sub(r'^\s*\d{1,3}\s+', '', clean_line)
        amounts = [float(a.replace(',', '')) for a in amt_re.findall(clean_line)]

        if len(amounts) < 2:
            continue
        balance   = amounts[-1]
        tx_amount = amounts[-2]

        # Description strategy:
        # 1. Inline if it starts with UPI/NEFT etc.
        # 2. Otherwise look backward (withdrawals) or forward (deposits)
        desc_raw = ''

        if upi_re.match(inline):
            desc_raw = inline
        else:
            # Look backward up to 3 lines
            for back in range(idx - 1, max(idx - 4, -1), -1):
                l = lines[back]
                if is_noise(l) or main_re.match(l):
                    break
                if upi_re.match(l):
                    desc_raw = l
                    break

            # If nothing found backward, look forward (NEFT credits, deposits)
            if not desc_raw:
                next_main = main_idxs[ki + 1] if ki + 1 < len(main_idxs) else len(lines)
                for fwd in range(idx + 1, min(next_main, idx + 5)):
                    l = lines[fwd]
                    if is_noise(l):
                        continue
                    if l:
                        desc_raw = l
                        # Collect continuation lines
                        for fwd2 in range(fwd + 1, min(next_main, fwd + 4)):
                            l2 = lines[fwd2]
                            if l2 and not is_noise(l2) and not main_re.match(l2):
                                desc_raw += ' ' + l2
                        break

        if not desc_raw and inline:
            desc_raw = inline

        rows.append({'sno': sno, 'date': datetime.datetime.strptime(date_s, '%d.%m.%Y').date(),
                     'amount': tx_amount, 'balance': balance, 'desc': desc_raw})

    # Determine wd/deposit via balance delta
    transactions = []
    for k, r in enumerate(rows):
        if k == 0:
            is_wd = True
        else:
            delta = r['balance'] - rows[k - 1]['balance']
            is_wd = abs(delta + r['amount']) < 0.10  # balance dropped = withdrawal

        display  = clean_description(r['desc'])
        tx_type  = guess_transaction_type(r['desc'], is_wd)

        transactions.append({'date': r['date'], 'amount': Decimal(str(r['amount'])),
                             'is_withdrawal': is_wd, 'description': display,
                             'raw': r['desc'], 'type': tx_type})
    return transactions
