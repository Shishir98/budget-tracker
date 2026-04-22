from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import os, json
from ..models import Transaction, Category
from ..forms import PDFUploadForm
from ..pdf_parser import parse_bank_statement, guess_category, guess_transaction_type, guess_category_name


@login_required
def upload_pdf(request):
    if request.method == 'POST' and 'pdf_file' in request.FILES:
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = request.FILES['pdf_file']
            # Save temp
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                for chunk in pdf_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            
            try:
                raw_txns = parse_bank_statement(tmp_path)
            except Exception as e:
                messages.error(request, f'Could not parse PDF: {e}')
                os.unlink(tmp_path)
                return redirect('upload_pdf')
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            
            if not raw_txns:
                messages.warning(request, 'No transactions found in the PDF.')
                return redirect('upload_pdf')
            
            # Store in session for preview
            categories = Category.objects.filter(user=request.user)
            preview = []
            for t in raw_txns:
                guessed_cat = guess_category(t['description'], categories)
                guessed_type = guess_transaction_type(t['description'], t['is_withdrawal'])
                guessed_cat_name = guess_category_name(t['description'])
                preview.append({
                    'date': t['date'].strftime('%Y-%m-%d'),
                    'amount': str(t['amount']),
                    'description': t['description'][:120],
                    'is_withdrawal': t['is_withdrawal'],
                    'type': guessed_type,
                    'category_id': guessed_cat.pk if guessed_cat else '',
                    'category_name': guessed_cat.name if guessed_cat else (guessed_cat_name or ''),
                })
            
            request.session['pdf_preview'] = preview
            return redirect('pdf_preview')
    else:
        form = PDFUploadForm()
    
    return render(request, 'core/pdf/upload.html', {'form': form})


@login_required
def pdf_preview(request):
    preview = request.session.get('pdf_preview', [])
    if not preview:
        return redirect('upload_pdf')
    
    categories = Category.objects.filter(user=request.user)
    
    if request.method == 'POST':
        # Import selected transactions
        tx_data = request.POST.getlist('tx_data')
        imported = 0
        for td in tx_data:
            try:
                d = json.loads(td)
                cat_id = d.get('category_id')
                cat = None
                if cat_id:
                    try:
                        cat = Category.objects.get(pk=int(cat_id), user=request.user)
                    except (Category.DoesNotExist, ValueError):
                        pass
                
                from datetime import date
                Transaction.objects.create(
                    user=request.user,
                    date=date.fromisoformat(d['date']),
                    amount=d['amount'],
                    type=d['type'],
                    category=cat,
                    is_subscription=cat.is_subscription if cat else False,
                    notes=d.get('description', '')[:500],
                    raw_description=d.get('description', '')[:1000],
                    from_pdf=True,
                )
                imported += 1
            except Exception:
                continue
        
        del request.session['pdf_preview']
        messages.success(request, f'Imported {imported} transactions. Unlabeled ones can be categorized from the Transactions page.')
        return redirect('transaction_list')
    
    return render(request, 'core/pdf/preview.html', {
        'preview': preview,
        'categories': categories,
        'total': len(preview),
    })
