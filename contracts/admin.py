from django.contrib import admin

from .models import (Amal, Contract, DeleteRequest, GuarantorInfo, JewelryItem,
                     VehicleInfo)


class JewelryInline(admin.TabularInline):
    model = JewelryItem
    extra = 0


class VehicleInline(admin.StackedInline):
    model = VehicleInfo
    extra = 0


class GuarantorInline(admin.StackedInline):
    model = GuarantorInfo
    extra = 0


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'borrower_fio', 'collateral_type',
                    'amount', 'status', 'created_by')
    list_filter = ('collateral_type', 'status', 'date')
    search_fields = ('number', 'borrower_fio')
    inlines = [JewelryInline, VehicleInline, GuarantorInline]


@admin.register(DeleteRequest)
class DeleteRequestAdmin(admin.ModelAdmin):
    list_display = ('contract_number', 'contract_info', 'requested_by',
                    'assigned_to', 'status', 'created_at', 'decided_at')
    list_filter = ('status',)


@admin.register(Amal)
class AmalAdmin(admin.ModelAdmin):
    list_display = ('vaqt', 'kim_nomi', 'kim_roli', 'amal', 'obyekt', 'izoh')
    list_filter = ('amal', 'kim_roli', 'vaqt')
    search_fields = ('kim_nomi', 'obyekt', 'izoh')
    date_hierarchy = 'vaqt'
    readonly_fields = ('vaqt', 'kim', 'kim_nomi', 'kim_roli', 'amal', 'obyekt', 'izoh')

    def has_add_permission(self, request):
        return False      # tarix qo'lda yozilmaydi
