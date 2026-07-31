# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SetPasswordSimpleForm, WorkerCreateForm, WorkerEditForm
from contracts.models import Amal, amal_yoz

from .models import User


def _boss_required(user):
    if not user.is_boshliq:
        raise PermissionDenied('Bu bo\'lim faqat boshliqlar uchun.')


def _my_workers(boss):
    qs = User.objects.filter(role=User.ROLE_ISHCHI)
    if not boss.is_superuser:
        qs = qs.filter(added_by=boss)
    return qs


@login_required
def worker_list(request):
    _boss_required(request.user)
    workers = _my_workers(request.user).annotate(
        live_count=Count('contracts'), live_amount=Sum('contracts__amount'),
    ).order_by('-is_active', 'username')
    return render(request, 'accounts/worker_list.html', {'workers': workers})


@login_required
def worker_create(request):
    _boss_required(request.user)
    form = WorkerCreateForm(request.POST or None, boss=request.user)
    if request.method == 'POST' and form.is_valid():
        worker = form.save()
        amal_yoz(request.user, Amal.ISHCHI_QOSHDI, str(worker))
        messages.success(request, f'Ishchi {worker} qo\'shildi.')
        return redirect('worker_list')
    return render(request, 'accounts/worker_form.html', {
        'form': form, 'title': "Yangi ishchi qo'shish"})


@login_required
def worker_edit(request, pk):
    _boss_required(request.user)
    worker = get_object_or_404(_my_workers(request.user), pk=pk)
    form = WorkerEditForm(request.POST or None, instance=worker)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Saqlandi.')
        return redirect('worker_list')
    return render(request, 'accounts/worker_form.html', {
        'form': form, 'title': f'{worker} — tahrirlash', 'worker': worker})


@login_required
def worker_password(request, pk):
    _boss_required(request.user)
    worker = get_object_or_404(_my_workers(request.user), pk=pk)
    form = SetPasswordSimpleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        worker.set_password(form.cleaned_data['password1'])
        worker.save()
        amal_yoz(request.user, Amal.PAROL_OZGARTIRDI, str(worker))
        messages.success(request, f'{worker} uchun yangi parol o\'rnatildi.')
        return redirect('worker_list')
    return render(request, 'accounts/worker_form.html', {
        'form': form, 'title': f'{worker} — parolni almashtirish', 'worker': worker})


@login_required
def worker_fire(request, pk):
    """Bo'shatish: hisob o'chirilmaydi, faolsizlantiriladi — shartnomalari saqlanadi."""
    _boss_required(request.user)
    worker = get_object_or_404(_my_workers(request.user), pk=pk)
    if request.method == 'POST':
        if request.POST.get('mode') == 'delete':
            name = str(worker)
            worker.delete()
            amal_yoz(request.user, Amal.ISHCHI_OCHIRDI, name)
            messages.success(request, f'{name} tizimdan butunlay o\'chirildi.')
        else:
            worker.is_active = False
            worker.save(update_fields=['is_active'])
            amal_yoz(request.user, Amal.ISHCHI_BOSHATDI, str(worker))
            messages.success(request, f'{worker} bo\'shatildi (kira olmaydi).')
        return redirect('worker_list')
    return render(request, 'accounts/worker_fire.html', {
        'worker': worker, 'contracts_count': worker.contracts.count()})


@login_required
def worker_detail(request, pk):
    _boss_required(request.user)
    worker = get_object_or_404(_my_workers(request.user), pk=pk)
    contracts = worker.contracts.all()
    return render(request, 'accounts/worker_detail.html', {
        'worker': worker,
        'contracts': contracts,
        'live_count': contracts.count(),
        'live_amount': contracts.aggregate(s=Sum('amount'))['s'] or 0,
    })
