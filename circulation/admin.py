from django.contrib import admin
from .models import IssueRecord

@admin.register(IssueRecord)
class IssueRecordAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'issue_date', 'due_date', 'return_date', 'status')
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('book__title', 'user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('issue_date',)
    ordering = ('-issue_date',)
